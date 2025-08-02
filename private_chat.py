#!/usr/bin/env python3
"""
Private Chat Modul für das Meshtastic ↔ Telegram Gateway
Verwaltet private Chats zwischen Meshtastic und Telegram über Secret-Authentifizierung.
"""

import json
import os
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Optional, Tuple
from telegram import Bot
from config import TELEGRAM_TOKEN
from terminal_output import log_private_chat_secret_registered, log_private_chat_authenticated, log_private_message_telegram_to_meshtastic, log_private_message_meshtastic_to_telegram

# Globale Variablen
private_chats_file = "private_chats.json"
pending_secrets: Dict[str, dict] = {}  # Secret -> {meshtastic_node_id, timestamp}
authenticated_users: Dict[str, dict] = {}  # Secret -> {meshtastic_node_id, telegram_chat_id, meshtastic_name, telegram_name}
telegram_bot = None  # Wird bei Bedarf initialisiert
bot_username = None  # Wird dynamisch beim Start ermittelt

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

async def get_bot_info():
    """Ruft Bot-Informationen ab und speichert den Username"""
    global bot_username
    try:
        bot = get_telegram_bot()
        bot_info = await bot.get_me()
        bot_username = f"@{bot_info.username}"
        print(f"[Private Chat] Bot-Username ermittelt: {bot_username}")
        return bot_username
    except Exception as e:
        print(f"[Private Chat] Fehler beim Abrufen der Bot-Info: {e}")
        bot_username = "@IhrBot"  # Fallback
        return bot_username

def get_bot_mention():
    """Gibt Bot-Mention zurück (mit Fallback wenn noch nicht ermittelt)"""
    if bot_username:
        return bot_username
    else:
        return "an den Bot"  # Fallback wenn Username noch nicht verfügbar

def load_private_chats():
    """Lädt die gespeicherten privaten Chats aus der JSON-Datei"""
    global authenticated_users
    try:
        if os.path.exists(private_chats_file):
            with open(private_chats_file, 'r', encoding='utf-8') as f:
                authenticated_users = json.load(f)
                print(f"[Private Chat] {len(authenticated_users)} authentifizierte Benutzer geladen")
        else:
            authenticated_users = {}
            print("[Private Chat] Keine gespeicherten privaten Chats gefunden")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Laden der privaten Chats: {e}")
        authenticated_users = {}

def save_private_chats():
    """Speichert die privaten Chats in die JSON-Datei"""
    try:
        with open(private_chats_file, 'w', encoding='utf-8') as f:
            json.dump(authenticated_users, f, ensure_ascii=False, indent=2)
        print(f"[Private Chat] {len(authenticated_users)} authentifizierte Benutzer gespeichert")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Speichern der privaten Chats: {e}")

def handle_meshtastic_btc_command(text: str, node_id: int, sender_name: str) -> bool:
    """
    Verarbeitet !btc Befehle von Meshtastic
    Returns True wenn es ein BTC-Befehl war, False sonst
    """
    if text.strip().lower() != "!btc":
        return False
    
    print(f"[Private Chat] BTC-Befehl von {sender_name} (Node {node_id})")
    asyncio.create_task(send_bitcoin_price_to_meshtastic(node_id, sender_name))
    return True

