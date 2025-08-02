
#!/usr/bin/env python3
"""
Hauptprogramm für das Meshtastic ↔ Telegram Gateway
Startet alle Komponenten und koordiniert das System.
"""

import asyncio
import logging
import sys
from datetime import datetime
from config import LOG_LEVEL, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, config_exists
from terminal_output import log_startup, log_gateway_stopping, node_status_loop
from message_handler import meshtastic_loop, run_telegram_bot
import private_chat
import dashboard
import file_logger
import setup

async def run_setup_if_needed():
    """Führt Setup durch falls nötig und gibt Setup-Status zurück"""
    
    # Prüfe ob Setup benötigt wird
    if not config_exists() or not setup.is_setup_completed():
        print("🔧 Erste Ausführung erkannt - Setup wird gestartet...")
        print()
        
        result = await setup.run_setup()
        if result is None:
            print("❌ Setup fehlgeschlagen!")
            return False
            
        # Konfiguration neu laden nach Setup
        import config
        config.reload_config()
        
        print()
        print("✅ Setup-Phase 1 abgeschlossen!")
        print("🔄 Das System startet jetzt im Chat-ID-Setup-Modus...")
        print()
        return True  # Setup-Modus für Chat-ID-Ermittlung
    
    return False  # Kein Setup nötig

def check_and_setup_chat_id():
    """Prüft ob Chat-ID konfiguriert ist und startet Setup falls nötig"""
    config_data = setup.get_config()
    
    # Prüfe ob wir im Chat-ID-Setup-Modus sind
    if config_data and config_data.get('chat_id_pending', False):
        print("\n" + "="*60)
        print("� CHAT-ID SETUP - PHASE 2")
        print("="*60)
        print("✅ Bot-Konfiguration abgeschlossen!")
        print()
        print("📋 NÄCHSTE SCHRITTE:")
        print("1. Laden Sie Ihren Bot in eine Telegram-Gruppe ein")
        print("2. Senden Sie die Nachricht: !id")
        print("3. Der Bot antwortet mit Ihrer Chat-ID")
        print("4. Diese wird automatisch übernommen und das Setup ist abgeschlossen")
        print()
        print("💡 Tipp: Sie können auch in Gruppen !id verwenden um die Gruppen-ID zu bekommen")
        print("="*60)
        print("🔄 System startet im Chat-ID-Setup-Modus...")
        print()
        file_logger.log_info("System startet im Chat-ID-Setup-Modus")
        return True  # Setup-Modus
        
    # Normale Prüfung für fehlende Chat-ID (sollte nicht mehr auftreten)
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID.strip() == '':
        print("\n" + "="*60)
        print("⚠️  KONFIGURATIONSFEHLER")
        print("="*60)
        print("❌ Chat-ID fehlt in der Konfiguration!")
        print("💡 Starten Sie das Setup erneut mit: python setup.py")
        print("="*60)
        return False
        
    return False  # Normale Operation

async def cleanup_loop():
    """Cleanup-Loop für private Chat Funktionen"""
    while True:
        try:
            await asyncio.sleep(3600)  # Jede Stunde
            private_chat.cleanup_old_pending_secrets()
            file_logger.log_debug("Private Chat Cleanup durchgeführt")
        except asyncio.CancelledError:
            break
        except Exception as e:
            file_logger.log_error("cleanup_loop", str(e))

