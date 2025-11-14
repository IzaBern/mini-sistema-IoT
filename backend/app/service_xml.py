# manipulação e validação de XML
# aprova ou não baseado no xsd definido na T2

import os
import json
from lxml import etree
from flask import abort
from werkzeug.exceptions import HTTPException
from backend.config.settings import XSD_PATH, REGRAS_VALIDACAO, DATA_DIR

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

    REGRAS_VALIDACAO = _get_regras_validacao()
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
                    # se tá fora da faixa, o alerta deve ser acionado
                    msg_erro = f"ALERTA: Leitura ID {leitura_id}: Valor {valor_leitura} para {tipo_sensor} está fora da faixa permitida ({min_val} - {max_val})."
                    print(f"Log: {msg_erro}")

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


def persistir_xml(xml_data_string: str, xml_doc):
    # salva a string xml original na pasta backend/data/
    # usa o id da primeira leitura como nome
    # verifica duplicidade
    print("Log: Iniciando persistência do XML...")
    try:
        # usa o id da primeira leitura no XML como nome
        # o id é necessário para verificar a duplicidade
        leitura_id = xml_doc.xpath("/estufa/leituras/leitura[1]/@id")[0]
        filename = f"{leitura_id}.xml"
        filepath = os.path.join(DATA_DIR, filename)

        # verifica duplicidade (requisito T3: 409 Conflict)
        if os.path.exists(filepath):
            msg_erro = f"Conflito: A leitura com ID {leitura_id} já existe."
            print(f"Log: {msg_erro}")
            abort(409, description=msg_erro)  # 409 Conflict

        # salva a 'xml_data_string' (texto original)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml_data_string)

        print(f"Log: Ficheiro salvo com sucesso em {filepath}")
        return True

    except HTTPException as e:
        raise e

    except IndexError:
        # Erro se o XPath não encontrar um ID de leitura (culpa do XML)
        msg_erro = "Erro de persistência: Não foi possível extrair um ID da leitura do XML."
        print(f"Log: {msg_erro}")
        abort(400, description=msg_erro)

    except (IOError, OSError, Exception) as e:
        # Erro ao gravar no disco (falta de permissão) ou outro bug.
        # Isto é um erro 500 (culpa do servidor).
        print(f"Erro inesperado na persistência: {e}")
        abort(500, description=f"Erro interno ao salvar o ficheiro: {e}")


def _xml_doc_para_dict(xml_doc):
    # converter um XML Doc (lxml) num dicionario
    # python limpo e legível (pronto para JSON).
    try:
        # Extrai o ID da estufa
        estufa_id = xml_doc.xpath("/estufa/@id")[0]
        leituras_lista = []
        # Itera sobre cada nó <leitura>
        for leitura_node in xml_doc.xpath("/estufa/leituras/leitura"):
            leitura_dict = {
                "id": leitura_node.get("id"),
                "dataHora": leitura_node.xpath("./dataHora/text()")[0],
                "sensorRef": leitura_node.xpath("./sensorRef/@ref")[0],
                "valor": float(leitura_node.xpath("./valor/text()")[0])
            }
            leituras_lista.append(leitura_dict)

        # Retorna um dicionário estruturado
        return {
            "estufa_id": estufa_id,
            "leituras": leituras_lista
        }
    except Exception as e:
        print(f"Erro ao converter XML para Dict: {e}")
        # Se um ficheiro no disco estiver corrompido, não quebra a API inteira
        return None


def ler_dados_persistidos():
    # lê todos os ficheiros XML da pasta 'data/', converte-os
    # para dicionários e retorna uma lista de todos os dados.
    print("Log: Iniciando leitura de dados persistidos...")
    todos_os_dados = []

    try:
        # lista todos os ficheiros no diretório de dados
        ficheiros = os.listdir(DATA_DIR)

        # filtra apenas os que são .xml
        xml_ficheiros = [f for f in ficheiros if f.endswith('.xml')]

        # itera, lê e converte cada ficheiro
        for ficheiro in xml_ficheiros:
            filepath = os.path.join(DATA_DIR, ficheiro)

            try:
                # Abre e lê o ficheiro XML
                with open(filepath, 'r', encoding='utf-8') as f:
                    xml_string = f.read()

                # Faz o parse
                xml_doc = etree.fromstring(xml_string.encode('utf-8'))

                # Converte para dicionário usando a nossa helper
                dados_convertidos = _xml_doc_para_dict(xml_doc)

                if dados_convertidos:
                    todos_os_dados.append(dados_convertidos)

            except Exception as e:
                # Loga um erro se um ficheiro específico falhar, mas continua
                print(f"Erro ao processar o ficheiro {ficheiro}: {e}")

        print("Log: Leitura e conversão de dados concluída.")
        return todos_os_dados

    except Exception as e:
        # Erro grave (ex: não consegue ler a pasta 'data/')
        print(f"Erro crítico ao ler dados persistidos: {e}")
        abort(500, description="Erro interno ao aceder à base de dados de XMLs.")


