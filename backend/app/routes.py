# define o endereço POST /api/leituras, para a requisição HTTP

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from . import controller


def create_app():
    app = Flask(__name__)

    # --- Rotas POST ---
    @app.route('/api/leituras', methods=['POST'])
    def rota_receber_leitura():
        return controller.receber_leitura()

    @app.route('/api/configuracoes/reset', methods=['POST'])
    def rota_resetar_configuracoes():
        return controller.resetar_configuracoes()

    # -- Rotas GET --
    @app.route('/api/leituras', methods=['GET'])
    def rota_listar_leituras():
        return controller.listar_leituras()

    @app.route('/api/alertas', methods=['GET'])
    def rota_listar_alertas():
        return controller.listar_alertas()

    @app.route('/api/configuracoes', methods=['GET'])
    def rota_listar_configurcoes():
        return controller.listar_configuracoes()

    @app.route('/api/exportar', methods=['GET'])
    def rota_exportar_dados():
        return controller.exportar_dados()
    
    # -- Rotas PUT --
    @app.route('/api/configuracoes', methods=['PUT'])
    def rota_atualizar_configuracoes():
        return controller.atualizar_configuracoes()

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
