"""
CS 381 - Assignment 5
TCP/UDP Ping Server

Listens on two separate ports (TCP and UDP) for incoming ping messages.
Responds to each ping with a "received" pong message.

Ports used:
  TCP: 12001
  UDP: 12002
"""

import socket
import threading

TCP_PORT = 12001
UDP_PORT = 12002
HOST = ""  # bind to all interfaces


def handle_tcp_client(conn, addr):
    """Handle a single TCP client connection."""
    print(f"[TCP] Connection from {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode()
            print(f"[TCP] Received from {addr}: {message!r}")
            conn.sendall(b"received")
    finally:
        conn.close()
        print(f"[TCP] Connection closed: {addr}")


def tcp_server():
    """Run the TCP server in a loop, spawning a thread per client."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, TCP_PORT))
        s.listen()
        print(f"[TCP] Listening on port {TCP_PORT}")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True)
            t.start()


def udp_server():
    """Run the UDP server in a loop."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, UDP_PORT))
        print(f"[UDP] Listening on port {UDP_PORT}")
        while True:
            data, addr = s.recvfrom(1024)
            message = data.decode()
            print(f"[UDP] Received from {addr}: {message!r}")
            s.sendto(b"received", addr)


def main():
    print("Starting TCP/UDP Ping Server...")
    tcp_thread = threading.Thread(target=tcp_server, daemon=True)
    udp_thread = threading.Thread(target=udp_server, daemon=True)

    tcp_thread.start()
    udp_thread.start()

    print("Server running. Press Ctrl+C to stop.")
    try:
        tcp_thread.join()
        udp_thread.join()
    except KeyboardInterrupt:
        print("\nServer shutting down.")


if __name__ == "__main__":
    main()
