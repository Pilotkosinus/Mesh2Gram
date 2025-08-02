#!/usr/bin/env python3
"""
Terminal-Output-Modul für das Meshtastic ↔ Telegram Gateway
Jetzt mit Dashboard-Integration und File-Logging.
"""

import asyncio
import sys
from datetime import datetime
from collections import deque
from config import NODE_STATUS_INTERVAL, MAX_RECENT_NODES
import file_logger
import dashboard

def can_display_unicode():
    """
    Prüft, ob das Terminal Unicode/Emojis darstellen kann
    """
    try:
        # Einfacherer Test für bessere Kompatibilität
        test_emoji = "🚀"
        # Teste ob stdout das Emoji encodieren kann
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
            encoding = sys.stdout.encoding.lower()
            # Auf Linux/Unix ist oft UTF-8 verfügbar, auf Windows kann es problematisch sein
            if 'utf' in encoding:
                # Versuche tatsächlich zu encodieren
                test_emoji.encode(sys.stdout.encoding)
                return True
            else:
                return False
        return False
    except (UnicodeEncodeError, AttributeError, LookupError):
        return False

# Einmalige Prüfung beim Import
UNICODE_SUPPORT = can_display_unicode()

def get_emoji(emoji_char, fallback=""):
    """
    Gibt das Emoji zurück wenn unterstützt, sonst den Fallback
    """
    return emoji_char if UNICODE_SUPPORT else fallback

# Node-Tracking für Status-Updates
recent_nodes = deque(maxlen=MAX_RECENT_NODES)

def get_timestamp():
    """Gibt aktuellen Zeitstempel formatiert zurück"""
    return datetime.now().strftime("%H:%M:%S")

def log_startup():
    """Zeigt Gateway-Start an (nur für Setup-Modus)"""
    pass  # Dashboard-Modus braucht das nicht

def log_gateway_stopping():
    """Zeigt Gateway-Stop an"""
    file_logger.log_shutdown()

def log_network_available(host):
    """Zeigt verfügbares Netzwerk an"""
    file_logger.log_info(f"Gerät {host} ist wieder im Netzwerk erreichbar")

def log_waiting_for_device():
    """Zeigt Warten auf Gerät an"""
    file_logger.log_debug("Warte auf Gerät-Bereitschaft...")

def log_meshtastic_connecting(host):
    """Zeigt Meshtastic-Verbindungsversuch an"""
    file_logger.log_info(f"Verbinde mit Meshtastic-Node {host}...")

def log_meshtastic_connected(host):
    """Zeigt erfolgreiche Meshtastic-Verbindung an"""
    file_logger.log_meshtastic_connected(host)
    dashboard.update_meshtastic_connection(True, host)

def log_meshtastic_disconnected():
    """Zeigt Meshtastic-Trennung an"""
    file_logger.log_meshtastic_disconnected()
    dashboard.update_meshtastic_connection(False)

def log_channel_found(channel_name, channel_index):
    """Zeigt gefundenen Kanal an"""
    file_logger.log_info(f"Verwende Kanal '{channel_name}' (Index: {channel_index})")
    dashboard.update_channel_info(channel_name, channel_index)

def log_channel_default(channel_name, channel_index):
    """Zeigt konfigurierten Kanal an (wenn nicht automatisch erkannt)"""
    file_logger.log_warning(f"Kanal nicht automatisch erkannt, verwende Konfiguration: '{channel_name}' (Index: {channel_index})")
    dashboard.update_channel_info(channel_name, channel_index)

def log_telegram_connected(bot_name, username):
    """Zeigt erfolgreiche Telegram-Bot-Verbindung an"""
    file_logger.log_telegram_connected(bot_name, username)
    dashboard.update_telegram_connection(True, bot_name)

def log_telegram_polling_started():
    """Zeigt Start des Telegram-Pollings an"""
    file_logger.log_info("Telegram Polling gestartet")

def log_telegram_error(error):
    """Zeigt Telegram-Bot-Fehler an"""
    file_logger.log_error("Telegram", str(error))