def handle_telegram_id_command(update, context) -> bool:
    """
    Verarbeitet !id Befehle von Telegram (zeigt Chat-ID an)
    Returns True wenn es ein ID-Befehl war, False sonst
    """
    if not update.message or not update.message.text:
        return False
        
    if update.message.text.strip().lower() != "!id":
        return False
    
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = getattr(update.effective_chat, 'title', 'Privater Chat')
    
    # Prüfe ob wir im Setup-Modus sind
    import setup
    config_data = setup.get_config()
    
    if config_data and config_data.get('chat_id_pending', False):
        # Setup-Modus: Chat-ID automatisch übernehmen und Setup abschließen
        if setup.complete_setup(chat_id):
            if chat_type == 'private':
                response = (f"✅ Setup abgeschlossen!\n\n"
                           f"🆔 Chat-ID: `{chat_id}`\n"
                           f"💬 Typ: Privater Chat\n\n"
                           f"🔄 Das System wird neu gestartet...")
            else:
                response = (f"✅ Setup abgeschlossen!\n\n"
                           f"🆔 Chat-ID: `{chat_id}`\n"
                           f"💬 Typ: {chat_type}\n"
                           f"📝 Name: {chat_title}\n\n"
                           f"🔄 Das System wird neu gestartet...")
            
            asyncio.create_task(send_id_response_to_telegram(chat_id, response))
            print(f"[Setup] Chat-ID {chat_id} automatisch übernommen - Setup abgeschlossen!")
            
            # System nach kurzer Verzögerung neu starten
            async def restart_system():
                await asyncio.sleep(3)  # Kurz warten damit die Nachricht ankommt
                print("🔄 Setup abgeschlossen - System wird neu gestartet...")
                import os
                import sys
                os.execv(sys.executable, ['python'] + sys.argv)
            
            asyncio.create_task(restart_system())
            return True
        else:
            response = "❌ Fehler beim Abschließen des Setups!"
            asyncio.create_task(send_id_response_to_telegram(chat_id, response))
            return True
    else:
        # Normaler Modus: Nur Chat-ID anzeigen
        if chat_type == 'private':
            response = f"🆔 Chat-ID: `{chat_id}`\n💬 Typ: Privater Chat"
        else:
            response = f"🆔 Chat-ID: `{chat_id}`\n💬 Typ: {chat_type}\n📝 Name: {chat_title}\n\n📋 Für config.py verwenden:\nTELEGRAM_CHAT_ID = '{chat_id}'"
    
    asyncio.create_task(send_id_response_to_telegram(chat_id, response))
    print(f"[Private Chat] ID-Befehl in Chat {chat_id} ({chat_type}) verarbeitet")
    return True

def handle_meshtastic_help_command(text: str, node_id: int, sender_name: str) -> bool:
    """
    Verarbeitet !help Befehle von Meshtastic
    Returns True wenn es ein Help-Befehl war, False sonst
    """
    if text.strip().lower() != "!help":
        return False
    
    print(f"[Private Chat] Help-Befehl von {sender_name} (Node {node_id})")
    asyncio.create_task(send_help_commands_to_meshtastic(node_id, sender_name))
    return True

def handle_meshtastic_invalid_command(text: str, node_id: int, sender_name: str) -> bool:
    """
    Erkennt ungültige Befehle und sendet Hilfe
    Returns True wenn es ein ungültiger Befehl war, False sonst
    """
    text_lower = text.strip().lower()
    
    # Liste möglicher Tippfehler für Befehle
    invalid_commands = [
        "!seceret", "!secert", "!secrat", "!sekret", "!secret", 
        "!secrte", "!secre", "!scret", "!screet", "!sekreet",
        "!hlep", "!hepl", "!hep", "!halp", "!helop"
    ]
    
    # Prüfe auf Befehls-ähnliche Muster die mit ! beginnen
    if text.startswith("!") and len(text) > 1:
        # Extrahiere den Befehlsteil (ohne Parameter)
        command_part = text_lower.split()[0] if " " in text_lower else text_lower
        
        # Prüfe ob es ein bekannter gültiger Befehl ist
        valid_commands = ["!help", "!secret", "!btc"]
        if command_part not in valid_commands:
            # Es ist ein ungültiger Befehl
            print(f"[Private Chat] Ungültiger Befehl '{command_part}' von {sender_name} (Node {node_id})")
            asyncio.create_task(send_invalid_command_help_to_meshtastic(node_id, sender_name, command_part))
            return True
    
    return False

