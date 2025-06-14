# COLOQUE ESTE CÓDIGO COMPLETO NO ARQUIVO: server/router.py

from .plumbing import Request, Response

class Router:
    def __init__(self):
        self.routes = []

    def add_route(self, path, methods):
        methods = methods or ["GET"]
        def decorator(handler_func):
            self.routes.append({
                "path": path,
                "handler": handler_func,
                "methods": methods
            })
            return handler_func
        return decorator

    def handle_connection(self, conn):
        try:
            request = Request.from_socket(conn)
            response = Response(conn)
            
            # Chama a nova função find_handler
            handler = self.find_handler(request)
            
            if handler:
                handler(request, response)
            else:
                response.send(404, "Página não encontrada.")
        except Exception as e:
            print(f"Erro ao processar requisição: {e}")
        finally:
            conn.close()
    
    # --- FUNÇÃO CORRIGIDA E CORRETAMENTE INDENTADA ---
    def find_handler(self, request):
        # Esta nova versão é mais precisa para encontrar a rota correta
        request_parts = request.path.strip('/').split('/')
        
        for route in self.routes:
            # Primeiro, verifica se o método da requisição (GET, POST) é permitido pela rota
            if request.method not in route["methods"]:
                continue

            route_parts = route["path"].strip('/').split('/')

            # Se a quantidade de "partes" da URL for diferente, não é a rota certa
            if len(request_parts) != len(route_parts):
                continue

            match = True
            # Compara cada parte da URL
            for i in range(len(route_parts)):
                # Se a parte da rota for <id>, ela é um coringa e aceita qualquer valor
                if route_parts[i] == "<id>":
                    continue
                # Se qualquer outra parte for diferente, a rota não corresponde
                if route_parts[i] != request_parts[i]:
                    match = False
                    break
            
            # Se todas as partes corresponderam, encontramos o manipulador correto
            if match:
                return route["handler"]

        # Se o loop terminar e nenhuma rota corresponder, retorna None
        return None