def log_message_telegram_to_meshtastic(sender, text):
    """Zeigt weitergeleitete Nachricht von Telegram zu Meshtastic an"""
    file_logger.log_message_received("Telegram", sender, text)
    file_logger.log_message_sent("Meshtastic", text)
    dashboard.add_message_tg_to_mesh(sender, text)

def log_message_meshtastic_to_telegram(sender, text):
    """Zeigt weitergeleitete Nachricht von Meshtastic zu Telegram an"""
    file_logger.log_message_received("Meshtastic", sender, text)
    file_logger.log_message_sent("Telegram", text)
    dashboard.add_message_mesh_to_tg(sender, text)

def log_meshtastic_send_error(error):
    """Zeigt Fehler beim Senden an Meshtastic an"""
    file_logger.log_error("Meshtastic Send", str(error))

def log_telegram_send_error(error):
    """Zeigt Fehler beim Senden an Telegram an"""
    file_logger.log_error("Telegram Send", str(error))

def log_meshtastic_unavailable():
    """Zeigt an, dass Meshtastic-Interface nicht verfügbar ist"""
    file_logger.log_warning("Meshtastic-Interface nicht verfügbar")

def log_wrong_chat_id():
    """Zeigt an, dass Nachricht aus falscher Chat-ID ignoriert wurde"""
    file_logger.log_warning("Nachricht aus falscher Chat-ID ignoriert")

def log_private_message_sent(sender, recipient):
    """Zeigt gesendete private Nachricht an"""
    file_logger.log_info(f"Private Nachricht von {sender} an {recipient} weitergeleitet")
    dashboard.add_private_message()

def log_private_auth_success(user):
    """Zeigt erfolgreiche private Authentifizierung an"""
    file_logger.log_info(f"Benutzer {user} erfolgreich für private Nachrichten authentifiziert")

def log_private_auth_failed(user):
    """Zeigt fehlgeschlagene private Authentifizierung an"""
    file_logger.log_warning(f"Fehlgeschlagene Authentifizierung für private Nachrichten von {user}")

def log_bitcoin_price_request(sender, price):
    """Zeigt Bitcoin-Preis-Anfrage an"""
    file_logger.log_info(f"Bitcoin-Preis-Anfrage von {sender}: ${price}")

def log_id_request(sender, chat_id):
    """Zeigt ID-Anfrage an"""
    file_logger.log_info(f"Chat-ID-Anfrage von {sender}: {chat_id}")

def log_help_request(sender):
    """Zeigt Hilfe-Anfrage an"""
    file_logger.log_info(f"Hilfe-Anfrage von {sender}")

def log_unknown_command(sender, command):
    """Zeigt unbekannten Befehl an"""
    file_logger.log_warning(f"Unbekannter Befehl von {sender}: {command}")

def log_packet_debug(packet_info):
    """Zeigt Debug-Informationen für empfangenes Packet an"""
    file_logger.log_debug(f"Empfangenes Packet: {packet_info}")

def log_message_filtering(sender, recipient, broadcast, text):
    """Zeigt Nachrichten-Filterung an"""
    file_logger.log_debug(f"Von: {sender}, An: {recipient}, Broadcast: {broadcast}, Text: '{text}'")

def log_message_type(message_type):
    """Zeigt Nachrichten-Typ an"""
    file_logger.log_debug(message_type)

def log_node_activity(node_id, node_name):
    """Registriert Node-Aktivität"""
    file_logger.log_debug(f"Node-Aktivität: {node_name} (ID: {node_id})")
    dashboard.update_node_activity(node_id, node_name)

def add_recent_node(node_info):
    """Fügt Node zu den recent nodes hinzu (für Kompatibilität)"""
    recent_nodes.append({
        'id': node_info.get('id', 'Unknown'),
        'name': node_info.get('name', 'Unknown'),
        'last_seen': datetime.now()
    })

def log_reconnect_attempt(attempt, max_attempts):
    """Zeigt Wiederverbindungsversuch an"""
    file_logger.log_info(f"Wiederverbindungsversuch {attempt}/{max_attempts}")

