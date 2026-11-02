import http.server
import os
import socket
import ssl
import threading
import time

PORTA_DNS = 5053
PORTA_HTTPS = 4443
IP_SERVER = "127.0.0.1"
DOMINIO = "www.mioesercizio.local"
CERT_FILE = "server.pem"

def passaggio_dhcp():
  print("\n--- [STEP 1: DHCP] ---")
  print("[Client] Invio richiesta DHCP Discover...")
  time.sleep(0.5)
  print("[DHCP Server] Assegnato IP Client: 192.168.1.50")
  print(f"[DHCP Server] Configurato IP Server DNS: {IP_SERVER}")
  print("-----------------------\n")

def avvia_server_dns():
  try:
    sock_dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_dns.bind((IP_SERVER, PORTA_DNS))
    print(f"[DNS Server] Attivo sulla porta {PORTA_DNS}...")

    while True:
      dati, indirizzo = sock_dns.recvfrom(512)
      print(f"\n--- [STEP 2: DNS Request] ---")
      print(
          f"[DNS Server] Ricevuta richiesta di risoluzione per:"
          f" '{DOMINIO.decode() if isinstance(DOMINIO, bytes) else DOMINIO}'"
          f" da {indirizzo}"
      )

      sock_dns.sendto(IP_SERVER.encode(), indirizzo)
      print(f"[DNS Server] Risposto con IP: {IP_SERVER}")
      print("-----------------------------\n")
  except Exception as e:
    print(f"[DNS Server Errore]: {e}")

def avvia_server_https():
  if not os.path.exists(CERT_FILE):
    print(
        f"[ERRORE HTTPS]: Il file del certificato '{CERT_FILE}' non esiste!"
    )
    print("Per testare l'HTTPS, devi generare un certificato autofirmato.")
    return

  class GestoreSemplice(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
      self.send_response(200)
      self.send_header("Content-type", "text/html; charset=utf-8")
      self.end_headers()
      risposta_html = (
          "<h1>Esercizio Completato! Connessione HTTPS Protetta e"
          " Funzionante.</h1>"
      )
      self.wfile.write(risposta_html.encode("utf-8"))

    def log_message(self, format, *args):
      pass

  try:
    server_http = http.server.HTTPServer(
        (IP_SERVER, PORTA_HTTPS), GestoreSemplice
    )

    contesto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contesto_ssl.load_cert_chain(certfile=CERT_FILE)
    server_http.socket = contesto_ssl.wrap_socket(
        server_http.socket, server_side=True
    )

    print(f"[HTTPS Server] Attivo in modo sicuro sulla porta {PORTA_HTTPS}...")
    server_http.serve_forever()
  except Exception as e:
    print(f"[HTTPS Server Errore]: {e}")

def esegui_client():
  time.sleep(1.5)

  passaggio_dhcp()

  print(f"[Client] Chiedo al DNS l'IP di {DOMINIO}")
  sock_client_dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock_client_dns.sendto(DOMINIO.encode(), (IP_SERVER, PORTA_DNS))

  ip_risolto, _ = sock_client_dns.recvfrom(512)
  ip_risolto = ip_risolto.decode()
  print(f"[Client] DNS Risolto! L'IP di {DOMINIO} e' {ip_risolto}")

  print(f"\n--- [STEP 3: HTTPS Connection] ---")
  print(f"[Client] Inizio Handshake TCP/SSL verso {ip_risolto}:{PORTA_HTTPS}...")

  contesto_client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
  contesto_client.check_hostname = False
  contesto_client.verify_mode = ssl.CERT_NONE

  try:
    with socket.create_connection((ip_risolto, PORTA_HTTPS)) as sock_tcp:
      with contesto_client.wrap_socket(
          sock_tcp, server_hostname=DOMINIO
      ) as sock_ssl:
        print("[Client] Connessione SSL cifrata stabilita con successo!")

        richiesta_http = (
            f"GET / HTTP/1.1\r\nHost: {DOMINIO}\r\nConnection: close\r\n\r\n"
        )
        sock_ssl.sendall(richiesta_http.encode())

        risposta = sock_ssl.recv(1024).decode()
        print("\n[Client] Risposta ricevuta dal Server HTTPS:")
        print(risposta)
        print("----------------------------------\n")
  except Exception as e:
    print(f"[Client Errore di connessione]: {e}")

if __name__ == "__main__":
  thread_dns = threading.Thread(target=avvia_server_dns, daemon=True)
  thread_dns.start()

  thread_https = threading.Thread(target=avvia_server_https, daemon=True)
  thread_https.start()

  esegui_client()
