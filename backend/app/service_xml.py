# manipulação e validação de XML
# aprova ou não baseado no xsd definido na T2

from lxml import etree
from flask import abort
from werkzeug.exceptions import HTTPException
from backend.config.settings import XSD_PATH, REGRAS_VALIDACAO

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
    # devolve o documento lxml parseado em caso de sucesso

    if XSD_SCHEMA is None:
        # erro de configuração do servidor
        abort(500, description="Erro interno: Esquema XSD não está disponível.")

    try:
        xml_doc = etree.fromstring(xml_string.encode('utf-8'))
        XSD_SCHEMA.assertValid(xml_doc)

        print("Log: Validação XSD bem-sucedida.")
        return xml_doc  # retorna o documento parseado

    except etree.XMLSyntaxError as e:
        # Erro de "parse" (XML mal formado)
        print(f"Erro de sintaxe XML: {e}")
        abort(400, description=f"XML mal formado: {e}")

    except etree.DocumentInvalid as e:
        # Erro de validação XSD (estrutura inválida)
        print(f"Erro de validação XSD: {e}")
        abort(400, description=f"XML falhou na validação do esquema (XSD): {e}")
    except Exception as e:
        # Outro erro inesperado no parse
        print(f"Erro inesperado no parse/validação XSD: {e}")
        abort(500, description=f"Erro interno no processamento do XML: {e}")


def validar_regras_negocio(xml_doc):
    # valida as regras de negócio (faixas de valores) do xml
    # recebe um documento lxml (retornado pelo validar_xsd).
    print("Log: Iniciando validação de regras de negócio...")

    try:
        # cria um dicionário com todos os sensores
        # ID_do_Sensor -> tipo (ex: "S01" -> "pH")
        sensores = {}
        # pega todas as leituras
        for sensor in xml_doc.xpath("/estufa/sensores/sensor"):
            sensor_id = sensor.get("id")
            sensor_tipo = sensor.get("tipo")
            sensores[sensor_id] = sensor_tipo

        # pega todas as leituras
        for leitura in xml_doc.xpath("/estufa/leituras/leitura"):
            leitura_id = leitura.get("id")

            sensor_ref_id = leitura.xpath("./sensorRef/@ref")[0]
            tipo_sensor = sensores.get(sensor_ref_id)
            valor_leitura = float(leitura.xpath("./valor/text()")[0])

            # verifica a regra para o tipo de sensor
            if tipo_sensor in REGRAS_VALIDACAO:
                regra = REGRAS_VALIDACAO[tipo_sensor]
                min_val = regra["min"]
                max_val = regra["max"]

                if not (min_val <= valor_leitura <= max_val):
                    # se tá fora da faixa, aborta a requisição e
                    # solta a mensagem de erro e o código 400
                    msg_erro = f"Leitura ID {leitura_id}: Valor {valor_leitura} " \
                               f"para {tipo_sensor} está fora da faixa permitida " \
                               f"({min_val} - {max_val})."
                    print(f"Log: {msg_erro}")
                    abort(400, description=msg_erro)

        print("Log: Validação de regras de negócio bem-sucedida.")
        return True

    except HTTPException as e:
        # exceção 'abort', re-levanta (re-raise) ela para o Flask
        # deixa o manipulador de erros do routes.py pegar
        raise e

    except (IndexError, ValueError, KeyError, TypeError):
        # captura erros esperados de XPath ou conversão (ex: float(), dict key)
        msg_erro = "Erro de regra de negócio: Estrutura interna do XML " \
                   "inválida (ex: leitura sem valor ou sensorRef)."
        print(f"Log: {msg_erro}")
        abort(400, description=msg_erro)

    except Exception as e:
        # bugs ou erros inesperados
        print(f"Erro inesperado na validação de regras: {e}")
        abort(500, description=f"Erro interno ao processar regras de negócio: {e}")
