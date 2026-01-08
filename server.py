import http.server
import socketserver
import json
import time
import sys
import traceback
from notebooklm_client import NotebookLMClient

# Configuration from usage_example.py
from usage_example import HEADERS, AT_TOKEN

PORT = 8000

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

    def do_POST(self):
        if self.path == '/generate-infographic':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                youtube_url = data.get('youtube_url')
                if not youtube_url:
                    self.send_error(400, "Missing youtube_url")
                    return

                print(f"Received request for URL: {youtube_url}")
                
                # Logic from usage_example.py
                client = NotebookLMClient(headers=HEADERS, at_token=AT_TOKEN)
                
                # 1. Create Notebook
                print("Creating Notebook...")
                nb = client.create_notebook("Infographic Gen")
                nb_id = nb['notebook_id']
                print(f"Notebook ID: {nb_id}")

                # 2. Add Source
                print("Adding Source...")
                source_res = client.add_source(nb_id, "URL", json.dumps({"url": youtube_url}))
                source_id = source_res.get("source_id")
                
                if not source_id:
                     # Fallback
                     sources = client._get_sources(nb_id)
                     if sources:
                         source_id = sources[0]
                
                if not source_id:
                    raise Exception("Failed to add source or retrieve source ID")
                
                print(f"Source ID: {source_id}")
                
                # Wait for ingestion/stabilization
                time.sleep(5) 

                # 3. Run Infographic Tool
                print("Running Infographic Tool...")
                op_id = None
                for attempt in range(3):
                     tool_res = client.run_stdio_tool(nb_id, "infographic", "", source_ids=[source_id])
                     op_id = tool_res.get("operation_id")
                     if op_id:
                         break
                     time.sleep(2)
                
                if not op_id:
                    raise Exception("Failed to start infographic generation (no operation ID)")
                
                print(f"Operation ID: {op_id}")

                # 4. Wait for Result
                print("Waiting for completion...")
                image_url = None
                # Polling
                for _ in range(30): # 30 * 2 = 60 seconds max
                    result = client.wait_for_tool_execution(op_id, "infographic")
                    if result.get("status") == "DONE":
                        image_url = result.get('data')
                        break
                    time.sleep(2)
                
                if not image_url:
                    raise Exception("Timed out or failed to generate image")
                
                print(f"Success! Image URL: {image_url}")

                # Send Response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"image_url": image_url}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_error(404)

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

print(f"Server starting on port {PORT}...")
with ReusableTCPServer(("", PORT), RequestHandler) as httpd:
    print("Serving forever")
    httpd.serve_forever()
