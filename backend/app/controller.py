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

    # serviço de persistência (fazer)

    # se tudo passou, retorna sucesso
    return make_response(jsonify(message="Leitura recebida e validada (XSD) com sucesso."), 201)
