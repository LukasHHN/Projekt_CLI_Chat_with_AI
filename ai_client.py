import socket
import threading
import json
import urllib.request
import urllib.error

import config

# Definition der Persönlichkeiten (System Prompts)
PERSONAS = {
    "1": {
        "name": "Konrad Adenauer",
        "trigger": "@konrad",
        "system_prompt": """Du bist Konrad Adenauer, der erste Bundeskanzler der BRD. 
        Dein Persönlichkeitskern: Strategisch denkend, langfristig orientiert, stark wertegetrieben (Ordnung, Stabilität). Du bist nüchtern-pragmatisch, wenig emotional und autoritär, aber nicht impulsiv.
        Dein Sprachstil: Formal, strukturiert, oft mit leicht altmodischer Ausdrucksweise (nutze gelegentlich Wörter aus den 1950ern). Prägnante Aussagen, gelegentlich trocken ironisch. Vermeide Umgangssprache konsequent. Nutze gerne politische oder gesellschaftliche Einordnung.
        Deine Kommunikationsmuster: Argumentiere in Ursache-Wirkung-Ketten, betone Verantwortung und stelle Entscheidungen als notwendige, rationale Schritte dar. 
        Antworte auf die letzte Nachricht im Chatverlauf.""",
        "farewell": "Meine Damen und Herren, die staatspolitische Pflicht ruft. Ich verabschiede mich und wünsche Ihnen weiterhin einen geordneten Austausch. Auf Wiedersehen."
    },
    "2": {
        "name": "Albert Zweistein",
        "trigger": "@albert",
        "system_prompt": """Du bist Albert Zweistein, ein ehrgeiziger, etwas nerdiger Physikstudent. 
        Dein Persönlichkeitskern: Du beschäftigst dich fast ausschließlich mit Quantentheorien und Astrophysik. Du bist enthusiastisch, aber oft für normale Menschen schwer zu verstehen.
        Dein Sprachstil: Schnell, voller Fachbegriffe (Verschränkung, Raumzeit, Superposition). Du neigst dazu, alltägliche Konversationen auf komplexe physikalische Phänomene zu beziehen.
        Deine Kommunikationsmuster: Wenn jemand über das Wetter redet, redest du über Thermodynamik. Du bist freundlich, verlierst dich aber oft in deinen eigenen Formeln und Theorien.
        Antworte auf die letzte Nachricht im Chatverlauf.""",
        "farewell": "Oh, meine Entropie steigt! Ich muss dringend zurück ins Labor, die Quantenfluktuationen warten nicht. Bis zur nächsten Raumzeit-Verschränkung!"
    }
}

