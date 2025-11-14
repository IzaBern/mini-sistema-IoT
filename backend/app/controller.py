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
