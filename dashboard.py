#!/usr/bin/env python3
"""
Dashboard-Modul für das Meshtastic ↔ Telegram Gateway
Zeigt eine Live-Übersicht des Gateway-Status im Terminal an.
"""

import asyncio
import os
import sys
import unicodedata
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging

# Unicode-Support prüfen (wie in terminal_output.py)
def can_display_unicode():
    """Prüft, ob das Terminal Unicode/Emojis darstellen kann"""
    try:
        test_emoji = "🚀"
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
            encoding = sys.stdout.encoding.lower()
            if 'utf' in encoding:
                test_emoji.encode(sys.stdout.encoding)
                return True
            else:
                return False
        return False
    except (UnicodeEncodeError, AttributeError, LookupError):
        return False

# Einmalige Prüfung beim Import
UNICODE_SUPPORT = can_display_unicode()

def get_box_chars():
    """Gibt Box-Zeichen zurück je nach Unicode-Support"""
    if UNICODE_SUPPORT:
        return {
            'top_left': '┌',
            'top_right': '┐', 
            'bottom_left': '└',
            'bottom_right': '┘',
            'horizontal': '─',
            'vertical': '│',
            'cross': '├',
            'cross_right': '┤'
        }
    else:
        return {
            'top_left': '+',
            'top_right': '+',
            'bottom_left': '+', 
            'bottom_right': '+',
            'horizontal': '-',
            'vertical': '|',
            'cross': '+',
            'cross_right': '+'
        }

def get_status_chars():
    """Gibt Status-Zeichen zurück je nach Unicode-Support"""
    if UNICODE_SUPPORT:
        return {
            'connected': '✅',
            'disconnected': '❌',
            'arrow': '↔'
        }
    else:
        return {
            'connected': '[OK]',
            'disconnected': '[X]',
            'arrow': '<->'
        }

def display_width(text):
    """Berechnet die tatsächliche Display-Breite eines Strings mit Emojis"""
    width = 0
    for char in text:
        # Emoji und Wide-Charaktere haben Breite 2, normale Zeichen Breite 1
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        elif unicodedata.category(char) == 'So':  # Symbol, other (Emojis)
            width += 2
        else:
            width += 1
    return width

def pad_to_width(text, target_width):
    """Polstert einen String auf die gewünschte Display-Breite auf"""
    current_width = display_width(text)
    if current_width >= target_width:
        # Text ist zu lang - kürzen
        result = ""
        width = 0
        for char in text:
            char_width = 2 if (unicodedata.east_asian_width(char) in ('F', 'W') or 
                             unicodedata.category(char) == 'So') else 1
            if width + char_width > target_width:
                break
            result += char
            width += char_width
        return result
    else:
        # Text ist zu kurz - auffüllen
        padding_needed = target_width - current_width
        return text + " " * padding_needed

# Dashboard-Daten (Thread-safe)
class DashboardData:
    def __init__(self):
        self.start_time = datetime.now()
        self.meshtastic_connected = False
        self.meshtastic_connect_time = None
        self.meshtastic_disconnections = 0
        self.meshtastic_last_disconnection = None
        
        self.telegram_connected = False
        self.telegram_bot_name = ""
        self.telegram_connect_time = None
        
        self.messages_tg_to_mesh = 0
        self.messages_mesh_to_tg = 0
        self.private_messages = 0
        
        self.last_message = {"time": None, "sender": "", "text": ""}
        
        self.active_nodes = deque(maxlen=10)  # Letzte 10 aktive Nodes
        self.node_last_seen = {}  # Node ID -> letzter Zeitstempel
        
        self.channel_name = ""
        self.channel_index = 1
        self.host = ""

dashboard_data = DashboardData()

