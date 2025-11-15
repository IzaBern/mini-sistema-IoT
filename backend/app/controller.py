# cordena o fluxo da operação, recebe o request e envia para validação

from flask import request, jsonify, make_response
from . import service_xml


def receber_leitura():
    # controlador para o recebimento de novas leituras XML
    xml_data_string = request.data.decode('utf-8')

    if not xml_data_string:
        # abort 400, corpo da requisição está vazio
        return make_response(jsonify(error="Corpo da requisição está vazio."), 400)

    # validação xsd
    xml_doc = service_xml.validar_xsd(xml_data_string)
    # validação de regras
    service_xml.validar_regras_negocio(xml_doc)
    # serviço de persistência
    service_xml.persistir_xml(xml_data_string, xml_doc)

    # se tudo passou, retorna sucesso
    return make_response(jsonify(message="Leitura recebida e validada (XSD) com sucesso."), 201)


def listar_leituras():
    # listar todas as leituras persistidas
    dados = service_xml.ler_dados_persistidos()
    # retorna dados com status 200 (ok)
    return make_response(jsonify(dados), 200)


def listar_alertas():
    # chama os alertas
    dados_alertas = service_xml.ler_dados_de_alerta()
    # retorna dados com status 200 (ok)
    return make_response(jsonify(dados_alertas), 200)


def listar_configuracoes():
    # lista as configurações de regras atuais
    dados_regras = service_xml.ler_configuracoes_regras()
    if not dados_regras:
        # Se o ficheiro estiver vazio ou corrompido
        return make_response(jsonify(error="Ficheiro de regras não encontrado ou inválido."), 500)

    return make_response(jsonify(dados_regras), 200)


def atualizar_configuracoes():
    # controlador para atualizar as regras de negócio

    # pega o JSON enviado pelo utilizador no corpo (body) do pedido
    try:
        novas_regras = request.get_json()
        if not novas_regras:
            raise ValueError("Corpo (body) do JSON está vazio.")
    except Exception as e:
        return make_response(jsonify(error=f"JSON mal formado: {e}"), 400)

    service_xml.atualizar_configuracoes_regras(novas_regras)

    # retorna sucesso se tudo ok
    return make_response(jsonify(message="Configurações atualizadas com sucesso."), 200)


def resetar_configuracoes():
    # controlador para restaurar as regras para o padrão.
    service_xml.resetar_regras_para_default()
    return make_response(jsonify(message="Configurações restauradas para o padrão."), 200)


# backend/app/controller.py

# ... (imports de request, jsonify, make_response, service_xml) ...

# ... (funções existentes) ...

# --- NOVA FUNÇÃO EXPORTAR (RF8) ---
def exportar_dados():
    # controlador para exportar dados
    formato = request.args.get('formato', 'json')

    if formato.lower() != 'csv':
        return make_response(jsonify(error="Formato de exportação não suportado. Use ?formato=csv"), 400)

    # chamar o serviço para gerar a string CSV
    csv_data = service_xml.exportar_dados_para_csv()

    if not csv_data:
        return make_response(jsonify(message="Sem dados para exportar."), 200)

    # cria a Resposta de Ficheiro (Download)
    # 'Response' manual
    response = make_response(csv_data)
    # 'Header' para forçar o download
    response.headers["Content-Disposition"] = "attachment; filename=leituras.csv"
    # 'MIME type' para que o navegador saiba que é um CSV
    response.headers["Content-Type"] = "text/csv; charset=utf-8"

    return response


def excluir_leituras():
    # Controlador para o pedido de exclusão de todas as leituras.
    resultado = service_xml.excluir_todas_as_leituras()
    return make_response(jsonify(resultado), 200)
