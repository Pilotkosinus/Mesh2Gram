#!/usr/bin/env python3
"""
Gateway-Modul für das Meshtastic ↔ Telegram Gateway
Hier wird die gesamte Nachrichtenweiterleitung gehandhabt.
"""

import asyncio
import meshtastic
import meshtastic.tcp_interface
import socket
from datetime import datetime
from pubsub import pub
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters

from config import *
from terminal_output import *
import private_chat
import file_logger

# Globale Variablen
telegram_bot = None  # Wird bei Bedarf initialisiert
meshtastic_interface = None

def get_telegram_bot():
    """Gibt den Telegram Bot zurück, initialisiert ihn bei Bedarf"""
    global telegram_bot
    if telegram_bot is None:
        # Direkt aus JSON-Datei lesen für aktuellste Konfiguration
        import setup
        config_data = setup.get_config()
        
        if config_data and config_data.get('telegram_token'):
            token = config_data['telegram_token']
        else:
            # Fallback auf config.py
            from config import TELEGRAM_TOKEN
            token = TELEGRAM_TOKEN
            
        if not token or token.strip() == '':
            raise ValueError("Telegram Token ist nicht konfiguriert!")
        telegram_bot = Bot(token=token)
    return telegram_bot

async def send_to_meshtastic_safe(text, destination_id=None):
    """Sichere Sendefunktion mit Fehlerbehandlung und Dashboard-Updates"""
    if not meshtastic_interface:
        log_meshtastic_unavailable()
        # Dashboard über Verbindungsverlust informieren
        import dashboard
        dashboard.update_meshtastic_connection(False)
        return False
        
    try:
        if destination_id:
            meshtastic_interface.sendText(text, destinationId=destination_id)
        else:
            meshtastic_interface.sendText(text, channelIndex=CHANNEL_INDEX)
        return True
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        log_meshtastic_send_error(f"Verbindungsfehler beim Senden: {e}")
        # Dashboard über Verbindungsverlust informieren
        import dashboard
        dashboard.update_meshtastic_connection(False)
        return False
    except Exception as e:
        error_msg = str(e)
        log_meshtastic_send_error(f"Unbekannter Fehler beim Senden: {error_msg}")
        
        # Bei Timeout-Fehlern Dashboard über Verbindungsverlust informieren
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            import dashboard
            dashboard.update_meshtastic_connection(False)
            file_logger.log_warning("Meshtastic-Verbindung als unterbrochen markiert aufgrund von Timeout")
        
        return False

async def check_meshtastic_connection():
    """Prüft ob die Meshtastic-Verbindung noch aktiv ist (sanfter)"""
    if not meshtastic_interface:
        return False
        
    try:
        # Erst prüfen ob das Interface noch existiert
        if hasattr(meshtastic_interface, 'socket'):
            # Für TCP Interface prüfen wir den Socket-Status weniger aggressiv
            try:
                sock = meshtastic_interface.socket
                if sock is None:
                    return False
                    
                # Einfacher Check ob Socket noch verbunden ist
                sock.settimeout(0.5)  # Längerer Timeout
                try:
                    # Sanfter Test
                    sock.getpeername()  # Wirft Exception wenn nicht verbunden
                    return True
                except (OSError, socket.error):
                    return False
                finally:
                    sock.settimeout(None)
            except (ConnectionResetError, BrokenPipeError, OSError, AttributeError):
                return False
        return True
    except Exception:
        return False

async def ping_meshtastic_host(host, timeout=3):
    """Überprüft ob der Meshtastic-Host im Netzwerk erreichbar ist UND der TCP-Port verfügbar ist"""
    try:
        # Versuche TCP-Verbindung zum Meshtastic TCP Port
        future = asyncio.open_connection(host, 4403)  # Meshtastic TCP Port
        try:
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            # Verbindung erfolgreich - sofort wieder schließen
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass  # Ignoriere Fehler beim Schließen
            return True
        except asyncio.TimeoutError:
            return False
        except (ConnectionRefusedError, OSError):
            # Port nicht verfügbar oder Gerät noch nicht bereit
            return False
        except Exception:
            return False
    except Exception:
        return False