def get_uptime():
    """Berechnet die Uptime als formatierter String"""
    uptime = datetime.now() - dashboard_data.start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_connection_duration(connect_time):
    """Berechnet die Verbindungsdauer"""
    if not connect_time:
        return "00:00:00"
    duration = datetime.now() - connect_time
    hours, remainder = divmod(int(duration.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_time_since(timestamp):
    """Berechnet die Zeit seit einem Ereignis"""
    if not timestamp:
        return "Nie"
    delta = datetime.now() - timestamp
    if delta.total_seconds() < 60:
        return f"Vor {int(delta.total_seconds())} Sekunden"
    elif delta.total_seconds() < 3600:
        return f"Vor {int(delta.total_seconds() / 60)} Minuten"
    else:
        return f"Vor {int(delta.total_seconds() / 3600)} Stunden"

def clear_screen():
    """Löscht den Bildschirm"""
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_dashboard():
    """Zeichnet das Dashboard"""
    try:
        clear_screen()
        
        # Definiere feste Breite für das Dashboard
        DASHBOARD_WIDTH = 118  # Innere Breite
        
        # Hole die passenden Zeichen
        box = get_box_chars()
        status = get_status_chars()
        
        # Header
        print(box['top_left'] + box['horizontal'] * DASHBOARD_WIDTH + box['top_right'])
        
        # Projekt-Name (fett)
        project_name = "Mesh2Gram"
        project_padding = (DASHBOARD_WIDTH - len(project_name)) // 2
        project_line = " " * project_padding + project_name + " " * (DASHBOARD_WIDTH - len(project_name) - project_padding)
        print(box['vertical'] + project_line + box['vertical'])
        
        # Haupttitel
        header_text = f"MESHTASTIC {status['arrow']} TELEGRAM GATEWAY DASHBOARD"
        header_padding = (DASHBOARD_WIDTH - len(header_text)) // 2
        header_line = " " * header_padding + header_text + " " * (DASHBOARD_WIDTH - len(header_text) - header_padding)
        print(box['vertical'] + header_line + box['vertical'])
        print(box['cross'] + box['horizontal'] * DASHBOARD_WIDTH + box['cross_right'])
        
        # Zeit und System-Info
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = get_uptime()
        system_line = f" Zeit: {current_time}       Uptime: {uptime}             Host: {dashboard_data.host}"
        system_line = pad_to_width(system_line, DASHBOARD_WIDTH)
        print(box['vertical'] + system_line + box['vertical'])
        print(box['cross'] + box['horizontal'] * DASHBOARD_WIDTH + box['cross_right'])
        
        # Verbindungsstatus
        mesh_status = "Verbunden" if dashboard_data.meshtastic_connected else "Getrennt"
        mesh_emoji = status['connected'] if dashboard_data.meshtastic_connected else status['disconnected']
        mesh_duration = get_connection_duration(dashboard_data.meshtastic_connect_time)
        
        # Zusätzliche Info wenn getrennt
        if not dashboard_data.meshtastic_connected and dashboard_data.host:
            mesh_status = f"Getrennt ({dashboard_data.host} nicht erreichbar)"
        
        tg_status = f"Verbunden ({dashboard_data.telegram_bot_name})" if dashboard_data.telegram_connected else "Getrennt"
        tg_emoji = status['connected'] if dashboard_data.telegram_connected else status['disconnected']
        
        mesh_line = f" Meshtastic: {mesh_emoji} {mesh_status}          Dauer: {mesh_duration}"
        mesh_line = pad_to_width(mesh_line, DASHBOARD_WIDTH)
        print(box['vertical'] + mesh_line + box['vertical'])
        
        tg_line = f" Telegram:   {tg_emoji} {tg_status}        Unterbr.: {dashboard_data.meshtastic_disconnections}"
        tg_line = pad_to_width(tg_line, DASHBOARD_WIDTH)
        print(box['vertical'] + tg_line + box['vertical'])
        
        last_disconnection = get_time_since(dashboard_data.meshtastic_last_disconnection)
        disconn_line = f" Letzte Unterbrechung: {last_disconnection}"
        disconn_line = pad_to_width(disconn_line, DASHBOARD_WIDTH)
        print(box['vertical'] + disconn_line + box['vertical'])
        print(box['cross'] + box['horizontal'] * DASHBOARD_WIDTH + box['cross_right'])
        
        # Kanal-Info
        channel_line = f" Kanal: '{dashboard_data.channel_name}' (Index: {dashboard_data.channel_index})"
        channel_line = pad_to_width(channel_line, DASHBOARD_WIDTH)
        print(box['vertical'] + channel_line + box['vertical'])
        print(box['cross'] + box['horizontal'] * DASHBOARD_WIDTH + box['cross_right'])
        
        # Nachrichten-Statistiken
        arrow_tg_mesh = "→" if UNICODE_SUPPORT else "->"
        arrow_mesh_tg = "→" if UNICODE_SUPPORT else "->"
        
        msg_tg_line = f" Nachrichten Telegram {arrow_tg_mesh} Meshtastic: {dashboard_data.messages_tg_to_mesh}"
        msg_tg_line = pad_to_width(msg_tg_line, DASHBOARD_WIDTH)
        print(box['vertical'] + msg_tg_line + box['vertical'])
        
        msg_mesh_line = f" Nachrichten Meshtastic {arrow_mesh_tg} Telegram: {dashboard_data.messages_mesh_to_tg}"
        msg_mesh_line = pad_to_width(msg_mesh_line, DASHBOARD_WIDTH)
        print(box['vertical'] + msg_mesh_line + box['vertical'])
        
        msg_priv_line = f" Private Nachrichten:                {dashboard_data.private_messages}"
        msg_priv_line = pad_to_width(msg_priv_line, DASHBOARD_WIDTH)
        print(box['vertical'] + msg_priv_line + box['vertical'])
        print(box['cross'] + box['horizontal'] * DASHBOARD_WIDTH + box['cross_right'])
        
        # Letzte Nachricht
        if dashboard_data.last_message["time"]:
            last_msg_time = dashboard_data.last_message["time"].strftime("%H:%M:%S")
            last_msg_text = dashboard_data.last_message["text"][:50]  # Kürzen falls zu lang
            last_msg_line = f" Letzte Nachricht ({last_msg_time}): {dashboard_data.last_message['sender']}: {last_msg_text}"
        else:
            last_msg_line = " Letzte Nachricht: Keine"
        last_msg_line = pad_to_width(last_msg_line, DASHBOARD_WIDTH)
        print(box['vertical'] + last_msg_line + box['vertical'])
        print(box['cross'] + box['horizontal'] * DASHBOARD_WIDTH + box['cross_right'])
        
        # Aktive Nodes
        nodes_header = " Letzte 10 aktive Nodes:"
        nodes_header = pad_to_width(nodes_header, DASHBOARD_WIDTH)
        print(box['vertical'] + nodes_header + box['vertical'])
        
        # Sortiere Nodes nach letzter Aktivität
        sorted_nodes = sorted(dashboard_data.active_nodes, key=lambda x: x['last_seen'], reverse=True)
        
        for i in range(10):
            if i < len(sorted_nodes):
                node = sorted_nodes[i]
                time_str = node['last_seen'].strftime("%H:%M:%S")
                node_line = f"   {i+1}. {node['name']} (ID: {node['id']}) - {time_str}"
            else:
                node_line = ""
            node_line = pad_to_width(node_line, DASHBOARD_WIDTH)
            print(box['vertical'] + node_line + box['vertical'])
        
        # Credits-Line unten rechts
        credits_text = "vipe coded by Pilotkosinus with Claude Sonnet 4 Agent"
        credits_padding = DASHBOARD_WIDTH - len(credits_text)
        credits_line = " " * credits_padding + credits_text
        print(box['vertical'] + credits_line + box['vertical'])
        
        print(box['bottom_left'] + box['horizontal'] * DASHBOARD_WIDTH + box['bottom_right'])
        print("\nStrg+C zum Beenden")
        
    except UnicodeEncodeError as e:
        # Fallback bei Unicode-Problemen
        print("Dashboard: Unicode-Fehler erkannt, verwende ASCII-Modus")
        print("=" * 80)
        print("MESH2GRAM - MESHTASTIC <-> TELEGRAM GATEWAY")
        print("=" * 80)
        print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Uptime: {get_uptime()}")
        print(f"Meshtastic: {'[OK]' if dashboard_data.meshtastic_connected else '[X]'}")
        print(f"Telegram: {'[OK]' if dashboard_data.telegram_connected else '[X]'}")
        print(f"Kanal: {dashboard_data.channel_name} (Index: {dashboard_data.channel_index})")
        print(f"Nachrichten TG->Mesh: {dashboard_data.messages_tg_to_mesh}")
        print(f"Nachrichten Mesh->TG: {dashboard_data.messages_mesh_to_tg}")
        print(f"Private Nachrichten: {dashboard_data.private_messages}")
        print("=" * 80)
        print("Strg+C zum Beenden")

# Event-Handler für Dashboard-Updates
def update_meshtastic_connection(connected, host=None):
    """Aktualisiert Meshtastic-Verbindungsstatus"""
    try:
        old_status = dashboard_data.meshtastic_connected
        
        if connected and not dashboard_data.meshtastic_connected:
            dashboard_data.meshtastic_connect_time = datetime.now()
            dashboard_data.meshtastic_connected = True
            logging.debug(f"Dashboard: Meshtastic als verbunden markiert")
        elif not connected and dashboard_data.meshtastic_connected:
            dashboard_data.meshtastic_disconnections += 1
            dashboard_data.meshtastic_last_disconnection = datetime.now()
            dashboard_data.meshtastic_connect_time = None
            dashboard_data.meshtastic_connected = False
            logging.debug(f"Dashboard: Meshtastic als getrennt markiert")
        
        # Host-Info aktualisieren wenn verfügbar
        if host:
            dashboard_data.host = host
            
        # Logge die Statusänderung
        if old_status != connected:
            status_change = "verbunden" if connected else "getrennt"
            logging.info(f"Dashboard-Status geändert: Meshtastic {status_change}")
            
            # Bei kritischen Statusänderungen sofortiges Dashboard-Update erzwingen
            try:
                force_dashboard_update()
            except Exception as e:
                logging.warning(f"Konnte Dashboard-Sofort-Update nicht erzwingen: {e}")
            
    except Exception as e:
        logging.error(f"Fehler in update_meshtastic_connection: {e}")
        # Fallback: Status trotzdem setzen
        dashboard_data.meshtastic_connected = connected
        if host:
            dashboard_data.host = host

def force_dashboard_update():
    """Erzwingt ein sofortiges Dashboard-Update (für kritische Statusänderungen)"""
    try:
        # Dashboard direkt einmal zeichnen für sofortige Anzeige
        draw_dashboard()
        logging.debug("Dashboard-Sofort-Update durchgeführt")
    except Exception as e:
        logging.warning(f"Dashboard-Sofort-Update fehlgeschlagen: {e}")

def update_telegram_connection(connected, bot_name=""):
    """Aktualisiert Telegram-Verbindungsstatus"""
    if connected and not dashboard_data.telegram_connected:
        dashboard_data.telegram_connect_time = datetime.now()
    elif not connected:
        dashboard_data.telegram_connect_time = None
    
    dashboard_data.telegram_connected = connected
    dashboard_data.telegram_bot_name = bot_name

def update_channel_info(name, index):
    """Aktualisiert Kanal-Informationen"""
    dashboard_data.channel_name = name
    dashboard_data.channel_index = index

def add_message_tg_to_mesh(sender, text):
    """Registriert Nachricht von Telegram zu Meshtastic"""
    dashboard_data.messages_tg_to_mesh += 1
    dashboard_data.last_message = {
        "time": datetime.now(),
        "sender": sender,
        "text": text
    }

def add_message_mesh_to_tg(sender, text):
    """Registriert Nachricht von Meshtastic zu Telegram"""
    dashboard_data.messages_mesh_to_tg += 1
    dashboard_data.last_message = {
        "time": datetime.now(),
        "sender": sender,
        "text": text
    }

def add_private_message():
    """Registriert private Nachricht"""
    dashboard_data.private_messages += 1

def update_node_activity(node_id, node_name):
    """Aktualisiert Node-Aktivität"""
    now = datetime.now()
    
    # Prüfe ob Node bereits in der Liste ist
    for i, node in enumerate(dashboard_data.active_nodes):
        if node['id'] == node_id:
            # Update existing node
            dashboard_data.active_nodes[i]['last_seen'] = now
            dashboard_data.active_nodes[i]['name'] = node_name  # Update name falls geändert
            return
    
    # Neuer Node
    new_node = {
        'id': node_id,
        'name': node_name,
        'last_seen': now
    }
    dashboard_data.active_nodes.append(new_node)

async def dashboard_loop():
    """Hauptschleife für Dashboard-Updates"""
    last_update_time = datetime.now()
    error_count = 0
    
    while True:
        try:
            # Prüfe ob zu viel Zeit seit dem letzten Update vergangen ist
            current_time = datetime.now()
            time_since_update = (current_time - last_update_time).total_seconds()
            
            # Wenn mehr als 5 Sekunden vergangen sind, logge eine Warnung
            if time_since_update > 5:
                logging.warning(f"Dashboard-Update verzögert um {time_since_update:.1f} Sekunden")
            
            draw_dashboard()
            last_update_time = current_time
            error_count = 0  # Reset error count nach erfolgreichem Update
            
            await asyncio.sleep(1)  # Update jede Sekunde
            
        except asyncio.CancelledError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            error_count += 1
            # Fehler loggen aber Dashboard weiterlaufen lassen
            logging.error(f"Fehler in dashboard_loop (#{error_count}): {e}")
            
            # Bei vielen aufeinanderfolgenden Fehlern längere Pause
            if error_count > 5:
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(2)

def start_dashboard():
    """Startet das Dashboard"""
    return asyncio.create_task(dashboard_loop())
