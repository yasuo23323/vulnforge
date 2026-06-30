#!/usr/bin/env python3
"""Simple HTTP server that serves frontend and proxies /api to backend."""
import http.server
import urllib.request
import os

BACKEND = "http://localhost:8000"
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            url = BACKEND + self.path
            try:
                resp = urllib.request.urlopen(url, timeout=10)
                self.send_response(resp.status)
                self.send_header("Access-Control-Allow-Origin", "*")
                for k, v in resp.headers.items():
                    if k.lower() in ("content-type", "content-length"):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(f'{{"error":"{e}"}}'.encode())
            return
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            url = BACKEND + self.path
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len) if content_len else b""
            req = urllib.request.Request(url, data=body,
                headers={"Content-Type": self.headers.get("Content-Type", "application/json")},
                method="POST")
            try:
                resp = urllib.request.urlopen(req, timeout=30)
                self.send_response(resp.status)
                self.send_header("Access-Control-Allow-Origin", "*")
                for k, v in resp.headers.items():
                    if k.lower() in ("content-type", "content-length"):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(f'{{"error":"{e}"}}'.encode())

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.join(script_dir, "frontend", "dist"))
    server = http.server.HTTPServer(("0.0.0.0", 3000), ProxyHandler)
    print(f"Frontend proxy at http://localhost:3000 -> API at {BACKEND}")
    server.serve_forever()