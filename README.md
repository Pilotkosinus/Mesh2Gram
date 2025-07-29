# Meshtastic ↔ Telegram Gateway 📡↔📱

Ein vollständiges Gateway-System zur bidirektionalen Nachrichtenweiterleitung zwischen Meshtastic-Netzwerk und Telegram mit Features für Gruppen- und Privatchats.

## 📁 Projektstruktur

```
meshgateway/
├── main.py              # Hauptprogramm - hier startest du das Gateway
├── config.py            # Alle Konfigurationseinstellungen
├── message_handler.py   # Nachrichtenweiterleitung zwischen Meshtastic und Telegram
├── private_chat.py      # Private Chat Funktionalität mit Secret-Authentifizierung
├── terminal_output.py   # Terminal-Ausgaben und Logging mit Emoji-Support
├── private_chats.json   # Gespeicherte private Chat-Verbindungen (wird automatisch erstellt)
├── requirements.txt     # Python-Abhängigkeiten
└── README.md           # Diese Dokumentation
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

### 3. Konfiguration
Bearbeite `config.py` und trage deine Daten ein:
```python
MESHTASTIC_HOST = '192.168.178.32'    # IP deiner Meshtastic-Node
TELEGRAM_TOKEN = 'DEIN_BOT_TOKEN'     # Token von @BotFather (Schritt 1)
TELEGRAM_CHAT_ID = ''                 # Wird automatisch ermittelt

# Meshtastic-Kanal konfigurieren (wichtig!)
CHANNEL_NAME = 'Meinmesh'            # Name des Kanals in der Meshtastic-App
CHANNEL_INDEX = 1                     # Index des Kanals (meist 1, siehe App)
```

**🔍 Kanal-Informationen finden:**
1. Öffne die **Meshtastic-App** auf deinem Handy
2. Gehe zu **Kanäle** (Channels)
3. Schaue dir die Kanal-Liste an:
   ```
   Kanal 0: Primary (LongFast)    ← Index 0, Name "Primary"
   Kanal 1: Meinmash             ← Index 1, Name "Meinmash"
   Kanal 2: Testing               ← Index 2, Name "Testing"
   ```
4. **Kopiere Name und Index** des gewünschten Kanals in die `config.py`

### 4. Start

Das System startet automatisch im **Setup-Modus** wenn keine Chat-ID konfiguriert ist.


### 📱 Chat-ID automatisch ermitteln

**Setup-Modus (empfohlen):**
1. Starte das System ohne Chat-ID: `python main.py`
2. Das System zeigt Setup-Hinweise an
3. Sende `!id` an deinen Bot in Telegram
4. Kopiere die erhaltene Chat-ID in `config.py`
5. Starte neu

**Manuell:**
- In Gruppen: Füge den Bot hinzu und sende `!id`
- In Privatachats: Starte Chat mit Bot und sende `!id`

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

## 🖥️ Terminal-Ausgabe & Monitoring

### Emoji-Support
Das System erkennt automatisch, ob dein Terminal Emojis darstellen kann:
- **Mit Emojis**: `🚀 📱➡️📡 ✅ 🔒`
- **Ohne Emojis**: `[START] [TG]->[MESH] [OK] [PRIVATE]`

### Live-Monitoring
```
[14:32:15] 🚀 Starte Meshtastic ↔ Telegram Gateway...
[14:32:16] ✅ Mit Meshtastic-Node 192.168.178.22 verbunden
[14:32:17] 📻 Kanal 'Kanalname' gefunden (Index 1)
[14:32:18] 🤖 Telegram-Bot verbunden:  (@yourbotusername)
[14:32:19] 🔄 Telegram Polling gestartet
[14:32:45] 📱➡️📡 @andreas: Hallo vom Telegram!
[14:33:12] 📡➡️📱 NodeUser: Antwort vom Mesh!
[14:33:45] 🔒📱➡️📡 @user → MeshUser (Private Chat)
```

### Node-Status Updates
Alle 3 Minuten (konfigurierbar) zeigt das System aktive Nodes:
```
[14:35:00] 📊 Letzte 10 aktive Nodes:
   1. Alice       (ID: 123456789) - zuletzt: 14:34:52
   2. Bob         (ID: 987654321) - zuletzt: 14:34:28
   3. Charlie     (ID: 456789123) - zuletzt: 14:33:15
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
- Prüfe IP-Adresse in `config.py`
- Stelle sicher, dass die Node erreichbar ist
- Prüfe Netzwerkverbindung

**2. "Telegram-Bot antwortet nicht"**
- Prüfe Bot-Token in `config.py`
- Stelle sicher, dass der Bot aktiv ist
- Prüfe Internet-Verbindung

**3. "Chat-ID Setup funktioniert nicht"**
- Starte im Setup-Modus: `TELEGRAM_CHAT_ID = ''`
- Sende `!id` an den Bot
- Kopiere die **komplette** Chat-ID inklusive Minuszeichen

**4. "Private Chats funktionieren nicht"**
- Stelle sicher, dass Meshtastic-Nachrichten als **private** Nachrichten gesendet werden
- Prüfe, ob das Secret korrekt eingegeben wurde
- Secrets sind case-sensitive!

**5. "Bot reagiert nicht auf Nachrichten in Gruppen"**
- ⚠️ **HÄUFIGSTER FEHLER**: Privacy-Settings falsch konfiguriert
- Gehe zu @BotFather → `/setprivacy` → deinen Bot wählen → `Disable`
- Status muss sein: `DISABLED` (nicht ENABLED!)
- Ohne diese Einstellung empfängt der Bot nur `/befehle` und @mentions


### Debug-Modus
```python
# In config.py:
LOG_LEVEL = 'DEBUG'
```

Zeigt detaillierte Informationen über alle Operationen.

### Datenverarbeitung
- **Nachrichten**: Werden nicht dauerhaft gespeichert
- **Node-IDs**: Nur für Status-Anzeige verwendet
- **Chat-IDs**: Nur für Weiterleitung verwendet


## 🔧 Modularer Aufbau & Anpassungen

### Dateistruktur
```
main.py              → Orchestrierung, Setup-Logik, Async-Koordination
config.py            → Zentrale Konfiguration, alle Einstellungen
message_handler.py   → Gruppenchat-Logik, Meshtastic ↔ Telegram Bridge
private_chat.py      → Private Chat-System, Secret-Authentifizierung, Bitcoin-API
terminal_output.py   → Logging, Emoji-Support, Node-Status-Tracking
```

## 📚 Dependencies

```bash
# Kern-Dependencies (requirements.txt)
meshtastic>=2.3.0           # Meshtastic-Kommunikation
python-telegram-bot>=20.0   # Telegram Bot API
pypubsub>=4.0.3             # Event-System für Meshtastic
aiohttp>=3.8.0              # HTTP-Client für APIs
```


**💡 Tipp**: Für Fragen und Support siehe die Terminal-Ausgabe - sie zeigt alle wichtigen Informationen in Echtzeit!

