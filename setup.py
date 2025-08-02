#!/usr/bin/env python3
"""
Setup-Modul für das Meshtastic ↔ Telegram Gateway
Führt den Benutzer durch den initialen Konfigurationsprozess.
"""

import json
import os
import asyncio
import logging
from datetime import datetime
import re

# Pfad zur Konfigurationsdatei
CONFIG_FILE = "gateway_config.json"

def clear_screen():
    """Löscht den Bildschirm"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Zeigt den Setup-Header"""
    clear_screen()
    print("=" * 70)
    print("🚀 MESHTASTIC ↔ TELEGRAM GATEWAY SETUP")
    print("=" * 70)
    print()

def print_step(step_num, title):
    """Zeigt einen Setup-Schritt-Header"""
    print(f"📋 SCHRITT {step_num}: {title}")
    print("-" * 50)

def validate_ip(ip):
    """Validiert eine IP-Adresse"""
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

def validate_telegram_token(token):
    """Validiert ein Telegram Bot Token"""
    pattern = r'^\d+:[A-Za-z0-9_-]+$'
    return bool(re.match(pattern, token)) and len(token) > 30

async def test_meshtastic_connection(host):
    """Testet die Verbindung zum Meshtastic-Host"""
    try:
        print(f"🔍 Teste Verbindung zu {host}...")
        
        # Teste TCP-Verbindung auf Port 4403
        future = asyncio.open_connection(host, 4403)
        reader, writer = await asyncio.wait_for(future, timeout=5)
        
        writer.close()
        try:
            await writer.wait_closed()
        except:
            pass
            
        print(f"✅ Verbindung zu {host} erfolgreich!")
        return True
        
    except asyncio.TimeoutError:
        print(f"❌ Timeout bei Verbindung zu {host}")
        return False
    except (ConnectionRefusedError, OSError):
        print(f"❌ Verbindung zu {host} fehlgeschlagen (Port 4403 nicht erreichbar)")
        return False
    except Exception as e:
        print(f"❌ Verbindungsfehler: {e}")
        return False

async def test_telegram_bot(token):
    """Testet das Telegram Bot Token"""
    try:
        print("🔍 Teste Telegram Bot Token...")
        
        # Import hier um Abhängigkeiten zu vermeiden falls telegram-bot-api nicht installiert ist
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{token}/getMe"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        bot_name = bot_info.get('username', 'Unbekannt')
                        print(f"✅ Bot Token gültig! Bot-Name: @{bot_name}")
                        return True, bot_name
                    else:
                        print(f"❌ Bot Token ungültig: {data.get('description', 'Unbekannte Antwort')}")
                        return False, None
                else:
                    print(f"❌ Bot Token ungültig (HTTP {response.status})")
                    return False, None
                    
    except ImportError:
        print("⚠️  aiohttp nicht installiert - Bot-Test übersprungen")
        return True, "Unbekannt"  # Optimistisch weitermachen
    except Exception as e:
        print(f"❌ Fehler beim Bot-Test: {e}")
        return False, None