async def wait_for_device_ready(host, max_wait_time=30):
    """Wartet bis das Gerät vollständig bereit ist"""
    from terminal_output import get_timestamp
    print(f"[{get_timestamp()}] [WAITING] Warte auf Gerät-Bereitschaft...")
    
    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
        if await ping_meshtastic_host(host, 2):
            # Zusätzliche kurze Wartezeit für vollständige Bereitschaft
            await asyncio.sleep(2)
            return True
        await asyncio.sleep(1)
    
    return False

async def handle_telegram_message(update: Update, context):
    """Handler für eingehende Telegram-Nachrichten"""
    
    if not update.message:
        return
    
    # Prüfe ob es eine private Nachricht ist
    if update.effective_chat.type == 'private':
        # Private Nachricht verarbeiten
        telegram_username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        text = update.message.text
        if text:
            await private_chat.handle_telegram_private_message(
                update.effective_chat.id, 
                telegram_username, 
                text
            )
        return
    
    # Für Gruppen: Prüfe zuerst ob es private Chat-bezogene Nachrichten sind
    telegram_username = update.effective_user.username or update.effective_user.first_name or "Unknown"
    
    # Ignoriere Bot-Nachrichten (auch in Gruppen)
    if update.effective_user.is_bot:
        return
    
    # Prüfe zuerst auf !id Befehl (funktioniert in allen Chats)
    if private_chat.handle_telegram_id_command(update, context):
        return  # ID-Command verarbeitet
    
    # Prüfe ob es ein Secret für private Chats ist (in beliebiger Gruppe)
    if (update.message.text and 
        update.message.text.strip() in private_chat.pending_secrets):
        await private_chat.handle_telegram_private_message(
            update.effective_chat.id, 
            telegram_username, 
            update.message.text
        )
        return
    
    # Prüfe ob es eine private Chat-Nachricht von einem authentifizierten Benutzer ist
    if (update.message.text and 
        await private_chat.handle_telegram_group_message(
            update.effective_chat.id, 
            telegram_username, 
            update.message.text
        )):
        return  # Private Chat-Nachricht wurde verarbeitet
    
    # Text zuerst holen (wird für Setup-Modus benötigt)
    text = update.message.text
    
    # Prüfe ob es aus der konfigurierten Haupt-Chat-ID kommt (normaler Gruppenchat)
    if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID.strip() != '':
        if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
            log_wrong_chat_id()
            return
    else:
        # Setup-Modus: Keine Chat-ID konfiguriert, nur !id Kommando erlauben
        if text and text.lower().strip() == '!id':
            # !id wird bereits von handle_telegram_id_command verarbeitet
            return
        else:
            # In Setup-Modus andere Nachrichten ignorieren
            await update.message.reply_text(
                "⚙️ System ist im Setup-Modus!\n"
                "Verwenden Sie !id um Ihre Chat-ID zu erhalten."
            )
            return
    if not text:
        return
    
    # Telegram-Username ermitteln
    user = update.effective_user
    if user.username:
        sender_name = f"@{user.username}"
    elif user.first_name:
        sender_name = user.first_name
        if user.last_name:
            sender_name += f" {user.last_name}"
    else:
        sender_name = "Telegram User"
    
    # Nachricht an Meshtastic senden
    try:
        # Nachricht mit Telegram-Username als Prefix
        message = f"{sender_name}: {text}"
        success = await send_to_meshtastic_safe(message)
        if success:
            log_message_telegram_to_meshtastic(sender_name, text)
        else:
            log_telegram_send_error("Meshtastic-Verbindung nicht verfügbar")
    except Exception as e:
        log_meshtastic_send_error(e)

