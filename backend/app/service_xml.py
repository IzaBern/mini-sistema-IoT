# manipulação e validação de XML
# aprova ou não baseado no xsd definido na T2

from lxml import etree
from flask import abort
from backend.config.settings import XSD_PATH

# --- Carregamento do Schema ---
try:
    schema_file = open(XSD_PATH, "rb")
    schema_doc = etree.parse(schema_file)
    XSD_SCHEMA = etree.XMLSchema(schema_doc)
    print("Log: Esquema XSD carregado com sucesso.")
except Exception as e:
    print(f"Erro crítico ao carregar XSD: {e}")
    XSD_SCHEMA = None


def validar_xsd(xml_string: str):
    # valida o xml usando o xsd
    # devolve um erro 400 (abort) caso a validação falhe

    if XSD_SCHEMA is None:
        # erro de configuração do servidor
        abort(500, description="Erro interno: Esquema XSD não está disponível.")

    try:
        xml_doc = etree.fromstring(xml_string.encode('utf-8'))
        XSD_SCHEMA.assertValid(xml_doc)

        print("Log: Validação XSD bem-sucedida.")
        return xml_doc  # retorna o documento parseado para o próximo passo

    except etree.XMLSyntaxError as e:
        # Erro de "parse" (XML mal formado)
        print(f"Erro de sintaxe XML: {e}")
        # Retorna um erro 400 (Bad Request) com a mensagem
        abort(400, description=f"XML mal formado: {e}")

    except etree.DocumentInvalid as e:
        # Erro de validação XSD (estrutura inválida)
        print(f"Erro de validação XSD: {e}")
        abort(400, description=f"XML falhou na validação do esquema (XSD): {e}")