import socket
import threading
import json
import sys

# Konfiguration (muss mit Server übereinstimmen)
HOST = '127.0.0.1'
PORT = 65432

def receive_messages(sock):
    """Läuft im Hintergrund und druckt Nachrichten auf den Bildschirm."""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\n[!] Verbindung zum Server verloren.")
                break
            
            message_data = json.loads(data.decode('utf-8'))
            sender = message_data.get("sender", "Unbekannt")
            text = message_data.get("text", "")
            
            # Der magische Terminal-Trick:
            # \r springt an den Anfang der Zeile
            # \033[2K löscht die aktuelle Zeile (damit der halbe User-Input verschwindet)
            # Danach drucken wir die Nachricht und bauen den Prompt "Du >" wieder auf.
            sys.stdout.write(f"\r\033[2K\033[93m{sender}:\033[0m {text}\nDu > ")
            sys.stdout.flush()
            
        except ConnectionAbortedError:
            break # Passiert beim sauberen Beenden
        except Exception as e:
            print(f"\n[Fehler im Empfangs-Thread] {e}")
            break

def start_client():
    # Benutzername abfragen
    username = input("Wähle einen Benutzernamen: ").strip()
    if not username:
        username = "Anonym"

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((HOST, PORT))
        print(f"[*] Verbunden mit Server {HOST}:{PORT}")
        print("[*] Tippe '/quit', um den Chat zu verlassen.\n")
        
        # Empfangs-Thread starten
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receive_thread.daemon = True
        receive_thread.start()
        
        # Hauptschleife für Benutzereingaben
        while True:
            msg_text = input("Du > ")
            
            if msg_text.lower() == '/quit':
                break
                
            if msg_text.strip(): # Keine leeren Nachrichten senden
                message_data = {
                    "sender": username,
                    "text": msg_text
                }
                client_socket.sendall(json.dumps(message_data).encode('utf-8'))
                
    except ConnectionRefusedError:
        print("[!] Konnte keine Verbindung zum Server herstellen. Läuft er?")
    except KeyboardInterrupt:
        print("\n[*] Beende Client...")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()