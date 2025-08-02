# Meshtastic ↔ Telegram Gateway 📡↔📱

Ein vollständiges Gateway-System zur bidirektionalen Nachrichtenweiterleitung zwischen Meshtastic-Netzwerk und Telegram mit umfassenden Features für Gruppen- und Privatchats.

## 📁 Projektstruktur

```
meshgateway/
├── main.py                  # Hauptprogramm - hier startest du das Gateway
├── setup.py                 # Interaktiver Setup-Assistent für erste Konfiguration
├── config.py                # Konfigurationsverwaltung (lädt gateway_config.json)
├── dashboard.py             # Live-Dashboard mit Echtzeit-Statusanzeige
├── gateway_config.json      # Automatisch generierte Konfigurationsdatei
├── message_handler.py       # Nachrichtenweiterleitung zwischen Meshtastic und Telegram
├── private_chat.py          # Private Chat Funktionalität mit Secret-Authentifizierung
├── terminal_output.py       # Terminal-Ausgaben und Logging mit Emoji-Support
├── file_logger.py           # Datei-basiertes Logging-System
├── debug_private_chats.py   # Debug-Tool für Private Chat-Verbindungen
├── private_chats.json       # Gespeicherte private Chat-Verbindungen (wird automatisch erstellt)
├── requirements.txt         # Python-Abhängigkeiten
├── logs/                    # Log-Dateien (automatisch erstellt)
├── .venv/                   # Virtuelle Python-Umgebung (optional)
└── README.md               # Diese Dokumentation
```

## 🚀 Schnellstart

### 1. Bot erstellen & konfigurieren

**Telegram-Bot erstellen:**
1. Öffne Telegram und suche nach `@BotFather`
2. Sende `/start` um den BotFather zu starten
3. Sende `/newbot` um einen neuen Bot zu erstellen
4. Wähle einen Namen für deinen Bot (z.B. "Mein Mesh Gateway")
5. Wähle einen Username für deinen Bot (muss auf "bot" enden, z.B. "MeinMeshGatewayBot")
6. **Kopiere das Bot-Token** (z.B. `123456789:ABCDEF...`)

**⚠️ WICHTIG: Privacy-Settings konfigurieren**

Damit der Bot alle Nachrichten in Gruppen empfangen kann (nicht nur Befehle), musst du die Privacy-Settings deaktivieren:

1. Sende `/setprivacy` an @BotFather
2. Wähle deinen Bot aus der Liste
3. Der BotFather zeigt den aktuellen Status:
   ```
   'Enable' - your bot will only receive messages that either start with the '/' symbol or mention the bot by username.
   'Disable' - your bot will receive all messages that people send to groups.
   Current status is: ENABLED
   ```
4. **Sende `Disable`** um alle Nachrichten zu empfangen
5. Bestätigung: `Success! The new status is: DISABLED.`

**🎯 Warum ist das wichtig?**
- **ENABLED**: Bot erhält nur `/befehle` und @mentions → **Private Chats funktionieren NICHT**
- **DISABLED**: Bot erhält alle Nachrichten → **Alles funktioniert perfekt**

### 2. Installation
```bash
# Repository klonen oder Dateien herunterladen
cd meshgateway

# Dependencies installieren
pip install -r requirements.txt
```

### 3. Automatisches Setup 🚀

Das Gateway verfügt über einen **interaktiven Setup-Assistenten**, der Sie durch die komplette Konfiguration führt.

**Ersten Start:**
```bash
python main.py
```

Das System erkennt automatisch, dass noch keine Konfiguration vorhanden ist und startet den **Setup-Wizard**:

#### 📋 Setup-Schritte (automatisch geführt):

**Schritt 1: Meshtastic Host**
- Eingabe der IP-Adresse Ihres Meshtastic-Geräts
- Automatische Verbindungstests auf Port 4403
- Validierung der Erreichbarkeit

**Schritt 2: Kanal-Konfiguration**
- Eingabe des Kanal-Namens (z.B. "LongFast", "Secondary")
- Eingabe des Kanal-Index (normalerweise 0-7)

**Schritt 3: Telegram Bot Token**
- Eingabe Ihres Bot-Tokens von @BotFather
- Automatische Token-Validierung über Telegram API
- Ermittlung des Bot-Namens

**Schritt 4: Chat-ID Setup**
- Automatischer Start des Bot-Systems
- Anzeige der nächsten Schritte für Chat-ID-Ermittlung

#### 🎯 Chat-ID automatisch ermitteln:

Nach dem Setup-Wizard:
1. **Bot zur Telegram-Gruppe hinzufügen**
2. **`!id` in der Gruppe senden**
3. **Chat-ID wird automatisch erkannt und gespeichert**
4. **Setup ist abgeschlossen - Gateway startet automatisch**