def handle_meshtastic_secret_command(text: str, node_id: int, sender_name: str) -> bool:
    """
    Verarbeitet !secret Befehle von Meshtastic
    Returns True wenn es ein Secret-Befehl war, False sonst
    """
    global pending_secrets, authenticated_users
    
    # Case-insensitive Prüfung
    if not text.lower().startswith("!secret "):
        return False
    
    # Secret extrahieren (originaler Text beibehalten für das Secret selbst)
    secret_part = text[8:].strip()  # "!secret " entfernen
    
    # Prüfe auf "del" Befehl (case-insensitive)
    if secret_part.lower() == "del":
        # Lösche bestehende Authentifizierung für diese Node
        deleted_secret = None
        for secret, user_data in list(authenticated_users.items()):
            if user_data['meshtastic_node_id'] == node_id:
                deleted_secret = secret
                del authenticated_users[secret]
                break
        
        if deleted_secret:
            save_private_chats()
            print(f"[Private Chat] Authentifizierung von {sender_name} (Node {node_id}) gelöscht")
            asyncio.create_task(send_deletion_confirmation_to_meshtastic(node_id, sender_name))
        else:
            print(f"[Private Chat] Keine Authentifizierung für {sender_name} (Node {node_id}) gefunden")
            asyncio.create_task(send_no_auth_found_to_meshtastic(node_id, sender_name))
        
        return True
    
    # Neues Secret setzen
    if len(secret_part) < 4:
        print(f"[Private Chat] Secret von {sender_name} zu kurz (min. 4 Zeichen)")
        asyncio.create_task(send_secret_too_short_to_meshtastic(node_id, sender_name))
        return True
    
    # Lösche zuerst bestehende Authentifizierung für diese Node
    for secret, user_data in list(authenticated_users.items()):
        if user_data['meshtastic_node_id'] == node_id:
            del authenticated_users[secret]
            save_private_chats()
            break
    
    # Secret in Pending-Liste speichern
    pending_secrets[secret_part] = {
        'meshtastic_node_id': node_id,
        'meshtastic_name': sender_name,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"[Private Chat] Secret '{secret_part}' von {sender_name} (Node {node_id}) registriert")
    print(f"[Private Chat] Benutzer kann jetzt das Secret in Telegram-DM eingeben")
    
    # Bestätigung an Meshtastic-Benutzer senden
    asyncio.create_task(send_secret_confirmation_to_meshtastic(node_id, sender_name, secret_part))
    
    return True

async def handle_telegram_private_message(telegram_chat_id: int, telegram_username: str, text: str) -> bool:
    """
    Verarbeitet private Telegram-Nachrichten
    Returns True wenn es verarbeitet wurde, False sonst
    """
    global pending_secrets, authenticated_users
    
    # Prüfen ob es ein Secret für Authentifizierung ist
    if text.strip() in pending_secrets:
        secret = text.strip()
        pending_info = pending_secrets[secret]
        
        # Authentifizierung vervollständigen
        authenticated_users[secret] = {
            'meshtastic_node_id': pending_info['meshtastic_node_id'],
            'telegram_chat_id': telegram_chat_id,
            'meshtastic_name': pending_info['meshtastic_name'],
            'telegram_name': telegram_username,
            'created': datetime.now().isoformat()
        }
        
        # Secret aus Pending entfernen
        del pending_secrets[secret]
        
        # Speichern
        save_private_chats()
        
        # Bestätigung senden
        try:
            bot = get_telegram_bot()
            await bot.send_message(
                chat_id=telegram_chat_id,
                text=f"✅ Privater Chat erfolgreich eingerichtet!\n"
                     f"Du bist jetzt mit dem Meshtastic-Benutzer '{pending_info['meshtastic_name']}' verbunden.\n"
                     f"Alle Nachrichten werden ab sofort weitergeleitet."
            )
        except Exception as e:
            print(f"[Private Chat] Fehler beim Senden der Bestätigung: {e}")
        
        print(f"[Private Chat] Authentifizierung abgeschlossen: {telegram_username} ↔ {pending_info['meshtastic_name']}")
        log_private_chat_authenticated(telegram_username, pending_info['meshtastic_name'])
        return True
    
    # Prüfen ob Benutzer bereits authentifiziert ist
    user_secret = None
    for secret, user_data in authenticated_users.items():
        if user_data['telegram_chat_id'] == telegram_chat_id:
            user_secret = secret
            break
    
    if user_secret:
        # Nachricht an Meshtastic weiterleiten
        await forward_telegram_to_meshtastic(user_secret, text, telegram_username)
        return True
    
    # Nicht authentifiziert und kein gültiges Secret
    try:
        bot = get_telegram_bot()
        await bot.send_message(
            chat_id=telegram_chat_id,
            text="🔒 Du bist nicht authentifiziert für private Chats.\n"
                 "Sende zuerst '!secret DEIN_SECRET' an den Bot über Meshtastic, "
                 "dann sende das gleiche Secret hier."
        )
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der Auth-Nachricht: {e}")
    
    return True

