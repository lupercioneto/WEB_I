class Request:
    def __init__(self, raw_request):
        self.method = ""
        self.path = ""
        self.headers = {}
        self.body = ""
        self._parse(raw_request)

    def _parse(self, raw_request):
        lines = raw_request.split("\r\n")
        if not lines: return

        # Parse request line
        request_line = lines[0]
        self.method, self.path, _ = request_line.split(" ")

        # Parse headers
        header_lines = lines[1:]
        empty_line_index = header_lines.index("") if "" in header_lines else -1
        
        if empty_line_index != -1:
            for line in header_lines[:empty_line_index]:
                key, value = line.split(": ", 1)
                self.headers[key] = value
            # Body is everything after the empty line
            self.body = "\r\n".join(header_lines[empty_line_index+1:])
    
    @classmethod
    def from_socket(cls, conn):
        raw_data = conn.recv(2048).decode('utf-8')
        return cls(raw_data)

class Response:
    def __init__(self, conn):
        self.conn = conn
        self.headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Server": "MeuServidorPython"
        }

    def _build_response(self, status_code, body=""):
        status_messages = {200: "OK", 302: "Found", 404: "Not Found", 400: "Bad Request"}
        status_text = status_messages.get(status_code, "Internal Server Error")

        response_line = f"HTTP/1.1 {status_code} {status_text}\r\n"
        
        # Add content length if there is a body
        if body:
            self.headers["Content-Length"] = str(len(body.encode('utf-8')))
        
        headers = "".join([f"{k}: {v}\r\n" for k, v in self.headers.items()])
        
        return (response_line + headers + "\r\n" + body).encode('utf-8')

    def send(self, status_code, body):
        response_data = self._build_response(status_code, body)
        self.conn.sendall(response_data)

    def redirect(self, location):
        self.headers["Location"] = location
        response_data = self._build_response(302) # 302 é o código para redirecionamento
        self.conn.sendall(response_data)