async def connection_monitor():
    """Überwacht Verbindungsstatus und zeigt Statistiken (verbesserter Monitor)"""
    from message_handler import meshtastic_interface, ping_meshtastic_host, check_meshtastic_connection
    from config import MESHTASTIC_HOST, MESHTASTIC_PING_TIMEOUT
    from terminal_output import log_device_offline, log_device_back_online
    
    last_interface_status = None
    consecutive_failures = 0
    
    while True:
        try:
            await asyncio.sleep(30)  # Häufigere Prüfung alle 30 Sekunden
            
            # Interface-Status prüfen mit der gründlicheren Methode
            interface_connected = await check_meshtastic_connection()
            
            # Zusätzliche Ping-Prüfung bei scheinbar funktionierender Verbindung
            if interface_connected:
                ping_ok = await ping_meshtastic_host(MESHTASTIC_HOST, MESHTASTIC_PING_TIMEOUT)
                if not ping_ok:
                    consecutive_failures += 1
                    file_logger.log_warning(f"Ping-Test fehlgeschlagen ({consecutive_failures}/3)")
                    
                    # Nach 3 aufeinanderfolgenden Fehlern als getrennt markieren
                    if consecutive_failures >= 3:
                        interface_connected = False
                        file_logger.log_error("Verbindung als unterbrochen erkannt nach mehreren Ping-Fehlern")
                        # Direkte Dashboard-Aktualisierung für sofortige Anzeige
                        dashboard.update_meshtastic_connection(False, MESHTASTIC_HOST)
                else:
                    consecutive_failures = 0  # Reset bei erfolgreichem Ping
            else:
                consecutive_failures = 0
            
            # Dashboard-Update bei Statusänderung
            if interface_connected != last_interface_status:
                # Verwende die spezialisierten Log-Funktionen für bessere Synchronisation
                if interface_connected:
                    log_device_back_online(MESHTASTIC_HOST)
                    dashboard.update_meshtastic_connection(True, MESHTASTIC_HOST)
                else:
                    log_device_offline(MESHTASTIC_HOST)
                    # Dashboard-Update ist bereits in log_device_offline enthalten
                
                status_msg = 'Verbunden' if interface_connected else 'Getrennt'
                file_logger.log_info(f"Meshtastic-Verbindungsstatus geändert: {status_msg}")
                last_interface_status = interface_connected
                
                # Bei Verbindungsverlust versuche Neustart der Meshtastic-Schleife
                if not interface_connected:
                    file_logger.log_info("Versuche Meshtastic-Verbindung wiederherzustellen...")
                    
        except asyncio.CancelledError:
            break
        except Exception as e:
            file_logger.log_error("connection_monitor", str(e))

async def main_async():
    """Hauptfunktion die alle Services parallel startet"""
    
    # Prüfe ob Setup benötigt wird
    setup_needed = await run_setup_if_needed()
    
    if setup_needed:
        # Im Setup-Modus nur Telegram Bot starten für Chat-ID-Ermittlung
        print("📱 Telegram Bot wird gestartet für Chat-ID Setup...")
        print("💡 Senden Sie !id in Telegram um Ihre Chat-ID zu erhalten")
        print("🔧 Meshtastic wird im Setup-Modus nicht gestartet")
        print()
        
        # Konfiguration erneut laden nach Setup
        import config
        config.reload_config()
        
        try:
            await run_telegram_bot()
        except KeyboardInterrupt:
            file_logger.log_shutdown()
        return
    
    # Dashboard mit Konfigurations-Werten initialisieren
    from config import CHANNEL_NAME, CHANNEL_INDEX
    dashboard.update_channel_info(CHANNEL_NAME, CHANNEL_INDEX)
    
    # Chat-ID Setup prüfen (sollte nur noch im Ausnahmefall auftreten)
    setup_mode = check_and_setup_chat_id()
    
    if setup_mode:
        # Im Setup-Modus nur Telegram Bot starten
        print("📱 Telegram Bot wird gestartet für Chat-ID Setup...")
        print("💡 Senden Sie !id in Telegram um Ihre Chat-ID zu erhalten")
        print("🔧 Meshtastic wird im Setup-Modus nicht gestartet")
        print()
        
        try:
            await run_telegram_bot()
        except KeyboardInterrupt:
            file_logger.log_shutdown()
    else:
        # Normale Operation - Dashboard-Modus
        file_logger.log_startup()
        
        # Dashboard starten
        dashboard_task = dashboard.start_dashboard()
        
        # Alle Tasks parallel starten
        meshtastic_task = asyncio.create_task(meshtastic_loop())
        telegram_task = asyncio.create_task(run_telegram_bot())
        status_task = asyncio.create_task(node_status_loop())
        cleanup_task = asyncio.create_task(cleanup_loop())
        monitor_task = asyncio.create_task(connection_monitor())
        
        try:
            # Warten bis einer der Tasks beendet wird
            done, pending = await asyncio.wait(
                [meshtastic_task, telegram_task, status_task, cleanup_task, monitor_task, dashboard_task],
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
            file_logger.log_shutdown()
            
            # Alle Tasks beenden
            for task in [meshtastic_task, telegram_task, status_task, cleanup_task, monitor_task, dashboard_task]:
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