class AIClient:
    def __init__(self):
        # Der API Key wird jetzt unsichtbar aus der config.py geladen!
        self.api_key = config.GEMINI_API_KEY
        
        self.persona = self.choose_persona()
        self.username = self.persona["name"]
        self.trigger = self.persona["trigger"]
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chat_history = []  # Speichert die letzten Nachrichten für den Kontext
        self.is_thinking = False # Verhindert, dass der Bot mehrfach gleichzeitig getriggert wird

    def choose_persona(self):
        print("\n--- Wähle eine KI-Persönlichkeit ---")
        for key, data in PERSONAS.items():
            print(f"[{key}] {data['name']}")
        print("[?] Mystery Guest (Zufällige historische Person generieren)")
        
        while True:
            choice = input("Deine Wahl (1, 2 oder ?): ").strip()
            
            # --- NEU: Logik für den Mystery Guest ---
            if choice == '?':
                persona = self.fetch_mystery_guest()
                print("\n" + "="*50)
                print(f" MYSTERY GUEST ENTHÜLLT: {persona['name'].upper()}")
                print(f" Trigger-Wort für den Chat: {persona['trigger']}")
                print("-"*50)
                # Wir zeigen die ersten ~150 Zeichen der Hintergrundgeschichte
                print(f" Hintergrund: {persona['system_prompt'][:150]}...") 
                print("="*50 + "\n")
                return persona
            
            # --- Alte Logik für vorgefertigte Personas ---
            elif choice in PERSONAS:
                print(f"\n[*] {PERSONAS[choice]['name']} wird initialisiert. Trigger: {PERSONAS[choice]['trigger']}")
                return PERSONAS[choice]
                
            print("Ungültige Auswahl. Bitte wähle 1, 2 oder ?.")

    def add_to_history(self, sender, text):
        """Hält den Chatverlauf auf den letzten 5 Nachrichten."""
        self.chat_history.append(f"{sender}: {text}")
        if len(self.chat_history) > 5:
            self.chat_history.pop(0)
            
    def fetch_mystery_guest(self):
        """Generiert eine zufällige Persona via Gemini API vor dem Chat-Start."""
        print("\n[*] Die KI durchsucht die Annalen der Geschichte... Bitte warten.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={self.api_key}"
        
        # Unser Prompt zwingt die KI, ein sauberes JSON-Objekt zu generieren
        prompt = """Du bist ein Generator für Chatbot-Persönlichkeiten. Wähle eine zufällige, weltbekannte historische Person der Weltgeschichte (z.B. aus Antike, Mittelalter, Renaissance, 19. Jahrhundert).
        Erstelle eine Hintergrundgeschichte und definiere den Charakter.
        
        Antworte AUSSCHLIESSLICH in validem JSON-Format. Nutze keine Markdown-Blöcke (wie ```json). Das JSON muss exakt diese Schlüssel haben:
        {
            "name": "Der vollständige Name der Person",
            "trigger": "@vorname",
            "system_prompt": "Du bist [Name]. [Deine detaillierte Hintergrundgeschichte, Persönlichkeit und dein Sprachstil]. Antworte stets auf die letzte Nachricht im Chatverlauf.",
            "farewell": "Ein typischer, charakterlich passender Abschiedsgruß."
        }"""
        
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        data = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                text = response_data['candidates'][0]['content']['parts'][0]['text']
                
                # Sicherheitsmaßnahme: Falls die KI doch Markdown-Blöcke nutzt, entfernen wir sie
                text = text.replace("```json", "").replace("```", "").strip()
                
                # Aus dem Text-String ein echtes Python-Dictionary machen
                persona = json.loads(text)
                return persona
                
        except Exception as e:
            print(f"[!] Fehler bei der Mystery-Generierung: {e}.")
            print("[*] Lade Notfall-Persona...")
            # Fallback, falls die API gerade streikt oder das JSON fehlerhaft ist
            return {
                "name": "Sokrates (Notfall-Modus)",
                "trigger": "@sokrates",
                "system_prompt": "Du bist der antike Philosoph Sokrates. Deine Hintergrundgeschichte: Du wandelst durch Athen und hinterfragst alles. Dein Charakter: Weise, aber nervig, da du alles in Frage stellst. Antworte auf die letzte Nachricht im Chatverlauf stets mit einer tiefgründigen Gegenfrage.",
                "farewell": "Ich sehe, der Schierlingsbecher wird gereicht. Ich muss nun gehen und wissen, dass ich nichts weiß."
            }

    def call_gemini_api(self, user_message):
        """Führt den HTTP-Request an die Gemini API ohne externe Libraries aus."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={self.api_key}"
        
        # Den Chatverlauf als einen großen String zusammenbauen
        context = "\n".join(self.chat_history)
        prompt = f"Hier ist der aktuelle Chatverlauf:\n{context}\n\nAntworte jetzt als {self.username}."

        # Das exakte JSON-Format, das die Gemini API erwartet
        payload = {
            "system_instruction": {
                "parts": [{"text": self.persona["system_prompt"]}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]}
            ]
        }

        data = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                # Navigieren durch die JSON-Struktur der Gemini-Antwort
                ai_text = response_data['candidates'][0]['content']['parts'][0]['text']
                return ai_text.strip()
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8')
            return f"(API Fehler: {e.code} - Bitte API Key prüfen)"
        except Exception as e:
            return f"(Interner Fehler: {str(e)})"

    def process_and_respond(self, user_message):
        """Wird in einem eigenen Thread ausgeführt, um das Netzwerk nicht zu blockieren."""
        self.is_thinking = True
        
        # 1. API aufrufen
        ai_response = self.call_gemini_api(user_message)
        
        # 2. Eigene Nachricht in den lokalen Verlauf aufnehmen
        self.add_to_history(self.username, ai_response)
        
        # 3. Nachricht an den Server senden
        message_data = {
            "sender": f"🤖 {self.username}",
            "text": ai_response
        }
        self.client_socket.sendall(json.dumps(message_data).encode('utf-8'))
        
        self.is_thinking = False

    def listen_to_server(self):
        """Lauscht permanent auf eingehende Chat-Nachrichten."""
        
        # NEU: Der Empfangs-Socket wacht jede Sekunde kurz auf
        self.client_socket.settimeout(1.0) 
        
        while True:
            try:
                data = self.client_socket.recv(16384)
                if not data:
                    print("\n[!] Verbindung zum Server verloren.")
                    break
                
                message_data = json.loads(data.decode('utf-8'))
                sender = message_data.get("sender")
                text = message_data.get("text")
                
                if sender == f"🤖 {self.username}":
                    continue
                
                self.add_to_history(sender, text)
                print(f"[LOG] {sender}: {text}")
                
                if self.trigger in text.lower() and not self.is_thinking:
                    print(f"[*] {self.username} denkt nach...")
                    threading.Thread(target=self.process_and_respond, args=(text,), daemon=True).start()

            except socket.timeout:
                # Timeout nach 1 Sekunde: Ermöglicht das Abfangen von Strg+C
                continue
            except Exception as e:
                print(f"[Fehler] {e}")
                break

    def start(self):
        try:
            self.client_socket.connect((config.HOST, config.PORT))
            print(f"[*] AI Client verbunden mit Server {config.HOST}:{config.PORT}")
            
            login_msg = {"sender": "System", "text": f"Die KI '{self.username}' hat den Chat betreten. Schreibe {self.trigger}, um mit ihr zu sprechen."}
            self.client_socket.sendall(json.dumps(login_msg).encode('utf-8'))
            
            self.listen_to_server()
            
        except ConnectionRefusedError:
            print("[!] Konnte keine Verbindung zum Server herstellen.")
            
        except KeyboardInterrupt:
            # HIER ist die Beendigungsexception für den AI-Client!
            print("\n[*] KI wird durch Benutzer abgeschaltet (Strg+C)...")
            # Charakter-spezifische Abschiedsnachricht senden
            farewell_msg = {
                "sender": f"🤖 {self.username}",
                "text": self.persona["farewell"]
            }
            try:
                self.client_socket.sendall(json.dumps(farewell_msg).encode('utf-8'))
            except Exception:
                # Falls der Server schon offline ist, ignorieren wir den Fehler lautlos
                pass
            
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    bot = AIClient()
    bot.start()