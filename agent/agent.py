"""
Service Sentinel - Agent (Client)

Registers with the Monitor via TCP on startup, then sends a UDP heartbeat
ping every 3 seconds so the Monitor knows this agent is alive.
Also sends a TCP status report every 30 seconds.

Environment variables:
  AGENT_NAME   - unique name for this agent (default: "agent")
  MONITOR_HOST - hostname of the monitor container (default: "monitor")
"""

import socket
import time
import os
import json

AGENT_NAME   = os.environ.get("AGENT_NAME",   "agent")
MONITOR_HOST = os.environ.get("MONITOR_HOST", "monitor")
TCP_PORT     = 12001
UDP_PORT     = 12002

HEARTBEAT_INTERVAL   = 3   # seconds between UDP pings
STATUS_REPORT_EVERY  = 30  # seconds between TCP status updates


def tcp_send(event, info):
    """Send a JSON status message to the monitor over TCP."""
    payload = json.dumps({
        "name":  AGENT_NAME,
        "event": event,
        "info":  info,
    }).encode()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((MONITOR_HOST, TCP_PORT))
            s.sendall(payload)
    except Exception as e:
        print(f"[{AGENT_NAME}] TCP send failed: {e}", flush=True)


def main():
    print(f"[{AGENT_NAME}] Starting up...", flush=True)

    # Wait briefly to ensure the monitor is ready before connecting
    time.sleep(2)

    # Register with the monitor (TCP)
    tcp_send("register", f"Agent '{AGENT_NAME}' is online and ready.")
    print(f"[{AGENT_NAME}] Registered with monitor via TCP.", flush=True)

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    last_status_time = time.time()

    print(f"[{AGENT_NAME}] Sending heartbeat every {HEARTBEAT_INTERVAL}s...", flush=True)

    while True:
        # Send UDP heartbeat
        try:
            udp_sock.sendto(AGENT_NAME.encode(), (MONITOR_HOST, UDP_PORT))
            print(f"[{AGENT_NAME}] Heartbeat sent.", flush=True)
        except Exception as e:
            print(f"[{AGENT_NAME}] Heartbeat error: {e}", flush=True)

        # Periodic TCP status report
        if time.time() - last_status_time >= STATUS_REPORT_EVERY:
            tcp_send("status", f"Agent '{AGENT_NAME}' is healthy.")
            last_status_time = time.time()

        time.sleep(HEARTBEAT_INTERVAL)


if __name__ == "__main__":
    main()