def log_meshtastic_reconnecting(delay):
    """Zeigt Wiederverbindungsversuch an"""
    file_logger.log_info(f"Wiederverbindung in {delay:.0f} Sekunden...")

def log_connection_status(connected):
    """Zeigt periodischen Verbindungsstatus an (veraltet - wird durch Dashboard ersetzt)"""
    pass  # Dashboard übernimmt das

def log_network_ping_failed(host):
    """Zeigt fehlgeschlagenen Netzwerk-Ping an"""
    file_logger.log_warning(f"Netzwerk-Ping zu {host} fehlgeschlagen")

def log_device_offline(host):
    """Zeigt dass Gerät offline ist"""
    file_logger.log_warning(f"Gerät {host} ist nicht mehr im Netzwerk erreichbar")
    try:
        # Versuche Dashboard-Update mit Retry-Logik
        import dashboard
        dashboard.update_meshtastic_connection(False, host)
        file_logger.log_debug(f"Dashboard über Gerät-Offline-Status von {host} informiert")
    except Exception as e:
        file_logger.log_error(f"Fehler bei Dashboard-Update (offline): {e}")

def log_device_back_online(host):
    """Zeigt dass Gerät wieder online ist"""
    file_logger.log_info(f"Gerät {host} ist wieder im Netzwerk erreichbar")
    try:
        # Dashboard über Wiederverbindung informieren
        import dashboard
        dashboard.update_meshtastic_connection(True, host)
        file_logger.log_debug(f"Dashboard über Gerät-Online-Status von {host} informiert")
    except Exception as e:
        file_logger.log_error(f"Fehler bei Dashboard-Update (online): {e}")

def log_meshtastic_error(error):
    """Zeigt Meshtastic-Fehler an"""
    file_logger.log_error("Meshtastic", str(error))

def log_meshtastic_connection_lost():
    """Zeigt verlorene Meshtastic-Verbindung an"""
    file_logger.log_warning("Meshtastic-Verbindung verloren")
    dashboard.update_meshtastic_connection(False)

def log_channel_config_error():
    """Zeigt Kanal-Konfigurationsfehler an"""
    file_logger.log_warning("Kanalkonfiguration nicht lesbar, verwende Standard-Kanal")

def log_telegram_stopping():
    """Zeigt Telegram-Stop an"""
    file_logger.log_info("Telegram-Bot wird gestoppt")

def add_node_to_recent(node_id, node_name):
    """Fügt Node zu den recent nodes hinzu"""
    log_node_activity(node_id, node_name)

def log_private_chat_secret_registered(secret, node_name):
    """Zeigt registriertes Secret für private Chats an"""
    file_logger.log_info(f"Private Chat Secret registriert für {node_name}: {secret}")

def log_private_chat_authenticated(node_name, telegram_user):
    """Zeigt erfolgreiche private Chat-Authentifizierung an"""
    file_logger.log_info(f"Private Chat authentifiziert: {node_name} ↔ {telegram_user}")

def log_private_message_telegram_to_meshtastic(telegram_user, node_name, message):
    """Zeigt private Nachricht von Telegram zu Meshtastic an"""
    file_logger.log_info(f"Private Nachricht: {telegram_user} → {node_name}: {message}")
    dashboard.add_private_message()

def log_private_message_meshtastic_to_telegram(node_name, telegram_user, message):
    """Zeigt private Nachricht von Meshtastic zu Telegram an"""
    file_logger.log_info(f"Private Nachricht: {node_name} → {telegram_user}: {message}")
    dashboard.add_private_message()

async def node_status_loop():
    """Node-Status-Loop (vereinfacht für Dashboard-Modus)"""
    while True:
        try:
            await asyncio.sleep(NODE_STATUS_INTERVAL)
            # Dashboard zeigt bereits alle Node-Informationen an
            file_logger.log_debug(f"Node-Status-Update: {len(recent_nodes)} aktive Nodes")
        except asyncio.CancelledError:
            break
        except Exception as e:
            file_logger.log_error("node_status_loop", str(e))
