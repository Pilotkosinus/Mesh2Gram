#!/usr/bin/env python3
"""
Gateway-Modul für das Meshtastic ↔ Telegram Gateway
Hier wird die gesamte Nachrichtenweiterleitung gehandhabt.
"""

import asyncio
import meshtastic
import meshtastic.tcp_interface
from pubsub import pub
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters

from config import *
from terminal_output import *
import private_chat

# Globale Variablen
telegram_bot = Bot(token=TELEGRAM_TOKEN)
meshtastic_interface = None

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
    
    # Prüfe ob es aus der konfigurierten Haupt-Chat-ID kommt (normaler Gruppenchat)
    if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID.strip() != '':
        if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
            log_wrong_chat_id()
            return
    else:
        # Setup-Modus: Keine Chat-ID konfiguriert, nur !id Kommando erlauben
        if text.lower().strip() == '!id':
            await private_chat.handle_telegram_id_command(update.effective_chat.id, update)
            return
        else:
            # In Setup-Modus andere Nachrichten ignorieren
            await update.message.reply_text(
                "⚙️ System ist im Setup-Modus!\n"
                "Verwenden Sie !id um Ihre Chat-ID zu erhalten."
            )
            return
    
    text = update.message.text
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
        if meshtastic_interface:
            # Nachricht mit Telegram-Username als Prefix
            message = f"{sender_name}: {text}"
            meshtastic_interface.sendText(message, channelIndex=CHANNEL_INDEX)
            log_message_telegram_to_meshtastic(sender_name, text)
        else:
            log_meshtastic_unavailable()
    except Exception as e:
        log_meshtastic_send_error(e)

async def handle_text(packet, interface, target_channel_index):
    """Schickt den empfangenen Text asynchron an den Telegram-Channel,
    mit Prefix des Absender-Namens."""
    # Debug: Packet-Info anzeigen
    print(f"[DEBUG] Empfangenes Packet: {packet}")
    
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

    # Prüfe ob es eine private Nachricht ist (to-Feld zeigt spezifische Node an)
    to_id = packet.get('to')
    is_broadcast = (to_id == 4294967295)  # 4294967295 = Broadcast an alle (^all)
    
    print(f"[DEBUG] Von: {sender_name} (Node {node_id}), An: {to_id}, Broadcast: {is_broadcast}, Text: '{text}'")
    
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
            await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
            log_message_meshtastic_to_telegram(sender_name, text)
        else:
            # Setup-Modus: Keine Weiterleitung an Telegram
            print(f"[SETUP] Meshtastic Nachricht ignoriert (keine Chat-ID): {sender_name}: {text}")
    except Exception as e:
        log_telegram_send_error(e)

async def meshtastic_loop():
    """Hauptschleife für Meshtastic-Verbindung"""
    global meshtastic_interface
    
    # 1) Verbinden
    try:
        meshtastic_interface = meshtastic.tcp_interface.TCPInterface(hostname=MESHTASTIC_HOST)
        log_meshtastic_connected(MESHTASTIC_HOST)
    except Exception as e:
        log_meshtastic_error(e)
        return

    # 2) Kanalindex auslesen (wenn verfügbar)
    target_channel_index = CHANNEL_INDEX
    try:
        if hasattr(meshtastic_interface, 'localConfig') and hasattr(meshtastic_interface.localConfig, 'channels'):
            for ch in meshtastic_interface.localConfig.channels:
                if hasattr(ch, 'name') and ch.name == CHANNEL_NAME:
                    target_channel_index = ch.index
                    log_channel_found(CHANNEL_NAME, target_channel_index)
                    break
        else:
            log_channel_default(CHANNEL_NAME)
    except Exception as e:
        log_channel_config_error()

    # 3) Laufenden Event-Loop referenzieren
    loop = asyncio.get_running_loop()

    # 4) Callback: Paket in Async-Loop einspeisen
    def on_receive(packet, interface):
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(handle_text(packet, interface, target_channel_index))
        )

    pub.subscribe(on_receive, 'meshtastic.receive.text')

    # 5) Loop am Laufen halten
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        log_meshtastic_disconnecting()
        if meshtastic_interface:
            meshtastic_interface.close()
            meshtastic_interface = None

async def run_telegram_bot():
    """Startet den Telegram-Bot"""
    # Application erstellen
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
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