### 4. Konfigurationsdatei

Das Setup erstellt automatisch eine `gateway_config.json` mit allen Einstellungen:
```json
{
    "meshtastic_host": "192.168.1.100",
    "channel_name": "LongFast", 
    "channel_index": 0,
    "telegram_token": "1234567890:ABCdef...",
    "telegram_bot_name": "MeinBot",
    "telegram_chat_id": "-1001234567890",
    "setup_completed": true
}
```

**🔍 Kanal-Informationen finden:**
1. Öffne die **Meshtastic-App** auf deinem Handy
2. Gehe zu **Kanäle** (Channels)
3. Schaue dir die Kanal-Liste an:
   ```
   Kanal 0: Primary (LongFast)    ← Index 0, Name "Primary"
   Kanal 1: Secondary             ← Index 1, Name "Secondary"
   Kanal 2: Testing               ← Index 2, Name "Testing"
   ```
4. **Verwende Name und Index** im Setup-Wizard

### 5. Start nach Setup

Nach dem ersten Setup startet das Gateway normal:
```bash
python main.py
```

Das System lädt automatisch die gespeicherte Konfiguration und startet alle Services.

## 📋 Vollständige Feature-Liste

### 🌐 Gruppenchat-Features
| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **Bidirektionale Weiterleitung** | Nachrichten zwischen Meshtastic ↔ Telegram | ✅ |
| **Bot-Nachrichten-Filter** | Ignoriert Bot-Nachrichten in Gruppen | ✅ |
| **Chat-ID Validierung** | Nur Nachrichten aus konfigurierter Gruppe | ✅ |
| **Node-Status Updates** | Regelmäßige Liste aktiver Nodes | ✅ |
| **Setup-Modus** | Funktioniert ohne konfigurierte Chat-ID | ✅ |
| **Terminal-Erkennung** | Automatische Terminal-Kompatibilität | ✅ |


### 💰 Zusatzfeatures
| Feature | Beschreibung | Status |
|---------|--------------|--------|
| **Bitcoin-Ticker** | Aktueller Bitcoin-Preis via API | ✅ |
| **Hilfe-System** | Automatische Befehlshilfe | ✅ |
| **Fehlertoleranz** | Tippfehler-Erkennung bei Befehlen | ✅ |
| **Chat-ID Anzeige** | ID-Ermittlung für Setup | ✅ |

## � Alle verfügbaren Befehle

### 🔵 Telegram-Befehle

| Befehl | Wo verfügbar | Beschreibung | Beispiel |
|--------|-------------|--------------|----------|
| `!id` | Überall | Zeigt Chat-ID und Typ an | `!id` |
| `[SECRET]` | Privatchat | Authentifizierung mit Secret | `meinpasswort123` |

### 🟢 Meshtastic-Befehle

| Befehl | Beschreibung | Beispiel | Antwort |
|--------|--------------|----------|---------|
| `!help` | Zeigt alle verfügbaren Befehle | `!help` | Liste aller Befehle |
| `!secret [WORT]` | Privaten Chat einrichten | `!secret meinpasswort` | Bestätigung + Anleitung |
| `!secret del` | Privaten Chat löschen | `!secret del` | Lösch-Bestätigung |
| `!btc` | Aktueller Bitcoin-Preis | `!btc` | `₿ Bitcoin: $43,521.85 USD` |


## 🔒 Private Chat Setup (Detailliert)

> ⚠️ **Voraussetzung**: Bot-Privacy muss auf **DISABLED** stehen (siehe Bot-Erstellung)

### Schritt-für-Schritt Anleitung

**Schritt 1: Secret über Meshtastic senden**
```
Über Meshtastic (private Nachricht an Bot):
!secret meinpasswort123
```

Das System antwortet:
```
✅ Secret 'meinpasswort123' empfangen!
Jetzt schreibe 'meinpasswort123' an @YourBot in Telegram
```

**Schritt 2: Authentifizierung in Telegram**
```
In Telegram (privater Chat mit Bot):
meinpasswort123
```

Das System antwortet:
```
✅ Privater Chat erfolgreich eingerichtet!
Du bist jetzt mit dem Meshtastic-Benutzer 'NodeName' verbunden.
Alle Nachrichten werden ab sofort weitergeleitet.
```

**Schritt 3: Chatten**
Ab sofort werden alle Nachrichten bidirektional weitergeleitet:
- Telegram → Meshtastic: `@username: Nachricht`
- Meshtastic → Telegram: `**NodeName**: Nachricht`

### Private Chat löschen
```
Über Meshtastic:
!secret del
```

System-Antwort:
```
✅ Privater Chat wurde gelöscht!
```

