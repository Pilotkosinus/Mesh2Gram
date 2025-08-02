#!/usr/bin/env python3
"""
Konfigurationsdatei für das Meshtastic ↔ Telegram Gateway
Lädt Konfiguration aus JSON-Datei oder verwendet Standardwerte.
"""

import json
import os

# Pfad zur Konfigurationsdatei
CONFIG_FILE = "gateway_config.json"

# Standard-Konfiguration (Fallback-Werte)
DEFAULT_CONFIG = {
    'meshtastic_host': '192.168.1.100',
    'channel_name': 'LongFast',
    'channel_index': 0,
    'telegram_token': '',
    'telegram_chat_id': '',
    'node_status_interval': 180,
    'max_recent_nodes': 10,
    'log_level': 'ERROR',
    'meshtastic_heartbeat_interval': 10,
    'meshtastic_ping_timeout': 2,
    'meshtastic_reconnect_delay': 3,
    'meshtastic_max_reconnect_delay': 30,
    'meshtastic_network_check_interval': 5
}

def load_config():
    """Lädt Konfiguration aus JSON-Datei oder verwendet Standardwerte"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge mit Standardwerten für fehlende Schlüssel
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
        except Exception as e:
            print(f"⚠️  Fehler beim Laden der Konfiguration: {e}")
            print(f"⚠️  Verwende Standardkonfiguration")
    
    return DEFAULT_CONFIG.copy()

# Lade aktuelle Konfiguration
_config = load_config()

# ——— Meshtastic-Konfiguration ———
MESHTASTIC_HOST = _config['meshtastic_host']
CHANNEL_NAME = _config['channel_name']
CHANNEL_INDEX = _config['channel_index']

# ——— Telegram-Konfiguration ———
TELEGRAM_TOKEN = _config['telegram_token']
TELEGRAM_CHAT_ID = _config['telegram_chat_id']

# ——— Status-Update-Konfiguration ———
NODE_STATUS_INTERVAL = _config['node_status_interval']
MAX_RECENT_NODES = _config['max_recent_nodes']

# ——— Logging-Konfiguration ———
LOG_LEVEL = _config['log_level']

# ——— Verbindungsüberwachung ———
MESHTASTIC_HEARTBEAT_INTERVAL = _config['meshtastic_heartbeat_interval']
MESHTASTIC_PING_TIMEOUT = _config['meshtastic_ping_timeout']
MESHTASTIC_RECONNECT_DELAY = _config['meshtastic_reconnect_delay']
MESHTASTIC_MAX_RECONNECT_DELAY = _config['meshtastic_max_reconnect_delay']
MESHTASTIC_NETWORK_CHECK_INTERVAL = _config['meshtastic_network_check_interval']

def config_exists():
    """Prüft ob Konfigurationsdatei existiert"""
    return os.path.exists(CONFIG_FILE)

def reload_config():
    """Lädt Konfiguration neu (für dynamische Updates)"""
    global _config, MESHTASTIC_HOST, CHANNEL_NAME, CHANNEL_INDEX
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    
    _config = load_config()
    MESHTASTIC_HOST = _config['meshtastic_host']
    CHANNEL_NAME = _config['channel_name'] 
    CHANNEL_INDEX = _config['channel_index']
    TELEGRAM_TOKEN = _config['telegram_token']
    TELEGRAM_CHAT_ID = _config['telegram_chat_id']
