# Projekt-Architektur: CLI-Chat mit KI-Teilnehmern

## 1. Übersicht
Eine kommandozeilenbasierte Chat-Anwendung, bestehend aus einem zentralen Server und mehreren Clients. Menschliche Nutzer und KI-gesteuerte Agenten können dem Chatraum beitreten und in Echtzeit miteinander kommunizieren.

## 2. Rahmenbedingungen
* **Sprache:** Python 3.x
* **Abhängigkeiten:** Zero-Dependencies (Nur Python Standardbibliothek).
* **UI:** Command Line Interface (CLI).

## 3. Kernkomponenten

### A. Der Server (`server.py`)
* **Aufgabe:** Verwaltet eingehende Verbindungen, hält eine Liste aller aktiven Clients (Menschen und KIs) und leitet eingehende Nachrichten an alle anderen Teilnehmer (Broadcasting) weiter.
* **Technologie:** Python `socket` Modul (TCP/IPv4) und `threading` für die parallele Verwaltung mehrerer Clients.

### B. Der Human-Client (`client.py`)
* **Aufgabe:** Verbindet sich mit dem Server. Nimmt Input vom Nutzer über die Tastatur an und stellt eingehende Nachrichten im Terminal dar.
* **Technologie:** `socket` für die Verbindung, `threading` (ein Thread lauscht permanent auf neue Nachrichten vom Server, der Main-Thread wartet auf Tastatureingaben des Nutzers).

### C. Der AI-Client (`ai_client.py`)
* **Aufgabe:** Agiert wie ein normaler Nutzer im Chatraum, wird aber von einem LLM (z.B. Gemini) gesteuert. Liest den Chatverlauf mit und antwortet, wenn er angesprochen wird (z.B. via "@AI_Bot").
* **Technologie:** Verbindet sich ebenfalls via `socket` mit dem Server. Nutzt `urllib.request`, um REST-API-Calls (HTTPS POST) an die KI-API zu senden, da keine externen SDKs wie `google-generativeai` oder `openai` erlaubt sind.