async def handle_telegram_group_message(telegram_chat_id: int, telegram_username: str, text: str) -> bool:
    """
    Verarbeitet Telegram-Gruppen-Nachrichten für private Chats
    Returns True wenn es verarbeitet wurde, False sonst
    """
    global authenticated_users
    
    # Prüfen ob diese Chat-ID von einem authentifizierten Benutzer verwendet wird
    user_secret = None
    authenticated_user_data = None
    for secret, user_data in authenticated_users.items():
        if user_data['telegram_chat_id'] == telegram_chat_id:
            user_secret = secret
            authenticated_user_data = user_data
            break
    
    if user_secret and authenticated_user_data:
        # Alle Nachrichten aus dieser Gruppe an Meshtastic weiterleiten
        # (nicht nur vom authentifizierten Benutzer)
        await forward_telegram_group_to_meshtastic(user_secret, text, telegram_username, authenticated_user_data)
        return True
    
    return False

async def handle_meshtastic_private_message(node_id: int, sender_name: str, text: str) -> bool:
    """
    Verarbeitet private Meshtastic-Nachrichten
    Returns True wenn es verarbeitet wurde, False sonst
    """
    # Prüfen ob Benutzer authentifiziert ist
    user_secret = None
    for secret, user_data in authenticated_users.items():
        if user_data['meshtastic_node_id'] == node_id:
            user_secret = secret
            break
    
    if user_secret:
        # Nachricht an Telegram weiterleiten
        await forward_meshtastic_to_telegram(user_secret, text, sender_name)
        return True
    
    # Benutzer ist nicht authentifiziert - sende Hilfe-Nachricht zurück
    await send_help_message_to_meshtastic(node_id, sender_name)
    return True  # Nachricht wurde verarbeitet (auch wenn nur mit Hilfe-Antwort)

async def forward_telegram_to_meshtastic(secret: str, text: str, telegram_username: str):
    """Leitet Telegram-Nachricht an Meshtastic weiter"""
    from message_handler import send_to_meshtastic_safe
    import file_logger
    
    user_data = authenticated_users[secret]
    target_node_id = user_data['meshtastic_node_id']
    
    try:
        # Private Nachricht an spezifische Node senden
        message = f"@{telegram_username}: {text}"
        success = await send_to_meshtastic_safe(message, target_node_id)
        if success:
            print(f"[Private Chat] Telegram → Meshtastic: @{telegram_username} → {user_data['meshtastic_name']}")
            log_private_message_telegram_to_meshtastic(telegram_username, user_data['meshtastic_name'], text)
        else:
            error_msg = f"[Private Chat] Fehler beim Senden an Meshtastic: Verbindung nicht verfügbar"
            print(error_msg)
            file_logger.log_error(error_msg)
    except Exception as e:
        error_msg = f"[Private Chat] Fehler beim Senden an Meshtastic: {e}"
        print(error_msg)
        file_logger.log_error(error_msg)

async def forward_telegram_group_to_meshtastic(secret: str, text: str, sender_username: str, authenticated_user_data: dict):
    """Leitet Telegram-Gruppen-Nachricht an Meshtastic weiter"""
    from message_handler import send_to_meshtastic_safe
    import file_logger
    
    target_node_id = authenticated_user_data['meshtastic_node_id']
    
    try:
        # Gruppen-Nachricht an spezifische Node senden mit Sender-Info
        message = f"[TG] @{sender_username}: {text}"
        success = await send_to_meshtastic_safe(message, target_node_id)
        if success:
            print(f"[Private Chat] Telegram-Gruppe → Meshtastic: @{sender_username} → {authenticated_user_data['meshtastic_name']}")
            log_private_message_telegram_to_meshtastic(f"{sender_username} (Gruppe)", authenticated_user_data['meshtastic_name'], text)
        else:
            error_msg = f"[Private Chat] Fehler beim Senden der Gruppen-Nachricht an Meshtastic: Verbindung nicht verfügbar"
            print(error_msg)
            file_logger.log_error(error_msg)
    except Exception as e:
        error_msg = f"[Private Chat] Fehler beim Senden der Gruppen-Nachricht an Meshtastic: {e}"
        print(error_msg)
        file_logger.log_error(error_msg)