def ler_dados_de_alerta():
    # lê todos os XMLs persistidos, aplica as regras de negócio
    # retorna uma lista das leituras que estão fora dos limites.

    REGRAS_VALIDACAO = _get_regras_validacao()
    print("Log: Iniciando verificação de alertas...")
    alertas = []

    try:
        # lista todos os ficheiros no diretório de dados
        ficheiros = os.listdir(DATA_DIR)
        xml_ficheiros = [f for f in ficheiros if f.endswith('.xml')]

        # itera por cada ficheiro XML
        for ficheiro in xml_ficheiros:
            filepath = os.path.join(DATA_DIR, ficheiro)

            try:
                # Abre, lê e faz o parse do ficheiro
                with open(filepath, 'r', encoding='utf-8') as f:
                    xml_string = f.read()
                xml_doc = etree.fromstring(xml_string.encode('utf-8'))

                # Obtém o ID da estufa
                estufa_id = xml_doc.xpath("/estufa/@id")[0]

                # verificação de regras (reutilizada do POST)

                # descobre o tipo do sensor
                sensores = {}
                for sensor in xml_doc.xpath("/estufa/sensores/sensor"):
                    sensores[sensor.get("id")] = sensor.get("tipo")

                # itera sobre as leituras do ficheiro
                for leitura in xml_doc.xpath("/estufa/leituras/leitura"):
                    sensor_ref_id = leitura.xpath("./sensorRef/@ref")[0]
                    tipo_sensor = sensores.get(sensor_ref_id)
                    valor_leitura = float(leitura.xpath("./valor/text()")[0])

                    # verifica a regra
                    if tipo_sensor in REGRAS_VALIDACAO:
                        regra = REGRAS_VALIDACAO[tipo_sensor]
                        min_val = regra["min"]
                        max_val = regra["max"]

                        # se NAO estiver na faixa, é um alerta e vai pra lista
                        if not (min_val <= valor_leitura <= max_val):
                            alerta_info = {
                                "estufa_id": estufa_id,
                                "leitura_id": leitura.get("id"),
                                "sensor_id": sensor_ref_id,
                                "tipo": tipo_sensor,
                                "valor_lido": valor_leitura,
                                "faixa_ideal": f"{min_val} - {max_val}",
                                "dataHora": leitura.xpath("./dataHora/text()")[0],
                                "ficheiro_origem": ficheiro
                            }
                            alertas.append(alerta_info)

            except Exception as e:
                # Loga erro de um ficheiro específico, mas continua para o próximo
                print(f"Erro ao processar alertas do ficheiro {ficheiro}: {e}")

        print("Log: Verificação de alertas concluída.")
        return alertas

    except Exception as e:
        # Erro grave (ex: não consegue ler a pasta 'data/')
        print(f"Erro crítico ao ler dados de alerta: {e}")
        abort(500, description="Erro interno ao processar alertas.")


def _get_regras_validacao():
    # lê o 'regras.json' e converte em um dicionário Python
    try:
        with open(REGRAS_VALIDACAO, 'r', encoding='utf-8') as f:
            regras = json.load(f)
        return regras
    except FileNotFoundError:
        print(f"Erro Crítico: Ficheiro de regras não encontrado em {REGRAS_VALIDACAO}")
        return {}  # retorna regras vazias se o ficheiro faltar
    except json.JSONDecodeError:
        print(f"Erro Crítico: Ficheiro de regras {REGRAS_VALIDACAO} tem um JSON inválido.")
        return {}
    except Exception as e:
        print(f"Erro inesperado ao ler ficheiro de regras: {e}")
        return {}


def ler_configuracoes_regras():
    # lê as regras de validação atuais do 'regras.json'
    print("Log: A ler ficheiro de regras de negócio...")
    return _get_regras_validacao()
