#!/usr/bin/env python3
"""
Terminal-Output-Modul für das Meshtastic ↔ Telegram Gateway
Hier wird alles gehandhabt, was im Terminal angezeigt wird.
Automatische Emoji-Erkennung für bessere Kompatibilität.
"""

import asyncio
import sys
from datetime import datetime
from collections import deque
from config import NODE_STATUS_INTERVAL, MAX_RECENT_NODES

def can_display_unicode():
    """
    Prüft, ob das Terminal Unicode/Emojis darstellen kann
    """
    try:
        # Versuche ein einfaches Emoji zu encodieren
        test_emoji = "🚀"
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
            test_emoji.encode(sys.stdout.encoding)
            # Zusätzlicher Test: Versuche tatsächlich zu drucken (aber nicht sichtbar)
            import io
            temp_buffer = io.StringIO()
            temp_buffer.write(test_emoji)
        else:
            # Fallback: Versuche mit der Standard-Encoding
            test_emoji.encode('utf-8')
        return True
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
    """Gibt aktuelle Uhrzeit als String zurück"""
    return datetime.now().strftime("%H:%M:%S")

def log_startup():
    """Zeigt Start-Nachricht an"""
    rocket = get_emoji("🚀", "[START]")
    arrow = get_emoji("↔", "<->")
    print(f"[{get_timestamp()}] {rocket} Starte Meshtastic {arrow} Telegram Gateway...")

def log_meshtastic_connected(host):
    """Zeigt erfolgreiche Meshtastic-Verbindung an"""
    check = get_emoji("✅", "[OK]")
    print(f"[{get_timestamp()}] {check} Mit Meshtastic-Node {host} verbunden")

def log_meshtastic_error(error):
    """Zeigt Meshtastic-Verbindungsfehler an"""
    cross = get_emoji("❌", "[ERROR]")
    print(f"[{get_timestamp()}] {cross} Fehler bei Meshtastic-Verbindung: {error}")

def log_channel_found(channel_name, index):
    """Zeigt gefundenen Kanal an"""
    radio = get_emoji("📻", "[CHANNEL]")
    print(f"[{get_timestamp()}] {radio} Kanal '{channel_name}' gefunden (Index {index})")

def log_channel_default(channel_name):
    """Zeigt Standard-Kanal-Verwendung an"""
    radio = get_emoji("📻", "[CHANNEL]")
    print(f"[{get_timestamp()}] {radio} Verwende Standard-Kanal-Index 1 für '{channel_name}'")

def log_channel_config_error():
    """Zeigt Kanalkonfigurationsfehler an"""
    warning = get_emoji("⚠️", "[WARNING]")
    print(f"[{get_timestamp()}] {warning} Kanalkonfiguration nicht lesbar, verwende Standard-Kanal-Index 1")

def log_telegram_connected(bot_name, username):
    """Zeigt erfolgreiche Telegram-Bot-Verbindung an"""
    robot = get_emoji("🤖", "[BOT]")
    print(f"[{get_timestamp()}] {robot} Telegram-Bot verbunden: {bot_name} (@{username})")

def log_telegram_polling_started():
    """Zeigt Start des Telegram-Pollings an"""
    refresh = get_emoji("🔄", "[POLLING]")
    print(f"[{get_timestamp()}] {refresh} Telegram Polling gestartet")

def log_telegram_error(error):
    """Zeigt Telegram-Bot-Fehler an"""
    cross = get_emoji("❌", "[ERROR]")
    print(f"[{get_timestamp()}] {cross} Fehler beim Telegram-Bot: {error}")

def log_message_telegram_to_meshtastic(sender, text):
    """Zeigt weitergeleitete Nachricht von Telegram zu Meshtastic an"""
    phone = get_emoji("📱", "[TG]")
    arrow_right = get_emoji("➡️", "->")
    radio = get_emoji("📡", "[MESH]")
    print(f"[{get_timestamp()}] {phone}{arrow_right}{radio} {sender}: {text}")

def log_message_meshtastic_to_telegram(sender, text):
    """Zeigt weitergeleitete Nachricht von Meshtastic zu Telegram an"""
    radio = get_emoji("📡", "[MESH]")
    arrow_right = get_emoji("➡️", "->")
    phone = get_emoji("📱", "[TG]")
    print(f"[{get_timestamp()}] {radio}{arrow_right}{phone} {sender}: {text}")

def log_meshtastic_send_error(error):
    """Zeigt Fehler beim Senden an Meshtastic an"""
    cross = get_emoji("❌", "[ERROR]")
    print(f"[{get_timestamp()}] {cross} Fehler beim Senden an Meshtastic: {error}")

