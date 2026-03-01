"""
CS 381 - Assignment 5
TCP/UDP Ping Client

Lets the user choose TCP or UDP, then sends 10 ping messages to the server
and prints the round-trip time (RTT) for each.

Server host/ports:
  TCP: 12001
  UDP: 12002
"""

import socket
import time

SERVER_HOST = "localhost"
TCP_PORT = 12001
UDP_PORT = 12002
NUM_PINGS = 10
TIMEOUT = 2.0  # seconds


def ping_tcp():
    """Send 10 pings over TCP and print RTT for each."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(TIMEOUT)
        s.connect((SERVER_HOST, TCP_PORT))
        print(f"\nConnected to {SERVER_HOST}:{TCP_PORT} via TCP\n")

        for i in range(1, NUM_PINGS + 1):
            message = "sent"
            start = time.perf_counter()
            s.sendall(message.encode())
            response = s.recv(1024).decode()
            rtt = (time.perf_counter() - start) * 1000  # ms
            print(f"Ping {i:2d}: response={response!r}  RTT={rtt:.3f} ms")


def ping_udp():
    """Send 10 pings over UDP and print RTT for each."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(TIMEOUT)
        print(f"\nSending UDP pings to {SERVER_HOST}:{UDP_PORT}\n")

        for i in range(1, NUM_PINGS + 1):
            message = "sent"
            start = time.perf_counter()
            s.sendto(message.encode(), (SERVER_HOST, UDP_PORT))
            try:
                response, _ = s.recvfrom(1024)
                rtt = (time.perf_counter() - start) * 1000  # ms
                print(f"Ping {i:2d}: response={response.decode()!r}  RTT={rtt:.3f} ms")
            except socket.timeout:
                print(f"Ping {i:2d}: Request timed out")


def main():
    print("TCP/UDP Ping Client")
    print("===================")
    choice = input("Select protocol (TCP/UDP): ").strip().upper()

    if choice == "TCP":
        ping_tcp()
    elif choice == "UDP":
        ping_udp()
    else:
        print(f"Unknown protocol: {choice!r}. Enter TCP or UDP.")


if __name__ == "__main__":
    main()
