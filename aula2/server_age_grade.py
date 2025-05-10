from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])

def verify_age_or_grade():
    resultado_idade = None
    resultado_nota = None

    if request.method == "POST":
        if "idade" in request.form:
            idade = int(request.form["idade"])
            resultado_idade = "Acesso permitido" if idade >= 18 else "Acesso negado"

        elif "nota" in request.form:
            nota = float(request.form["nota"])
            
            if nota <= 3:
                resultado_nota = "Reprovado"
            elif nota <= 8:
                resultado_nota = "Aprovado"
            elif nota > 8 and nota <= 10:
                resultado_nota = "Excelente!"
            else:
                resultado_nota = "Nota inválida" 

    return render_template("index.html", resultado_idade=resultado_idade, resultado_nota=resultado_nota)

app.run(debug=True)