async def forward_meshtastic_to_telegram(secret: str, text: str, sender_name: str):
    """Leitet Meshtastic-Nachricht an Telegram weiter"""
    import file_logger
    
    user_data = authenticated_users[secret]
    telegram_chat_id = user_data['telegram_chat_id']
    
    try:
        message = f"<b>{sender_name}</b>: {text}"
        bot = get_telegram_bot()
        await bot.send_message(
            chat_id=telegram_chat_id,
            text=message,
            parse_mode='HTML'
        )
        print(f"[Private Chat] Meshtastic → Telegram: {sender_name} → @{user_data['telegram_name']}")
        log_private_message_meshtastic_to_telegram(sender_name, user_data['telegram_name'], text)
    except Exception as e:
        error_msg = f"[Private Chat] Fehler beim Senden an Telegram: {e}"
        print(error_msg)
        file_logger.log_error(error_msg)

async def send_help_message_to_meshtastic(node_id: int, sender_name: str):
    """Sendet eine Hilfe-Nachricht an einen nicht-authentifizierten Meshtastic-Benutzer"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        help_message = ("🔒 Private Chats verfügbar!\n"
                       "1. Sende: !secret DEINWORT\n"
                       f"2. Schreibe das gleiche Wort an {get_bot_mention()} in Telegram")
        
        success = await send_to_meshtastic_safe(help_message, node_id)
        if success:
            print(f"[Private Chat] Hilfe-Nachricht an {sender_name} (Node {node_id}) gesendet")
        else:
            print(f"[Private Chat] Fehler beim Senden der Hilfe-Nachricht: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der Hilfe-Nachricht: {e}")

async def send_help_commands_to_meshtastic(node_id: int, sender_name: str):
    """Sendet die verfügbaren Befehle an den Benutzer"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        help_message = ("📋 Verfügbare Befehle:\n"
                       "!secret WORT - Privaten Chat einrichten\n"
                       "!secret del - Privaten Chat löschen\n"
                       "!btc - Bitcoin-Preis anzeigen\n"
                       "!help - Diese Hilfe anzeigen\n"
                       "!id - Chat-ID anzeigen (nur Telegram)")
        
        success = await send_to_meshtastic_safe(help_message, node_id)
        if success:
            print(f"[Private Chat] Befehls-Hilfe an {sender_name} (Node {node_id}) gesendet")
        else:
            print(f"[Private Chat] Fehler beim Senden der Befehls-Hilfe: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der Befehls-Hilfe: {e}")

async def send_deletion_confirmation_to_meshtastic(node_id: int, sender_name: str):
    """Bestätigt die Löschung der Authentifizierung"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        message = "✅ Privater Chat wurde gelöscht!"
        success = await send_to_meshtastic_safe(message, node_id)
        if success:
            print(f"[Private Chat] Löschbestätigung an {sender_name} (Node {node_id}) gesendet")
        else:
            print(f"[Private Chat] Fehler beim Senden der Löschbestätigung: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der Löschbestätigung: {e}")

async def send_no_auth_found_to_meshtastic(node_id: int, sender_name: str):
    """Informiert dass keine Authentifizierung gefunden wurde"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        message = "ℹ️ Kein privater Chat aktiv"
        success = await send_to_meshtastic_safe(message, node_id)
        if success:
            print(f"[Private Chat] 'Keine Auth'-Nachricht an {sender_name} (Node {node_id}) gesendet")
        else:
            print(f"[Private Chat] Fehler beim Senden der 'Keine Auth'-Nachricht: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der 'Keine Auth'-Nachricht: {e}")

