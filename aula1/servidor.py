from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("Requisição GET recebida com sucesso!".encode("utf-8"))


    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        resposta = f"Dados recebidos via POST: {body}"
        self.wfile.write(resposta.encode("utf-8"))


    def do_PUT(self):
        cnt_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(cnt_length).decode("utf-8")

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        response = f"Dados recebidos via PUT: {body}"
        self.wfile.write(response.encode("utf-8"))

    
    def do_DELETE(self):
        cnt_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(cnt_length).decode("utf-8")
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        response = f"Dados recebidos via DELETE: {body}"
        self.wfile.write(response.encode("utf-8"))


if __name__ == "__main__":
    httpd = HTTPServer(("localhost", 8080), SimpleHandler)
    print("Servidor rodando em http://localhost:8080")
    httpd.serve_forever()
