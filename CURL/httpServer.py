from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        file_content = self.rfile.read(content_length)
        filename = self.path.strip('/') or 'uploaded_file.pcap'
        filename = f"uploads/{filename}"
        with open(filename, 'wb') as f:
            f.write(file_content)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'File uploaded successfully')
    
    def do_GET(self):
        # Extract the path from the URL and remove leading/trailing slashes
        path = self.path.strip('/')
        
        # If no path is provided (e.g., request to "/"), return 404
        if not path:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File not found')
            return
        
        # Construct the full file path
        file_path = os.path.join('downloads', path)
        
        # Check if the file exists and is a regular file
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Send a 200 OK response
            self.send_response(200)
            # Set headers for a binary file download
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(os.path.getsize(file_path)))
            self.end_headers()
            # Read and send the file in chunks
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        else:
            # File not found, send 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File not found')

print("Starting Server")
httpd = HTTPServer(('0.0.0.0', 8000), SimpleHandler)
httpd.serve_forever()