async def send_secret_too_short_to_meshtastic(node_id: int, sender_name: str):
    """Informiert dass das Secret zu kurz ist"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        message = "❌ Secret zu kurz! Min. 4 Zeichen"
        success = await send_to_meshtastic_safe(message, node_id)
        if success:
            print(f"[Private Chat] 'Secret zu kurz'-Nachricht an {sender_name} (Node {node_id}) gesendet")
        else:
            print(f"[Private Chat] Fehler beim Senden der 'Secret zu kurz'-Nachricht: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der 'Secret zu kurz'-Nachricht: {e}")

async def send_invalid_command_help_to_meshtastic(node_id: int, sender_name: str, invalid_command: str):
    """Informiert über ungültigen Befehl und zeigt Hilfe"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        message = (f"❌ Ungültiger Befehl: {invalid_command}\n"
                   f"Verfügbare Befehle:\n"
                   f"!help - Hilfe anzeigen\n"
                   f"!secret WORT - Chat einrichten\n"
                   f"!btc - Bitcoin-Preis\n"
                   f"!id - Chat-ID (nur Telegram)")
        
        success = await send_to_meshtastic_safe(message, node_id)
        if success:
            print(f"[Private Chat] 'Ungültiger Befehl'-Hilfe an {sender_name} (Node {node_id}) gesendet")
        else:
            print(f"[Private Chat] Fehler beim Senden der 'Ungültiger Befehl'-Hilfe: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der 'Ungültiger Befehl'-Hilfe: {e}")

async def send_secret_confirmation_to_meshtastic(node_id: int, sender_name: str, secret: str):
    """Bestätigt den Empfang des Secrets und gibt Anweisungen"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        message = (f"✅ Secret '{secret}' empfangen!\n"
                   f"Jetzt schreibe '{secret}' an {get_bot_mention()} in Telegram")
        
        success = await send_to_meshtastic_safe(message, node_id)
        if success:
            print(f"[Private Chat] Secret-Bestätigung an {sender_name} (Node {node_id}) gesendet")
        else:
            print(f"[Private Chat] Fehler beim Senden der Secret-Bestätigung: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der Secret-Bestätigung: {e}")

async def get_bitcoin_price() -> str:
    """Holt den aktuellen Bitcoin-Preis von der CoinGecko API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    price = data['bitcoin']['usd']
                    return f"₿ Bitcoin: ${price:,.2f} USD"
                else:
                    return "❌ Fehler beim Abrufen des Bitcoin-Preises"
    except Exception as e:
        print(f"[Private Chat] Fehler beim Bitcoin-Preis abrufen: {e}")
        return "❌ Bitcoin-Preis derzeit nicht verfügbar"

async def send_bitcoin_price_to_meshtastic(node_id: int, sender_name: str):
    """Sendet den aktuellen Bitcoin-Preis an den Meshtastic-Benutzer"""
    from message_handler import send_to_meshtastic_safe
    
    try:
        price_message = await get_bitcoin_price()
        success = await send_to_meshtastic_safe(price_message, node_id)
        if success:
            print(f"[Private Chat] Bitcoin-Preis an {sender_name} (Node {node_id}) gesendet: {price_message}")
        else:
            print(f"[Private Chat] Fehler beim Senden des Bitcoin-Preises: Verbindung nicht verfügbar")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden des Bitcoin-Preises: {e}")

async def send_id_response_to_telegram(chat_id: int, message: str):
    """Sendet die Chat-ID-Information an Telegram"""
    try:
        bot = get_telegram_bot()
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        print(f"[Private Chat] Chat-ID-Info an Chat {chat_id} gesendet")
    except Exception as e:
        print(f"[Private Chat] Fehler beim Senden der Chat-ID-Info: {e}")

def get_authenticated_users_info() -> str:
    """Gibt Informationen über authentifizierte Benutzer zurück"""
    if not authenticated_users:
        return "Keine authentifizierten privaten Chats"
    
    info = f"🔐 Private Chats ({len(authenticated_users)}):\n"
    for secret, user_data in authenticated_users.items():
        info += f"• {user_data['meshtastic_name']} ↔ @{user_data['telegram_name']}\n"
    
    return info

def cleanup_old_pending_secrets():
    """Entfernt alte pending secrets (älter als 1 Stunde)"""
    global pending_secrets
    current_time = datetime.now()
    old_secrets = []
    
    for secret, data in pending_secrets.items():
        secret_time = datetime.fromisoformat(data['timestamp'])
        if (current_time - secret_time).total_seconds() > 3600:  # 1 Stunde
            old_secrets.append(secret)
    
    for secret in old_secrets:
        del pending_secrets[secret]
        print(f"[Private Chat] Altes pending secret '{secret}' entfernt")

# Beim Import laden
load_private_chats()
