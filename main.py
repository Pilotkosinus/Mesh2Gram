
#!/usr/bin/env python3
"""
Hauptprogramm für das Meshtastic ↔ Telegram Gateway
Startet alle Komponenten und koordiniert das System.
"""

import asyncio
import logging
import sys
from config import LOG_LEVEL, TELEGRAM_CHAT_ID
from terminal_output import log_startup, log_gateway_stopping, node_status_loop
from message_handler import meshtastic_loop, run_telegram_bot
import private_chat

def check_and_setup_chat_id():
    """Prüft ob Chat-ID konfiguriert ist und startet Setup falls nötig"""
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID.strip() == '':
        print("\n" + "="*60)
        print("🚀 TELEGRAM CHAT-ID SETUP")
        print("="*60)
        print("❌ Keine Telegram Chat-ID in der config.py gefunden!")
        print()
        print("📋 ANLEITUNG:")
        print("1. Das System startet jetzt trotzdem")
        print("2. Öffnen Sie Telegram und starten Sie einen Chat mit Ihrem Bot")
        print("3. Senden Sie in Telegram: !id")
        print("4. Der Bot antwortet mit Ihrer Chat-ID")
        print("5. Kopieren Sie diese Chat-ID in die config.py bei TELEGRAM_CHAT_ID")
        print("6. Starten Sie das System neu")
        print()
        print("💡 Tipp: Sie können auch in Gruppen !id verwenden um die Gruppen-ID zu bekommen")
        print("="*60)
        print("🔄 System startet im Setup-Modus...")
        print()
        return True  # Setup-Modus
    return False  # Normale Operation

async def cleanup_loop():
    """Cleanup-Loop für private Chat Funktionen"""
    while True:
        try:
            await asyncio.sleep(3600)  # Jede Stunde
            private_chat.cleanup_old_pending_secrets()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Fehler in cleanup_loop: {e}")

async def main_async():
    """Hauptfunktion die alle Services parallel startet"""
    # Chat-ID Setup prüfen
    setup_mode = check_and_setup_chat_id()
    
    if setup_mode:
        # Im Setup-Modus nur Telegram Bot starten
        log_startup()
        print("📱 Telegram Bot wird gestartet für Chat-ID Setup...")
        print("💡 Senden Sie !id in Telegram um Ihre Chat-ID zu erhalten")
        print("🔧 Meshtastic wird im Setup-Modus nicht gestartet")
        print()
        
        try:
            await run_telegram_bot()
        except KeyboardInterrupt:
            log_gateway_stopping()
    else:
        # Normale Operation
        log_startup()
        
        # Alle Tasks parallel starten
        meshtastic_task = asyncio.create_task(meshtastic_loop())
        telegram_task = asyncio.create_task(run_telegram_bot())
        status_task = asyncio.create_task(node_status_loop())
        cleanup_task = asyncio.create_task(cleanup_loop())
        
        try:
            # Warten bis einer der Tasks beendet wird
            done, pending = await asyncio.wait(
                [meshtastic_task, telegram_task, status_task, cleanup_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Alle verbleibenden Tasks beenden
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        except KeyboardInterrupt:
            log_gateway_stopping()
            
            # Alle Tasks beenden
            for task in [meshtastic_task, telegram_task, status_task, cleanup_task]:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

def main():
    """Hauptfunktion - Startet das Gateway"""
    # Logging konfigurieren
    log_level = getattr(logging, LOG_LEVEL.upper())
    logging.basicConfig(level=log_level, format='')
    
    # Event Loop starten
    asyncio.run(main_async())

if __name__ == '__main__':
    main()
