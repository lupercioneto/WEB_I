import socket
from .router import Router

class Server:


    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.router = Router()


    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Servidor iniciado em http://{self.host}:{self.port}/usuarios")

        while True:
            conn, addr = server_socket.accept()
            self.router.handle_connection(conn)


    def route(self, path, methods=None):
        return self.router.add_route(path, methods)