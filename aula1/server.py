from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor rodando com Flask!"

app.run(debug=True)