def log_telegram_send_error(error):
    """Zeigt Fehler beim Senden an Telegram an"""
    cross = get_emoji("❌", "[ERROR]")
    print(f"[{get_timestamp()}] {cross} Fehler beim Senden an Telegram: {error}")

def log_meshtastic_unavailable():
    """Zeigt an, dass Meshtastic-Interface nicht verfügbar ist"""
    cross = get_emoji("❌", "[ERROR]")
    print(f"[{get_timestamp()}] {cross} Meshtastic-Interface nicht verfügbar")

def log_wrong_chat_id():
    """Zeigt an, dass Nachricht aus falscher Chat-ID ignoriert wurde"""
    warning = get_emoji("⚠️", "[WARNING]")
    print(f"[{get_timestamp()}] {warning} Nachricht aus falscher Chat-ID ignoriert")

def log_meshtastic_disconnecting():
    """Zeigt Trennung der Meshtastic-Verbindung an"""
    plug = get_emoji("🔌", "[DISCONNECT]")
    print(f"[{get_timestamp()}] {plug} Beende Verbindung zur Meshtastic-Node...")

def log_telegram_stopping():
    """Zeigt Stoppen des Telegram-Bots an"""
    stop = get_emoji("🛑", "[STOP]")
    print(f"[{get_timestamp()}] {stop} Stoppe Telegram-Bot...")

def log_gateway_stopping():
    """Zeigt Beenden des Gateways an"""
    stop = get_emoji("🛑", "[STOP]")
    print(f"\n[{get_timestamp()}] {stop} Gateway wird beendet...")

def log_private_chat_secret_registered(sender_name, node_id):
    """Zeigt registriertes Secret für private Chats an"""
    lock = get_emoji("🔐", "[SECRET]")
    print(f"[{get_timestamp()}] {lock} Secret von {sender_name} (Node {node_id}) registriert")

def log_private_chat_authenticated(telegram_user, meshtastic_user):
    """Zeigt erfolgreiche private Chat-Authentifizierung an"""
    check = get_emoji("✅", "[AUTH]")
    arrow = get_emoji("↔", "<->")
    print(f"[{get_timestamp()}] {check} Private Chat eingerichtet: @{telegram_user} {arrow} {meshtastic_user}")

def log_private_message_telegram_to_meshtastic(telegram_user, meshtastic_user):
    """Zeigt private Nachricht von Telegram zu Meshtastic an"""
    lock = get_emoji("🔒", "[PRIVATE]")
    phone = get_emoji("📱", "[TG]")
    arrow_right = get_emoji("➡️", "->")
    radio = get_emoji("📡", "[MESH]")
    print(f"[{get_timestamp()}] {lock}{phone}{arrow_right}{radio} @{telegram_user} → {meshtastic_user}")

def log_private_message_meshtastic_to_telegram(meshtastic_user, telegram_user):
    """Zeigt private Nachricht von Meshtastic zu Telegram an"""
    lock = get_emoji("🔒", "[PRIVATE]")
    radio = get_emoji("📡", "[MESH]")
    arrow_right = get_emoji("➡️", "->")
    phone = get_emoji("📱", "[TG]")
    print(f"[{get_timestamp()}] {lock}{radio}{arrow_right}{phone} {meshtastic_user} → @{telegram_user}")

def log_private_chat_info():
    """Zeigt Informationen über aktive private Chats an"""
    import private_chat
    info = private_chat.get_authenticated_users_info()
    print(f"[{get_timestamp()}] {info}")

def add_node_to_recent(node_id, sender_name):
    """Fügt eine Node zur Recent-Liste hinzu"""
    if node_id and sender_name not in [n['name'] for n in recent_nodes]:
        recent_nodes.append({
            'name': sender_name,
            'id': node_id,
            'last_seen': datetime.now()
        })

def show_node_status():
    """Zeigt die letzten aktiven Nodes an"""
    chart = get_emoji("📊", "[STATUS]")
    if recent_nodes:
        print(f"\n[{get_timestamp()}] {chart} Letzte {MAX_RECENT_NODES} aktive Nodes:")
        for i, node in enumerate(recent_nodes, 1):
            last_seen = node['last_seen'].strftime("%H:%M:%S")
            print(f"  {i:2}. {node['name']} (ID: {node['id']}) - zuletzt: {last_seen}")
        print()
    else:
        print(f"[{get_timestamp()}] {chart} Noch keine Nodes empfangen")

async def node_status_loop():
    """Zeigt alle X Minuten die letzten aktiven Nodes an"""
    while True:
        await asyncio.sleep(NODE_STATUS_INTERVAL)
        show_node_status()