### Features der Private Chats
- **Persistenz**: Chats bleiben nach Gateway-Restart bestehen
- **Sicherheit**: Jeder kann nur mit seinem eigenen Chat kommunizieren
- **Gruppen-Support**: Private Chats funktionieren auch aus Telegram-Gruppen
- **Auto-Cleanup**: Alte, unvollständige Authentifizierungen werden automatisch gelöscht

## 🖥️ Live-Dashboard & Monitoring

Das Gateway verfügt über ein **integriertes Live-Dashboard**, das eine vollständige Übersicht des Gateway-Status im Terminal anzeigt.

### � Dashboard-Features

Das Dashboard zeigt in Echtzeit:

#### **📈 Systemstatus**
- **Aktuelle Zeit & Uptime**: Zeigt die laufende Betriebszeit an
- **Host-Information**: IP-Adresse des Meshtastic-Geräts
- **Verbindungsstatus**: Live-Status beider Verbindungen (Meshtastic ↔ Telegram)

#### **� Verbindungsüberwachung**  
- **Meshtastic-Verbindung**: Status, Verbindungsdauer, automatische Wiederverbindungsversuche
- **Telegram-Bot**: Verbindungsstatus mit Bot-Namen
- **Unterbrechungszähler**: Anzahl der Verbindungsabbrüche
- **Letzte Unterbrechung**: Zeitpunkt der letzten Störung

#### **📻 Kanal-Informationen**
- **Kanal-Name**: Aktuell verwendeter Meshtastic-Kanal
- **Kanal-Index**: Entsprechender Index in der Meshtastic-App

#### **� Nachrichten-Statistiken**
- **Telegram → Meshtastic**: Anzahl weitergeleiteter Nachrichten
- **Meshtastic → Telegram**: Anzahl empfangener Nachrichten  
- **Private Nachrichten**: Anzahl der privaten Chat-Nachrichten
- **Letzte Nachricht**: Zeit, Absender und Inhalt der neuesten Nachricht

#### **👥 Node-Aktivität**
- **Letzte 10 aktive Nodes**: Liste der zuletzt aktiven Meshtastic-Teilnehmer
- **Node-IDs**: Eindeutige Identifikation der Teilnehmer
- **Zeitstempel**: Letzte Aktivität jedes Nodes

### 🎨 Adaptive Darstellung

Das Dashboard passt sich automatisch an die Terminal-Fähigkeiten an:
- **Unicode-Support**: Schöne Box-Zeichen und Emojis (✅❌↔)
- **ASCII-Fallback**: Kompatible Zeichen für ältere Terminals ([OK][X]<->)
- **Automatische Breitenanpassung**: Optimale Darstellung in verschiedenen Terminal-Größen

### 🔄 Live-Updates

- **1-Sekunden-Updates**: Das Dashboard aktualisiert sich automatisch jede Sekunde
- **Sofortige Statusänderungen**: Kritische Ereignisse (Verbindungsabbrüche) werden sofort angezeigt
- **Robuste Fehlerbehandlung**: Dashboard läuft auch bei temporären Problemen weiter

### 📱 Beispiel-Dashboard
```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                        Mesh2Gram                                                        │
│                                      MESHTASTIC ↔ TELEGRAM GATEWAY DASHBOARD                                       │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Zeit: 2025-08-02 14:32:45       Uptime: 02:15:32             Host: 192.168.1.100                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Meshtastic: ✅ Verbunden          Dauer: 02:15:28                                                                    │
│ Telegram:   ✅ Verbunden (MeinBot)        Unterbr.: 2                                                               │
│ Letzte Unterbrechung: Vor 45 Minuten                                                                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Kanal: 'LongFast' (Index: 0)                                                                                         │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Nachrichten Telegram → Meshtastic: 15                                                                                │
│ Nachrichten Meshtastic → Telegram: 23                                                                                │
│ Private Nachrichten:                8                                                                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Letzte Nachricht (14:32:12): NodeUser: Hallo aus dem Mesh!                                                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Letzte 10 aktive Nodes:                                                                                              │
│   1. Alice       (ID: 123456789) - 14:31:45                                                                         │
│   2. Bob         (ID: 987654321) - 14:30:22                                                                         │
│   3. Charlie     (ID: 456789123) - 14:28:15                                                                         │
│                                                                                                                       │
│                                                vipe coded by Pilotkosinus with Claude Sonnet 4 Agent                │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

Strg+C zum Beenden
```

## 🛠️ Erweiterte Nutzung

### Mehrere Telegram-Gruppen
Das System unterstützt primär **eine** Hauptgruppe, aber private Chats funktionieren von **überall**:
- Hauptgruppe: Bidirektionale Weiterleitung aller Nachrichten
- Andere Gruppen: Nur `!id` Befehl und private Chat-Authentifizierung

