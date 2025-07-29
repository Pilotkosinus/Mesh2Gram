#!/usr/bin/env python3
"""
Konfigurationsdatei für das Meshtastic ↔ Telegram Gateway
Hier können alle Einstellungen angepasst werden.
"""

# ——— Meshtastic-Konfiguration ———
MESHTASTIC_HOST = '192.000.000.15'  # IP-Adresse des Meshtastic-Geräts
CHANNEL_NAME = 'YOUR_CHANNEL_NAME'  # Name des Kanals, der für die Kommunikation verwendet wird
CHANNEL_INDEX = 1  # Index des Kanals (0 für den ersten Kanal, 1 für den zweiten usw.)

# ——— Telegram-Konfiguration ———
TELEGRAM_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'  # Bot-Token von BotFather

# Chat-ID Setup:
# 1. Starten Sie das System (funktioniert auch ohne Chat-ID)
# 2. Senden Sie !id in Telegram an Ihren Bot
# 3. Kopieren Sie die erhaltene Chat-ID hierhin:
TELEGRAM_CHAT_ID = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'  # z.B. '-1234567890' für Gruppen oder '123456789' für private Chats

# ——— Status-Update-Konfiguration ———
NODE_STATUS_INTERVAL = 180  # Sekunden (3 Minuten)
MAX_RECENT_NODES = 10  # Anzahl der Nodes, die in der Liste gespeichert werden

# ——— Logging-Konfiguration ———
LOG_LEVEL = 'ERROR'  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