async def handle_text(packet, interface, target_channel_index):
    """Schickt den empfangenen Text asynchron an den Telegram-Channel,
    mit Prefix des Absender-Namens."""
    # Debug: Packet-Info anzeigen
    log_packet_debug(packet)
    
    # Text extrahieren
    text = packet.get('decoded', {}).get('text')
    if not text:
        print(f"[DEBUG] Kein Text in Packet gefunden")
        return

    # Absender-Node-ID auslesen
    node_id = packet.get('from')
    # Default-Fallback, falls kein Name vorhanden
    sender_name = f"Node {node_id}" if node_id is not None else "Unbekannter Node"
    
    # Versuche den echten Namen der Node zu ermitteln
    if node_id is not None and hasattr(interface, 'nodesByNum'):
        node_info = interface.nodesByNum.get(node_id)
        if node_info:
            # Verschiedene Möglichkeiten für den Namen prüfen
            if 'user' in node_info and node_info['user']:
                user_info = node_info['user']
                
                # Prüfe verschiedene Attribute für den Namen
                if 'longName' in user_info and user_info['longName']:
                    sender_name = user_info['longName'].strip()
                elif 'shortName' in user_info and user_info['shortName']:
                    sender_name = user_info['shortName'].strip()
                elif 'id' in user_info and user_info['id']:
                    sender_name = user_info['id']
    
    # Alternative: Versuche auch nodes-Dictionary
    if sender_name.startswith("Node ") and hasattr(interface, 'nodes'):
        for node_num, node_data in interface.nodes.items():
            if node_num == node_id and 'user' in node_data:
                user_info = node_data['user']
                if 'longName' in user_info and user_info['longName']:
                    sender_name = user_info['longName']
                    break
                elif 'shortName' in user_info and user_info['shortName']:
                    sender_name = user_info['shortName']
                    break
                elif 'id' in user_info and user_info['id']:
                    sender_name = user_info['id']
                    break

    # Dashboard-Update: Node-Aktivität registrieren
    if node_id is not None:
        log_node_activity(node_id, sender_name)

    # Prüfe ob es eine private Nachricht ist (to-Feld zeigt spezifische Node an)
    to_id = packet.get('to')
    is_broadcast = (to_id == 4294967295)  # 4294967295 = Broadcast an alle (^all)
    
    log_message_filtering(sender_name, to_id, is_broadcast, text)
    
    if not is_broadcast:
        print(f"[DEBUG] Private Nachricht erkannt - verarbeite...")
        # Private Nachricht - prüfe zuerst auf Help-Commands
        if private_chat.handle_meshtastic_help_command(text, node_id, sender_name):
            print(f"[DEBUG] Help-Command verarbeitet")
            return  # Help-Command verarbeitet
            
        # Prüfe auf BTC-Commands
        if private_chat.handle_meshtastic_btc_command(text, node_id, sender_name):
            print(f"[DEBUG] BTC-Command verarbeitet")
            return  # BTC-Command verarbeitet
            
        # Prüfe auf Secret-Commands
        if private_chat.handle_meshtastic_secret_command(text, node_id, sender_name):
            print(f"[DEBUG] Secret-Command verarbeitet")
            return  # Secret-Command verarbeitet
        
        # Prüfe auf ungültige Befehle
        if private_chat.handle_meshtastic_invalid_command(text, node_id, sender_name):
            print(f"[DEBUG] Ungültiger Command erkannt und Hilfe gesendet")
            return  # Ungültiger Command verarbeitet
        
        # Prüfe ob es eine private Chat-Nachricht ist
        if await private_chat.handle_meshtastic_private_message(node_id, sender_name, text):
            print(f"[DEBUG] Private Chat-Nachricht weitergeleitet")
            return  # Private Nachricht weitergeleitet
        
        print(f"[DEBUG] Private Nachricht ignoriert (nicht authentifiziert)")
        # Normale private Nachricht - ignorieren
        return

    # Kanal-Filterung: Nur Nachrichten aus dem gewünschten Kanal weiterleiten
    packet_channel = packet.get('channel', packet.get('channelIndex', 0))
    
    # Prüfe ob es der richtige Kanal ist
    if packet_channel != CHANNEL_INDEX:
        print(f"[DEBUG] Falscher Kanal: {packet_channel} != {CHANNEL_INDEX}")
        return

    print(f"[DEBUG] Öffentliche Nachricht - leite an Telegram weiter")

    # Node zur Recent-Liste hinzufügen
    add_node_to_recent(node_id, sender_name)

    # Nachricht mit Prefix zusammensetzen (Name in fett)
    message = f"<b>{sender_name}</b>: {text}"

    # Senden
    try:
        if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID.strip() != '':
            bot = get_telegram_bot()
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
            log_message_meshtastic_to_telegram(sender_name, text)
        else:
            # Setup-Modus: Keine Weiterleitung an Telegram
            print(f"[SETUP] Meshtastic Nachricht ignoriert (keine Chat-ID): {sender_name}: {text}")
    except Exception as e:
        log_telegram_send_error(e)

