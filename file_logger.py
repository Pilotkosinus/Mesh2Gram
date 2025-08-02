#!/usr/bin/env python3
"""
Logging-Modul für das Meshtastic ↔ Telegram Gateway
Schreibt alle Debug-Meldungen in Log-Dateien.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_file_logging():
    """Konfiguriert das File-Logging"""
    # Log-Verzeichnis erstellen falls nicht vorhanden
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Log-Dateiname mit Datum
    log_filename = os.path.join(log_dir, f"gateway_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    # Rotating File Handler (max 10MB pro Datei, max 5 Dateien)
    file_handler = RotatingFileHandler(
        log_filename, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Formatter für Log-Dateien
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Logger konfigurieren
    logger = logging.getLogger('gateway')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    return logger

# Globaler Logger
file_logger = setup_file_logging()

def log_to_file(level, message):
    """Schreibt eine Nachricht in die Log-Datei"""
    if level.upper() == 'DEBUG':
        file_logger.debug(message)
    elif level.upper() == 'INFO':
        file_logger.info(message)
    elif level.upper() == 'WARNING':
        file_logger.warning(message)
    elif level.upper() == 'ERROR':
        file_logger.error(message)
    elif level.upper() == 'CRITICAL':
        file_logger.critical(message)
    else:
        file_logger.info(message)

def log_startup():
    """Loggt Gateway-Start"""
    log_to_file('INFO', '=' * 60)
    log_to_file('INFO', 'MESHTASTIC ↔ TELEGRAM GATEWAY GESTARTET')
    log_to_file('INFO', '=' * 60)

def log_shutdown():
    """Loggt Gateway-Stop"""
    log_to_file('INFO', 'Gateway wird beendet')
    log_to_file('INFO', '=' * 60)

def log_meshtastic_connected(host):
    """Loggt Meshtastic-Verbindung"""
    log_to_file('INFO', f'Mit Meshtastic-Node {host} verbunden')

def log_meshtastic_disconnected():
    """Loggt Meshtastic-Trennung"""
    log_to_file('WARNING', 'Meshtastic-Verbindung getrennt')

def log_meshtastic_reset():
    """Loggt Meshtastic-Verbindungsreset"""
    log_to_file('INFO', 'Meshtastic-Verbindung wird komplett zurückgesetzt (Reset)')

def log_telegram_connected(bot_name, username):
    """Loggt Telegram-Verbindung"""
    log_to_file('INFO', f'Telegram-Bot verbunden: {bot_name} (@{username})')

def log_message_received(source, sender, text):
    """Loggt empfangene Nachricht"""
    log_to_file('DEBUG', f'[{source}] Nachricht von {sender}: {text}')

def log_message_sent(destination, text):
    """Loggt gesendete Nachricht"""
    log_to_file('DEBUG', f'Nachricht gesendet an {destination}: {text}')

def log_error(component, error):
    """Loggt Fehler"""
    log_to_file('ERROR', f'[{component}] {error}')

def log_debug(message):
    """Loggt Debug-Nachricht"""
    log_to_file('DEBUG', message)

def log_info(message):
    """Loggt Info-Nachricht"""
    log_to_file('INFO', message)

def log_warning(message):
    """Loggt Warning-Nachricht"""
    log_to_file('WARNING', message)
