# define o endereço POST /api/leituras, para a requisição HTTP

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from . import controller


def create_app():
    app = Flask(__name__)

    # --- Rotas da API ---
    # rota POST
    @app.route('/api/leituras', methods=['POST'])
    def rota_receber_leitura():
        return controller.receber_leitura()

    # rota GET
    @app.route('/api/leituras', methods=['GET'])
    def rota_listar_leituras():
        return controller.listar_leituras()

    # (definir as outras rotas do T2 aqui)

    # --- MANIPULADOR DE ERROS ---.
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        # Transforma erros HTTP (abort) em respostas JSON
        response = jsonify(error={
            "code": e.code,
            "name": e.name,
            "description": e.description,
        })
        response.status_code = e.code
        return response

    return app