async def reset_meshtastic_interface():
    """Führt einen kompletten Reset der Meshtastic-Verbindung durch"""
    global meshtastic_interface
    
    try:
        file_logger.log_meshtastic_reset()
        
        # Interface schließen falls vorhanden
        if meshtastic_interface:
            try:
                meshtastic_interface.close()
            except:
                pass
            meshtastic_interface = None
        
        # Event-Subscriptions aufräumen
        try:
            pub.unsubscribe(None, 'meshtastic.receive.text')
        except:
            pass
            
        # Kurze Wartezeit für vollständige Bereinigung
        await asyncio.sleep(2)
        
        file_logger.log_info("Meshtastic Interface komplett zurückgesetzt")
        
    except Exception as e:
        file_logger.log_error("reset_meshtastic_interface", str(e))

async def meshtastic_loop():
    """Hauptschleife für Meshtastic-Verbindung mit stabiler Wiederverbindung"""
    global meshtastic_interface
    reconnect_delay = MESHTASTIC_RECONNECT_DELAY
    max_reconnect_delay = MESHTASTIC_MAX_RECONNECT_DELAY
    device_was_online = False
    last_connection_attempt = 0
    min_reconnect_interval = 3  # Mindestens 3 Sekunden zwischen Verbindungsversuchen
    consecutive_failures = 0  # Zähler für aufeinanderfolgende Fehler
    consecutive_timeouts = 0  # Spezifischer Zähler für Timeout-Fehler
    max_consecutive_timeouts = 3  # Nach 3 aufeinanderfolgenden Timeouts: kompletter Reset
    
    while True:
        try:
            # Verhindere zu häufige Verbindungsversuche
            now = asyncio.get_event_loop().time()
            if now - last_connection_attempt < min_reconnect_interval:
                await asyncio.sleep(min_reconnect_interval - (now - last_connection_attempt))
            
            last_connection_attempt = asyncio.get_event_loop().time()
            
            # Prüfe erst ob das Gerät im Netzwerk erreichbar ist und der TCP-Port verfügbar ist
            if not await ping_meshtastic_host(MESHTASTIC_HOST, MESHTASTIC_PING_TIMEOUT):
                if device_was_online:
                    log_device_offline(MESHTASTIC_HOST)
                    device_was_online = False
                    consecutive_failures = 0  # Reset bei erkanntem Offline-Status
                
                # Warte und prüfe wieder
                await asyncio.sleep(MESHTASTIC_NETWORK_CHECK_INTERVAL)
                continue
            
            # Gerät ist im Netzwerk - aber warte auf vollständige Bereitschaft
            if not device_was_online:
                log_device_back_online(MESHTASTIC_HOST)
                # Warte bis Gerät vollständig bereit ist
                if not await wait_for_device_ready(MESHTASTIC_HOST, 30):
                    log_meshtastic_error("Gerät antwortet nicht rechtzeitig")
                    await asyncio.sleep(MESHTASTIC_NETWORK_CHECK_INTERVAL)
                    continue
                device_was_online = True
            
            # 1) Verbinden
            log_meshtastic_connecting(MESHTASTIC_HOST)
            try:
                # Import von meshtastic (immer am Anfang)
                import meshtastic
                import meshtastic.tcp_interface
                
                # Prüfe auf zu viele aufeinanderfolgende Timeout-Fehler
                if consecutive_timeouts >= max_consecutive_timeouts:
                    from terminal_output import get_timestamp
                    print(f"[{get_timestamp()}] [WARNING] {consecutive_timeouts} aufeinanderfolgende Timeout-Fehler erkannt!")
                    print(f"[{get_timestamp()}] [INFO] Führe vollständigen Verbindungsreset durch (wie Neustart)...")
                    file_logger.log_warning(f"Zu viele Timeout-Fehler ({consecutive_timeouts}) - vollständiger Reset")
                    
                    # Kompletten Interface-Reset durchführen
                    await reset_meshtastic_interface()
                    
                    # Längere Wartezeit vor Reset
                    await asyncio.sleep(10)
                    
                    # Alle Zähler zurücksetzen
                    consecutive_timeouts = 0
                    consecutive_failures = 0
                    device_was_online = False
                    
                    # Module-Reload für kompletten Reset
                    import importlib
                    importlib.reload(meshtastic.tcp_interface)
                    
                    file_logger.log_info("Verbindungsreset abgeschlossen - versuche erneut zu verbinden")
                
                meshtastic_interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
                log_meshtastic_connected(MESHTASTIC_HOST)
                consecutive_failures = 0  # Reset bei erfolgreicher Verbindung
                consecutive_timeouts = 0  # Reset bei erfolgreicher Verbindung
                reconnect_delay = MESHTASTIC_RECONNECT_DELAY  # Reset delay
            except Exception as e:
                consecutive_failures += 1
                error_msg = f"Verbindungsfehler: {e}"
                log_meshtastic_error(error_msg)
                
                # Prüfe ob es ein Timeout-Fehler ist
                if "Timed out waiting for connection completion" in str(e):
                    consecutive_timeouts += 1
                    file_logger.log_warning(f"Timeout-Fehler #{consecutive_timeouts} von max. {max_consecutive_timeouts}")
                else:
                    consecutive_timeouts = 0  # Reset bei anderen Fehlern
                
                # Bei wiederholten Fehlern länger warten
                if consecutive_failures >= 3:
                    from terminal_output import get_timestamp
                    print(f"[{get_timestamp()}] [WARNING] {consecutive_failures} aufeinanderfolgende Fehler - längere Wartezeit")
                    await asyncio.sleep(min(consecutive_failures * 2, 30))
                
                continue  # Neuer Versuch

            # 2) Kanalindex auslesen
            target_channel_index = CHANNEL_INDEX
            try:
                if hasattr(meshtastic_interface, 'localConfig') and hasattr(meshtastic_interface.localConfig, 'channels'):
                    for ch in meshtastic_interface.localConfig.channels:
                        if hasattr(ch, 'name') and ch.name == CHANNEL_NAME:
                            target_channel_index = ch.index
                            log_channel_found(CHANNEL_NAME, target_channel_index)
                            break
                else:
                    log_channel_default(CHANNEL_NAME, CHANNEL_INDEX)
            except Exception as e:
                log_channel_config_error()

            # 3) Event-Loop und Callback
            loop = asyncio.get_running_loop()
            
            def on_receive(packet, interface):
                loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(handle_text(packet, interface, target_channel_index))
                )
            
            pub.subscribe(on_receive, 'meshtastic.receive.text')
            
            # 4) Moderatere Verbindungsüberwachung
            last_heartbeat = asyncio.get_event_loop().time()
            heartbeat_interval = MESHTASTIC_HEARTBEAT_INTERVAL
            last_network_check = 0
            
            try:
                while True:
                    await asyncio.sleep(2)  # Moderatere Prüfung
                    
                    current_time = asyncio.get_event_loop().time()
                    
                    # Prüfe Verbindungsstatus alle X Sekunden
                    if current_time - last_heartbeat >= heartbeat_interval:
                        if not await check_meshtastic_connection():
                            log_meshtastic_connection_lost()
                            break  # Verbindung verloren, neu verbinden
                        last_heartbeat = current_time
                    
                    # Zusätzlicher Netzwerk-Ping (weniger häufig)
                    if current_time - last_network_check >= heartbeat_interval * 2:
                        if not await ping_meshtastic_host(MESHTASTIC_HOST, MESHTASTIC_PING_TIMEOUT):
                            log_device_offline(MESHTASTIC_HOST)
                            device_was_online = False
                            break  # Gerät nicht mehr im Netzwerk
                        last_network_check = current_time
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_meshtastic_error(f"Unerwarteter Fehler: {e}")
                break
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            consecutive_failures += 1
            log_meshtastic_error(f"Allgemeiner Fehler: {e}")
            
        finally:
            # Cleanup - Saubere Bereinigung der Verbindung
            try:
                pub.unsubscribe(on_receive, 'meshtastic.receive.text')
            except:
                pass
                
            if meshtastic_interface:
                try:
                    meshtastic_interface.close()
                except:
                    pass
                meshtastic_interface = None
                
            log_meshtastic_disconnected()
            
            # Bei zu vielen Timeout-Fehlern zusätzliches Cleanup
            if consecutive_timeouts >= max_consecutive_timeouts - 1:
                file_logger.log_info("Zusätzliches Cleanup nach Timeout-Fehlern")
                await asyncio.sleep(3)  # Etwas länger warten
            
        # Intelligente Wiederverbindung mit adaptiver Wartezeit
        if device_was_online or await ping_meshtastic_host(MESHTASTIC_HOST, MESHTASTIC_PING_TIMEOUT):
            # Gerät ist online, aber mit angemessener Wartezeit besonders nach Fehlern
            wait_time = max(MESHTASTIC_RECONNECT_DELAY, consecutive_failures)
            log_meshtastic_reconnecting(wait_time)
            await asyncio.sleep(wait_time)
            reconnect_delay = MESHTASTIC_RECONNECT_DELAY
        else:
            # Gerät ist offline, längere Wartezeit mit exponential backoff
            current_delay = min(reconnect_delay + consecutive_failures, max_reconnect_delay)
            log_meshtastic_reconnecting(current_delay)
            await asyncio.sleep(current_delay)
            reconnect_delay = min(reconnect_delay * 1.3, max_reconnect_delay)

