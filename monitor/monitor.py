"""
Service Sentinel - Monitor (Server)

Central server that tracks the health of Agent containers.

Sockets:
  TCP port 12001 - receives reliable status reports and registration messages
  UDP port 12002 - receives lightweight heartbeat pings every 3 seconds

Flags an agent as DOWN if no heartbeat arrives within 9 seconds.
All events are written to a persistent audit log at /logs/sentinel_audit.log.
"""

import socket
import threading
import time
import os
import json
from datetime import datetime

TCP_PORT = 12001
UDP_PORT = 12002
HOST = ""                # bind to all interfaces
HEARTBEAT_TIMEOUT = 9   # seconds before an agent is flagged DOWN
LOG_FILE = "/logs/sentinel_audit.log"

# { agent_name: last_heartbeat_time }
agents = {}
agent_status = {}        # "UP" or "DOWN"
agents_lock = threading.Lock()


def log(message):
    """Print a timestamped message to stdout and append it to the audit log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# UDP listener - heartbeat pings
# ---------------------------------------------------------------------------

def udp_listener():
    """Receive UDP heartbeat pings from agents."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, UDP_PORT))
        log(f"[UDP] Listening for heartbeats on port {UDP_PORT}")
        while True:
            data, addr = s.recvfrom(1024)
            name = data.decode().strip()
            now = time.time()

            with agents_lock:
                is_new = name not in agents
                agents[name] = now

                if is_new:
                    agent_status[name] = "UP"
                    log(f"[HEARTBEAT] First ping from '{name}' ({addr[0]})")
                elif agent_status.get(name) == "DOWN":
                    agent_status[name] = "UP"
                    log(f"[RECOVERY]  Agent '{name}' is back online.")
                else:
                    log(f"[HEARTBEAT] Ping from '{name}' ({addr[0]})")


# ---------------------------------------------------------------------------
# TCP listener - status reports and registration
# ---------------------------------------------------------------------------

def handle_tcp_client(conn, addr):
    """Handle one TCP connection (registration or status report)."""
    try:
        data = conn.recv(4096)
        if not data:
            return
        try:
            report = json.loads(data.decode())
            name = report.get("name", addr[0])
            event = report.get("event", "status").upper()
            info = report.get("info", "")
            log(f"[TCP]       {event} from '{name}': {info}")
        except json.JSONDecodeError:
            log(f"[TCP]       Raw message from {addr}: {data.decode()!r}")
    finally:
        conn.close()


def tcp_listener():
    """Accept TCP connections for status reports and registration."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, TCP_PORT))
        s.listen()
        log(f"[TCP] Listening for status reports on port {TCP_PORT}")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True)
            t.start()


# ---------------------------------------------------------------------------
# Watchdog - failure detection
# ---------------------------------------------------------------------------

def watchdog():
    """Periodically check for agents that have gone silent."""
    log(f"[WATCHDOG]  Failure detection active (timeout: {HEARTBEAT_TIMEOUT}s)")
    while True:
        time.sleep(1)
        now = time.time()
        with agents_lock:
            for name, last_seen in agents.items():
                elapsed = now - last_seen
                if elapsed > HEARTBEAT_TIMEOUT and agent_status.get(name) != "DOWN":
                    agent_status[name] = "DOWN"
                    log(
                        f"[ALERT]     Agent '{name}' is DOWN — "
                        f"no heartbeat for {elapsed:.1f}s"
                    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    os.makedirs("/logs", exist_ok=True)
    log("=== Service Sentinel Monitor Starting ===")
    log(f"  TCP status reports : port {TCP_PORT}")
    log(f"  UDP heartbeat pings: port {UDP_PORT}")
    log(f"  Failure timeout    : {HEARTBEAT_TIMEOUT}s")
    log("==========================================")

    threads = [
        threading.Thread(target=udp_listener, daemon=True),
        threading.Thread(target=tcp_listener, daemon=True),
        threading.Thread(target=watchdog,     daemon=True),
    ]
    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        log("Monitor shutting down.")


if __name__ == "__main__":
    main()
