# inicia o servidor Flask
from .routes import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True faz o servidor reiniciar automaticamente e detalha erros
    # (lembrar de retirar o debug=true depois do desenvolvimento)
    app.run(debug=True, host="127.0.0.1", port=5000)