async def run_telegram_bot():
    """Startet den Telegram-Bot"""
    # Token aus aktueller Konfiguration holen
    import setup
    config_data = setup.get_config()
    
    if config_data and config_data.get('telegram_token'):
        token = config_data['telegram_token']
    else:
        from config import TELEGRAM_TOKEN
        token = TELEGRAM_TOKEN
    
    # Bot-Token validieren
    if not token or token.strip() == '':
        print("❌ Telegram Token ist nicht konfiguriert!")
        return
    
    # Application erstellen
    application = Application.builder().token(token).build()
    
    # Message-Handler hinzufügen (alle Nachrichten, nicht nur Text)
    application.add_handler(MessageHandler(filters.ALL, handle_telegram_message))
    
    # Bot starten
    try:
        await application.initialize()
        await application.start()
        
        # Test: Bot-Info abrufen
        bot_info = await application.bot.get_me()
        log_telegram_connected(bot_info.first_name, bot_info.username)
        
        # Bot-Username für private Chat Nachrichten speichern
        await private_chat.get_bot_info()
        
        # Polling starten
        await application.updater.start_polling(drop_pending_updates=True)
        log_telegram_polling_started()
        
        # Warten bis gestoppt
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        log_telegram_error(e)
    except asyncio.CancelledError:
        pass
    finally:
        log_telegram_stopping()
        try:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        except:
            pass
