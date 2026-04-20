import socket
import threading
import json
import config

# Konfiguration
clients = []       # Liste aller aktiven Client-Sockets

def broadcast(message_data, sender_sock=None):
    """Sendet eine JSON-Nachricht an alle verbundenen Clients, außer dem Absender."""
    encoded_msg = json.dumps(message_data).encode('utf-8')
    
    for client in clients[:]: # Kopie der Liste iterieren, falls sich diese ändert
        if client != sender_sock:
            try:
                client.sendall(encoded_msg)
            except Exception as e:
                # Falls Senden fehlschlägt (z.B. Client hart beendet), Socket entfernen
                print(f"[BROADCAST FEHLER] Client wird entfernt: {e}")
                clients.remove(client)
                client.close()

def handle_client(conn, addr):
    """Wird für jeden Client in einem eigenen Thread ausgeführt."""
    print(f"[NEUE VERBINDUNG] {addr} hat den Raum betreten.")
    try:
        while True:
            # Auf Nachrichten warten, Erhöhung der Nachrichtengröße auf 16KB für längere AI-Antworten
            data = conn.recv(16384)
            if not data:
                break # Leere Daten bedeuten, der Client hat sich getrennt
            
            # JSON decodieren
            message_data = json.loads(data.decode('utf-8'))
            print(f"[LOG] {message_data.get('sender')}: {message_data.get('text')}")
            
            # An alle anderen verteilen
            broadcast(message_data, conn)
            
    except Exception as e:
        print(f"[TRENNUNG/FEHLER] Verbindung zu {addr} abgebrochen: {e}")
    finally:
        if conn in clients:
            clients.remove(conn)
        conn.close()
        print(f"[INFO] {addr} wurde abgemeldet. Aktive Nutzer: {len(clients)}")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((config.HOST, config.PORT))
        server_socket.listen()
        
        # NEU: Der Socket wacht jede Sekunde kurz auf
        server_socket.settimeout(1.0) 
        
        print(f"[*] Server lauscht auf {config.HOST}:{config.PORT}")
        
        while True:
            try:
                conn, addr = server_socket.accept()
                clients.append(conn)
                
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.daemon = True 
                client_thread.start()
                
            except socket.timeout:
                # Timeout nach 1 Sekunde: Wir machen einfach mit der Schleife weiter.
                # Genau in diesem Moment kann Python das Strg+C registrieren!
                continue 
                
    except KeyboardInterrupt:
        # HIER ist die Beendigungsexception!
        print("\n[*] Server wird durch Benutzer heruntergefahren (Strg+C)...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()