from flask import Flask, request, render_template

app = Flask(__name__)

R_USER = "admin"
R_PASSWORD = "1234"
MAX_TRYS = 3
trys = 0

@app.route("/", methods=["GET", "POST"])

def login():  
    resultado = ""
    global trys

    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == R_USER and senha == R_PASSWORD:
            resultado = "Acesso permitido!"
            trys = 0  

        else:
            trys += 1
            if trys >= MAX_TRYS:
                resultado = "Acesso bloqueado!"
            else:
                resultado = f"Credenciais incorretas. Você tem {MAX_TRYS - trys} tentativas restantes."

    return render_template("login.html", resultado=resultado)


@app.route("/numeros", methods=["GET", "POST"])
def numeros():
    resultados = []

    if request.method == "POST":
        number = int(request.form["numero"])

        if number == 3:
            pass # Ignora o número 3
        elif number == -1:
            resultados.append("Saindo do programa.")
        else:
            resultados.append(f"Você digitou: {number}")
    
    return render_template("numeros.html", resultados=resultados)

app.run(debug=True)
