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
            
            handler = self.find_handler(request)
            
            if handler:
                handler(request, response)
            else:
                response.send(404, "Página não encontrada.")
        except Exception as e:
            print(f"Erro ao processar requisição: {e}")
        finally:
            conn.close()
    
    
    def find_handler(self, request):
        request_parts = request.path.strip('/').split('/')
        
        for route in self.routes:
            if request.method not in route["methods"]:
                continue

            route_parts = route["path"].strip('/').split('/')

            if len(request_parts) != len(route_parts):
                continue

            match = True

            for i in range(len(route_parts)):
                if route_parts[i] == "<id>":
                    continue
                if route_parts[i] != request_parts[i]:
                    match = False
                    break
            
            if match:
                return route["handler"]

        return None