### Bitcoin-Preis Feature
```
Befehl: !btc
Quelle: CoinGecko API
Format: ₿ Bitcoin: $118,521.85 USD
Timeout: 10 Sekunden
Fehlerbehandlung: Graceful degradation
```

### Automatische Wiederverbindung
- **Meshtastic**: Automatische Neuverbindung bei Verbindungsabbruch
- **Telegram**: Robustes Polling mit Fehlerbehandlung
- **Persistenz**: Alle Daten bleiben erhalten

## 🔧 Troubleshooting

### Häufige Probleme

**1. "Meshtastic-Interface nicht verfügbar"**
- Prüfe IP-Adresse in der Konfiguration (wird beim Setup getestet)
- Stelle sicher, dass die Node erreichbar ist
- Prüfe Netzwerkverbindung

**2. "Telegram-Bot antwortet nicht"**
- Prüfe Bot-Token (wird beim Setup validiert)
- Stelle sicher, dass der Bot aktiv ist
- Prüfe Internet-Verbindung

**3. "Setup schlägt fehl"**
- Starte das Setup erneut mit `python setup.py`
- Prüfe alle Eingaben auf Tippfehler
- Bei Netzwerkproblemen: Setup mit "Trotzdem verwenden" forcieren

**4. "Chat-ID Setup funktioniert nicht"**
- Bot muss zur Telegram-Gruppe hinzugefügt werden
- Sende `!id` in der Gruppe (nicht privat)
- Warte auf automatische Erkennung

**5. "Private Chats funktionieren nicht"**
- Stelle sicher, dass Meshtastic-Nachrichten als **private** Nachrichten gesendet werden
- Prüfe, ob das Secret korrekt eingegeben wurde
- Secrets sind case-sensitive!

**6. "Bot reagiert nicht auf Nachrichten in Gruppen"**
- ⚠️ **HÄUFIGSTER FEHLER**: Privacy-Settings falsch konfiguriert
- Gehe zu @BotFather → `/setprivacy` → deinen Bot wählen → `Disable`
- Status muss sein: `DISABLED` (nicht ENABLED!)
- Ohne diese Einstellung empfängt der Bot nur `/befehle` und @mentions

**7. "Konfiguration ist verloren/beschädigt"**
- Lösche `gateway_config.json`
- Starte `python main.py` für neues Setup
- Oder direkt `python setup.py` ausführen


### Debug-Modus
Für detaillierte Debug-Informationen können Sie das Log-Level in der `gateway_config.json` anpassen oder den Setup-Prozess wiederholen.

### Manuelle Konfiguration
Falls der Setup-Assistent nicht funktioniert, können Sie die `gateway_config.json` manuell erstellen:
```json
{
    "meshtastic_host": "192.168.1.100",
    "channel_name": "IhrKanalName",
    "channel_index": 0,
    "telegram_token": "IhrBotToken",
    "telegram_bot_name": "IhrBotName",
    "telegram_chat_id": "IhreChatID",
    "setup_completed": true,
    "chat_id_pending": false
}
```

### Datenverarbeitung
- **Nachrichten**: Werden nicht dauerhaft gespeichert
- **Node-IDs**: Nur für Status-Anzeige verwendet
- **Chat-IDs**: Nur für Weiterleitung verwendet


## 🔧 Modularer Aufbau & Anpassungen

### Modularer Aufbau
```
main.py              → Orchestrierung, Setup-Integration, Async-Koordination
setup.py             → Interaktiver Setup-Assistent mit Validierung und Tests
config.py            → Dynamische Konfigurationsverwaltung (JSON-basiert)
dashboard.py         → Live-Dashboard mit Echtzeit-Statusanzeige und Monitoring
gateway_config.json  → Zentrale Konfigurationsdatei (automatisch generiert)
message_handler.py   → Gruppenchat-Logik, Meshtastic ↔ Telegram Bridge
private_chat.py      → Private Chat-System, Secret-Authentifizierung, Bitcoin-API
terminal_output.py   → Console-Logging, Emoji-Support, Node-Status-Tracking
file_logger.py       → Datei-basiertes Logging mit Rotation
debug_private_chats.py → Debug-Tool für Private Chat-Diagnose
```

### Anpassungen
- **Setup wiederholen**: `python setup.py`
- **Konfiguration bearbeiten**: `gateway_config.json` editieren
- **Reset**: `gateway_config.json` löschen und neu starten

## 📚 Dependencies

```bash
# Kern-Dependencies (requirements.txt)
meshtastic>=2.3.0           # Meshtastic-Kommunikation
python-telegram-bot>=20.0   # Telegram Bot API
pypubsub>=4.0.3             # Event-System für Meshtastic
aiohttp>=3.8.0              # HTTP-Client für APIs
```


**💡 Tipp**: Für Fragen und Support siehe die Terminal-Ausgabe - sie zeigt alle wichtigen Informationen in Echtzeit!
