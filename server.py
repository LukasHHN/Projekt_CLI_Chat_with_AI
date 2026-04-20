import socket
import threading
import json

# Konfiguration
HOST = '127.0.0.1' # Localhost für den Test
PORT = 65432
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
            # Auf Nachrichten warten
            data = conn.recv(1024)
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
    # Option setzen, um den Port nach Neustart sofort wieder freizugeben
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[*] Server lauscht auf {HOST}:{PORT}")
        
        while True:
            conn, addr = server_socket.accept()
            clients.append(conn)
            
            # Neuen Thread für den Client starten
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True # Threads beenden sich, wenn das Hauptprogramm endet
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\n[*] Server wird heruntergefahren...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()