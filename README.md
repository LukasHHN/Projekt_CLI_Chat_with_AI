# AI-Chat-Plattform – CLI-Chat mit KI-Teilnehmern

Eine kommandozeilenbasierte Client-Server-Chat-Anwendung in Python. Menschliche Nutzer und KI-gesteuerte Agenten betreten denselben globalen Chatraum und kommunizieren in Echtzeit miteinander. Die KI-Teilnehmer treten mit eigener Persönlichkeit auf, können sich beim Beenden stilvoll verabschieden und lassen sich per „Mystery Guest" sogar ad hoc neu erfinden.

Das Projekt kommt komplett **ohne externe Abhängigkeiten** aus. Es wird ausschließlich die Python-Standardbibliothek verwendet.

## Inhaltsverzeichnis

- [Features](#features)
- [Architektur](#architektur)
- [Voraussetzungen](#voraussetzungen)
- [Schnellstart](#schnellstart)
- [AI-Personas](#ai-personas)
- [Mystery Guest](#mystery-guest)
- [Soft Shutdown](#soft-shutdown)
- [Projektstruktur](#projektstruktur)
- [Technische Entscheidungen](#technische-entscheidungen)
- [Planung und Dokumentation](#planung-und-dokumentation)
- [Erweiterbarkeit](#erweiterbarkeit)
- [Bekannte Grenzen](#bekannte-grenzen)
- [Sicherheit](#sicherheit)

## Features

- **Single-Room-Chat:** Jeder verbundene Client landet automatisch im selben globalen Chatraum.
- **Broadcasting:** Der Server leitet jede Nachricht an alle anderen Teilnehmer weiter.
- **Mehrere Clients parallel:** Menschen und KI-Agenten können gleichzeitig teilnehmen.
- **AI-Teilnehmer mit Persona:** Beim Start eines AI-Clients wird eine Persönlichkeit mit detaillierter Hintergrundgeschichte (System Prompt) gewählt.
- **Mystery Guest (`?`):** Die KI erfindet ad hoc eine völlig neue Persona mit Namen und Biografie, mit der der Client direkt beitritt.
- **Soft Shutdown:** Beim Beenden verabschiedet sich ein AI-Client mit einer zur Persona passenden Nachricht, bevor die Verbindung schließt.
- **Zero Dependencies:** Nur Python-Standardbibliothek, keine `pip install`-Schritte.

## Architektur

```
 ┌──────────────┐        ┌──────────────┐        ┌──────────────────┐
 │ Human-Client │        │ Human-Client │        │    AI-Client     │
 │  client.py   │        │  client.py   │        │  ai_client.py    │
 └──────┬───────┘        └──────┬───────┘        └───┬──────────┬───┘
        │ TCP                   │ TCP                │ TCP      │ HTTPS POST
        │                       │                    │          │ (urllib)
        └──────────────┬────────┴────────────────────┘          ▼
                       ▼                                 ┌──────────────┐
               ┌───────────────┐                         │   LLM-API    │
               │   server.py   │                         │   (Gemini)   │
               │  Broadcasting │                         └──────────────┘
               └───────────────┘
```

### Komponenten

| Komponente | Datei | Aufgabe |
|------------|-------|---------|
| Server | `server.py` | Nimmt Verbindungen an, führt die Liste aller aktiven Clients (Menschen und KIs) und verteilt eingehende Nachrichten per Broadcast an alle anderen Teilnehmer. |
| Human-Client | `client.py` | Verbindet sich mit dem Server, liest Tastatureingaben und zeigt eingehende Nachrichten im Terminal an. |
| AI-Client | `ai_client.py` | Verhält sich im Chat wie ein normaler Nutzer, wird aber von einem LLM gesteuert. Liest den Chatverlauf mit und antwortet, wenn er angesprochen wird (z. B. über `@AI_Bot`). |

### Nebenläufigkeit

- **Server:** Pro verbundenem Client läuft ein eigener Thread (`threading`). So blockiert ein langsamer Teilnehmer die anderen nicht.
- **Human-Client:** Ein Thread lauscht dauerhaft auf Nachrichten vom Server, der Main-Thread wartet auf Tastatureingaben.
- **AI-Client:** Verbindet sich ebenfalls per `socket` und sendet für die Antwortgenerierung HTTPS-POST-Anfragen an die LLM-REST-API (`urllib.request`). Externe SDKs wie `google-generativeai` oder `openai` sind nicht erlaubt und werden nicht verwendet.

## Voraussetzungen

- Python 3.x (Standardbibliothek genügt)
- Für AI-Clients: ein API-Key für den verwendeten LLM-Dienst (Gemini)
- Internetzugang für die AI-Clients (HTTPS-Anfragen an die LLM-API)

## Schnellstart

```bash
git clone <REPO-URL>
cd <REPO-ORDNER>
```

### 1. API-Key setzen (nur für AI-Clients)

```bash
# Git Bash / Linux / macOS
export GEMINI_API_KEY="dein_key_hier"

# Windows PowerShell
$env:GEMINI_API_KEY = "dein_key_hier"
```

### 2. Server starten

```bash
python server.py
```

### 3. Human-Client starten (eigenes Terminal)

```bash
python client.py
```

### 4. AI-Client starten (weiteres Terminal)

```bash
python ai_client.py
```

Beim Start des AI-Clients erscheint die Persona-Auswahl (siehe unten). Sobald ein AI-Client beigetreten ist, kannst du ihn im Chat direkt ansprechen, z. B. mit `@Tom Hallo, wie läuft die Farm?`.

Host, Port und weitere Startparameter: `<HIER ERGÄNZEN, z. B. --host / --port oder Konstanten in config>`

## AI-Personas

Jede Persona besteht aus einem detaillierten **System Prompt** mit Hintergrundgeschichte, Alltag, Sorgen, Sprachstil und Eigenheiten. Je ausführlicher die Biografie, desto glaubwürdiger und „plastischer" wirkt die Simulation im Chat.

| Persona | Kurzbeschreibung | Tonfall |
|---------|------------------|---------|
| **Tom Zawyer** | Besitzer einer abgelegenen Farm im Süden Mississippis. Kämpft mit den Folgen von Viehdiebstahl und der aktuellen Inflation. | rustikal, bodenständig |
| **Albert Zweistein** | Ehrgeiziger Physikstudent, fast ausschließlich mit Quantentheorien beschäftigt. Bezieht alltägliche Gespräche gern auf komplexe physikalische Phänomene. | neugierig, abschweifend, fachlich |
| `<weitere Personas ergänzen>` | | |

Die Persona-Prompts liegen in `<PFAD/DATEI EINTRAGEN, z. B. personas.py>`. Der AI-Client agiert eigenständig und bleibt in der gewählten Rolle, bis er beendet wird.

## Mystery Guest

In der Persona-Auswahl gibt es die Sonderoption **`?`**.

1. Der Client sendet eine Anfrage an die LLM-API mit dem Auftrag, eine neue, zufällige Persona zu erfinden: Name und eine kreative, einzigartige Hintergrundgeschichte.
2. Die Antwort der KI wird ausgewertet und als System Prompt des Clients verwendet.
3. Der Client tritt mit dieser neuen Identität dem Chat bei.

So entsteht ohne manuelle Vorkonfiguration eine theoretisch unendliche Vielfalt an Chat-Partnern.

## Soft Shutdown

Wird ein AI-Client beendet, bricht die Verbindung nicht abrupt ab. Stattdessen erzeugt die KI zunächst eine zur Persona passende Abschiedsnachricht und sendet sie in den Chat. Erst danach wird die Verbindung zum Server sauber geschlossen.

Beendet wird der AI-Client mit: `<TASTENKOMBINATION / BEFEHL EINTRAGEN, z. B. Strg+C oder /quit>`

## Projektstruktur

```
.
├── server.py          # Chat-Server (Verbindungen, Broadcasting)
├── client.py          # Human-Client (Tastatureingabe, Anzeige)
├── ai_client.py       # AI-Client (Persona, LLM-Anbindung, Soft Shutdown)
├── plan/              # Konzept, Architekturskizzen, Sequenzdiagramme, Spezifikationen
└── README.md
```

> Passe den Baum an, falls dein Repository weitere Dateien oder Module enthält (z. B. für Personas oder das gemeinsame Nachrichtenprotokoll).

## Technische Entscheidungen

- **`socket` + `threading` statt Frameworks:** Die Vorgabe „nur Standardbibliothek" macht TCP-Sockets mit einem Thread pro Client zur naheliegenden und gut verständlichen Lösung.
- **`urllib.request` für die KI-Anbindung:** Statt eines SDKs wird die REST-API per HTTPS-POST angesprochen. Das hält das Projekt abhängigkeitsfrei und zeigt den eigentlichen API-Aufruf transparent.
- **Server kennt keine KI:** Für den Server sind AI-Clients gewöhnliche Teilnehmer. Dadurch bleibt er schlank, und die KI-Logik lässt sich unabhängig weiterentwickeln.
- **Persona als Daten, nicht als Code:** Neue Persönlichkeiten sollen sich hinzufügen lassen, ohne die Client-Logik zu ändern.

## Planung und Dokumentation

Alle Planungsmaterialien liegen im Ordner [`plan/`](plan/):

- Technisches Konzept
- Architekturskizzen
- Sequenzdiagramme
- Technische Spezifikationen

Das Projekt wurde nach dem **AI-First-Ansatz** entwickelt: AI-Tools unterstützten Recherche, Konzeption, Implementierung und Prompt Engineering. Der Code wurde dabei nicht unreflektiert übernommen, sondern geprüft, strukturiert und nachvollzogen.

`<Optional: kurz beschreiben, welche AI-Tools in welchen Phasen genutzt wurden>`

## Erweiterbarkeit

Mögliche nächste Schritte:

- Weitere Personas durch zusätzliche System Prompts
- Mehrere Chaträume statt eines globalen Raums
- Anderer LLM-Anbieter durch Austausch der API-Anbindung im AI-Client
- Chat-Befehle (z. B. `/users`, `/quit`)
- Persistente Speicherung des Chatverlaufs

## Bekannte Grenzen

- Der Chat ist unverschlüsselt (reines TCP) und nur für lokale oder vertrauenswürdige Netze gedacht.
- Es gibt einen einzigen globalen Chatraum.
- Die Qualität der AI-Antworten hängt vom verwendeten Modell und vom System Prompt ab.
- AI-Clients benötigen eine Internetverbindung und einen gültigen API-Key. API-Aufrufe können Kosten verursachen oder durch Rate Limits begrenzt sein.

## Sicherheit

- Der API-Key gehört in eine Umgebungsvariable oder eine lokale `.env`-Datei, **niemals** in den Quellcode.
- Trage `.env` in die `.gitignore` ein, **bevor** du sie das erste Mal committest.
- Lege bei Bedarf eine `.env.example` mit Platzhaltern an und checke nur diese ein.
- Inhalte aus dem Chat werden in AI-Clients an die LLM-API gesendet. Teile im Chat keine vertraulichen Informationen.
