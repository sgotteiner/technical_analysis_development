import socket
import threading
import time

print("=========================================================")
print("[CDP PORT DUAL-STACK PROXY] BINDING IPV4 127.0.0.1 AND IPV6 ::1")
print("=========================================================")

def forward_data(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
    except:
        pass
    finally:
        source.close()
        destination.close()

def handle_ipv6_client(client_socket):
    try:
        # Connect to Chrome's IPv4 127.0.0.1:9222
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect(('127.0.0.1', 9222))
        
        t1 = threading.Thread(target=forward_data, args=(client_socket, target_socket))
        t2 = threading.Thread(target=forward_data, args=(target_socket, client_socket))
        t1.start()
        t2.start()
    except Exception as e:
        client_socket.close()

def start_ipv6_proxy():
    # Bind to IPv6 ::1 port 9223 or listen for localhost requests
    server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        server.bind(('::1', 9222))
        server.listen(10)
        print("Successfully bound IPv6 ::1:9222 -> IPv4 127.0.0.1:9222 proxy!")
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_ipv6_client, args=(client_sock,)).start()
    except Exception as e:
        print(f"Proxy bind status: {e}")

if __name__ == "__main__":
    start_ipv6_proxy()