def load_existing_config():
    """Lädt existierende Konfiguration falls vorhanden"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Fehler beim Laden der existierenden Konfiguration: {e}")
    return {}

def save_config(config):
    """Speichert die Konfiguration"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"✅ Konfiguration gespeichert in {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Konfiguration: {e}")
        return False

def config_exists():
    """Prüft ob bereits eine Konfiguration existiert"""
    return os.path.exists(CONFIG_FILE)

async def run_setup():
    """Führt den kompletten Setup-Prozess durch"""
    
    print_header()
    print("Willkommen beim Gateway-Setup!")
    print("Dieser Assistent hilft Ihnen bei der ersten Konfiguration.")
    print()
    
    # Prüfe ob bereits eine Konfiguration existiert
    if config_exists():
        existing_config = load_existing_config()
        print("⚠️  Es wurde bereits eine Konfiguration gefunden!")
        print(f"   Host: {existing_config.get('meshtastic_host', 'N/A')}")
        print(f"   Kanal: {existing_config.get('channel_name', 'N/A')}")
        print(f"   Bot: {'Konfiguriert' if existing_config.get('telegram_token') else 'Nicht konfiguriert'}")
        print()
        
        while True:
            choice = input("Möchten Sie die Konfiguration neu erstellen? (j/n): ").lower().strip()
            if choice in ['j', 'ja', 'y', 'yes']:
                break
            elif choice in ['n', 'nein', 'no']:
                print("Setup abgebrochen. Verwende existierende Konfiguration.")
                return existing_config
            else:
                print("Bitte geben Sie 'j' für Ja oder 'n' für Nein ein.")
        print()
    
    config = {}
    
    # Schritt 1: Meshtastic Host IP
    print_step(1, "MESHTASTIC HOST KONFIGURATION")
    print("Geben Sie die IP-Adresse Ihres Meshtastic-Geräts ein.")
    print("Beispiel: 192.168.1.100")
    print()
    
    while True:
        host = input("Meshtastic Host IP: ").strip()
        if not host:
            print("❌ Bitte geben Sie eine IP-Adresse ein.")
            continue
            
        if not validate_ip(host):
            print("❌ Ungültige IP-Adresse. Bitte versuchen Sie es erneut.")
            continue
            
        # Teste Verbindung
        if await test_meshtastic_connection(host):
            config['meshtastic_host'] = host
            break
        else:
            print("⚠️  Verbindung fehlgeschlagen. Trotzdem verwenden? (j/n): ", end="")
            if input().lower().strip() in ['j', 'ja', 'y', 'yes']:
                config['meshtastic_host'] = host
                break
            print("Bitte versuchen Sie eine andere IP-Adresse.")
    
    print()
    
    # Schritt 2: Kanal-Konfiguration
    print_step(2, "MESHTASTIC KANAL KONFIGURATION")
    print("Konfigurieren Sie den Meshtastic-Kanal, den Sie verwenden möchten.")
    print()
    
    # Kanal Name
    while True:
        channel_name = input("Kanal-Name (z.B. 'LongFast'): ").strip()
        if channel_name:
            config['channel_name'] = channel_name
            break
        print("❌ Bitte geben Sie einen Kanal-Namen ein.")
    
    # Kanal Index
    while True:
        try:
            channel_index = input("Kanal-Index (0-7, normalerweise 0): ").strip()
            if not channel_index:
                channel_index = "0"
            
            channel_index = int(channel_index)
            if 0 <= channel_index <= 7:
                config['channel_index'] = channel_index
                break
            else:
                print("❌ Kanal-Index muss zwischen 0 und 7 liegen.")
        except ValueError:
            print("❌ Bitte geben Sie eine gültige Zahl ein.")
    
    print()
    
    # Schritt 3: Telegram Bot Token
    print_step(3, "TELEGRAM BOT KONFIGURATION")
    print("Geben Sie Ihr Telegram Bot Token ein.")
    print("Sie erhalten dieses von @BotFather in Telegram.")
    print("Format: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ")
    print()
    
    while True:
        token = input("Telegram Bot Token: ").strip()
        if not token:
            print("❌ Bitte geben Sie ein Bot Token ein.")
            continue
            
        if not validate_telegram_token(token):
            print("❌ Ungültiges Bot Token Format. Bitte versuchen Sie es erneut.")
            continue
            
        # Teste Bot Token
        valid, bot_name = await test_telegram_bot(token)
        if valid:
            config['telegram_token'] = token
            config['telegram_bot_name'] = bot_name
            break
        else:
            print("⚠️  Bot Token ungültig. Trotzdem verwenden? (j/n): ", end="")
            if input().lower().strip() in ['j', 'ja', 'y', 'yes']:
                config['telegram_token'] = token
                config['telegram_bot_name'] = "Unbekannt"
                break
            print("Bitte versuchen Sie ein anderes Token.")
    
    print()
    
    # Schritt 4: Chat ID Setup vorbereiten
    print_step(4, "TELEGRAM CHAT-ID VORBEREITUNG")
    print("Jetzt wird der Telegram Bot gestartet, um Ihre Chat-ID zu ermitteln.")
    print()
    print("📋 NÄCHSTE SCHRITTE:")
    print("1. Laden Sie Ihren Bot in eine Telegram-Gruppe ein")
    print("2. Senden Sie die Nachricht: !id")
    print("3. Der Bot wird Ihre Chat-ID anzeigen")
    print("4. Diese wird automatisch übernommen")
    print()
    
    input("Drücken Sie ENTER um fortzufahren...")
    
    # Konfiguration zwischenspeichern
    config['setup_completed'] = False
    config['chat_id_pending'] = True
    config['setup_timestamp'] = datetime.now().isoformat()
    
    if save_config(config):
        print()
        print("✅ Grundkonfiguration gespeichert!")
        print("🚀 Das System startet jetzt im Chat-ID-Setup-Modus...")
        print()
        print("⚠️  WICHTIG: Senden Sie !id in Telegram um die Konfiguration abzuschließen!")
        return config
    else:
        print("❌ Fehler beim Speichern der Konfiguration!")
        return None

def complete_setup(chat_id):
    """Schließt das Setup mit der ermittelten Chat-ID ab"""
    try:
        config = load_existing_config()
        config['telegram_chat_id'] = str(chat_id)
        config['setup_completed'] = True
        config['chat_id_pending'] = False
        config['completion_timestamp'] = datetime.now().isoformat()
        
        if save_config(config):
            print(f"✅ Setup abgeschlossen! Chat-ID {chat_id} wurde gespeichert.")
            return True
        else:
            print("❌ Fehler beim Speichern der Chat-ID!")
            return False
    except Exception as e:
        print(f"❌ Fehler beim Abschließen des Setups: {e}")
        return False

def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    if config_exists():
        return load_existing_config()
    return None

def is_setup_completed():
    """Prüft ob das Setup vollständig abgeschlossen ist"""
    config = get_config()
    return config and config.get('setup_completed', False) and not config.get('chat_id_pending', True)

if __name__ == '__main__':
    # Für direkten Aufruf
    asyncio.run(run_setup())
