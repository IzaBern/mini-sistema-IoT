# manipulação e validação de XML
# aprova ou não baseado no xsd definido na T2

import os
import json
import shutil
import pandas as pd
from lxml import etree
from flask import abort
from werkzeug.exceptions import HTTPException
from backend.config.settings import XSD_PATH, REGRAS_VALIDACAO, DATA_DIR, REGRAS_DEFAULT_PATH

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
        # 1. Criar o mapa de sensores (ex: "S04" -> "pH")
        sensor_map = {}
        for sensor_node in xml_doc.xpath("/estufa/sensores/sensor"):
            sensor_id = sensor_node.get("id")
            sensor_tipo = sensor_node.get("tipo")  # Sem .lower()
            sensor_map[sensor_id] = sensor_tipo

        # 2. Validar cada leitura
        for leitura_node in xml_doc.xpath("/estufa/leituras/leitura"):
            sensor_ref_id = leitura_node.xpath("./sensorRef/@ref")[0]
            valor = float(leitura_node.xpath("./valor/text()")[0])

            # Obtém o tipo (ex: "pH") sem .lower()
            tipo_sensor = sensor_map.get(sensor_ref_id)

            # Compara o tipo (ex: "pH") com as chaves (ex: "pH")
            if tipo_sensor in REGRAS_VALIDACAO:
                regras = REGRAS_VALIDACAO[tipo_sensor]
                if not (regras['min'] <= valor <= regras['max']):
                    leitura_id = leitura_node.get("id")
                    print(f"ALERTA (POST): Leitura ID {leitura_id} ({tipo_sensor}) está fora da faixa. Valor: {valor}")
                    # (Nota: O T3 não rejeita, apenas regista o alerta para o T4)

        print("Log: Validação de regras de negócio concluída.")
        return True

    except Exception as e:

        print(f"Erro durante a validação de regras de negócio: {e}")

        abort(400, description=f"Erro ao processar regras de negócio: {e}")


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
    # ATUALIZADO para incluir o tipo do sensor

    try:
        # Extrai o ID da estufa
        estufa_id = xml_doc.xpath("/estufa/@id")[0]

        sensor_map = {}
        for sensor_node in xml_doc.xpath("/estufa/sensores/sensor"):
            sensor_id = sensor_node.get("id")
            sensor_tipo = sensor_node.get("tipo")
            sensor_map[sensor_id] = sensor_tipo

        leituras_lista = []
        # Itera sobre cada nó <leitura>
        for leitura_node in xml_doc.xpath("/estufa/leituras/leitura"):
            sensor_ref_id = leitura_node.xpath("./sensorRef/@ref")[0]
            tipo_sensor = sensor_map.get(sensor_ref_id, "tipo_desconhecido")
            leitura_dict = {
                "id": leitura_node.get("id"),
                "dataHora": leitura_node.xpath("./dataHora/text()")[0],
                "sensorRef": leitura_node.xpath("./sensorRef/@ref")[0],
                "tipo": tipo_sensor,
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
        for ficheiro_xml in os.listdir(DATA_DIR):
            if not ficheiro_xml.endswith('.xml'):
                continue

            caminho_ficheiro = os.path.join(DATA_DIR, ficheiro_xml)
            xml_doc = etree.parse(caminho_ficheiro)

            estufa_id = xml_doc.xpath("/estufa/@id")[0]

            # 1. Criar o mapa de sensores (ex: "S04" -> "pH")
            sensor_map = {}
            for sensor_node in xml_doc.xpath("/estufa/sensores/sensor"):
                sensor_id = sensor_node.get("id")
                sensor_tipo = sensor_node.get("tipo")  # Sem .lower()
                sensor_map[sensor_id] = sensor_tipo

            # 2. Validar cada leitura contra as regras ATUAIS
            for leitura_node in xml_doc.xpath("/estufa/leituras/leitura"):
                sensor_ref_id = leitura_node.xpath("./sensorRef/@ref")[0]
                valor = float(leitura_node.xpath("./valor/text()")[0])

                # Obtém o tipo (ex: "pH") sem .lower()
                tipo_sensor = sensor_map.get(sensor_ref_id)

                # Compara o tipo (ex: "pH") com as chaves (ex: "pH")
                if tipo_sensor in REGRAS_VALIDACAO:
                    regras = REGRAS_VALIDACAO[tipo_sensor]

                    if not (regras['min'] <= valor <= regras['max']):
                        # Se estiver FORA da faixa, adiciona ao alerta
                        alerta_info = {
                            "estufa_id": estufa_id,
                            "leitura_id": leitura_node.get("id"),
                            "sensor_id": sensor_ref_id,
                            "tipo": tipo_sensor,
                            "valor_lido": valor,
                            "faixa_ideal": f"{regras['min']} - {regras['max']}",
                            "dataHora": leitura_node.xpath("./dataHora/text()")[0],
                            "ficheiro_origem": ficheiro_xml
                        }
                        alertas.append(alerta_info)

        print("Log: Verificação de alertas concluída.")
        return alertas

    except Exception as e:
        print(f"Erro ao ler dados de alerta: {e}")
        return []


def _get_regras_validacao():
    # lê o 'regras.json' e converte em um dicionário Python
    try:
        # Verifica se o ficheiro "live" existe
        if not os.path.exists(REGRAS_VALIDACAO):
            print("Log: 'regras_atuais.json' não encontrado. A restaurar dos padrões.")
            # Copia do default para o atual
            shutil.copyfile(REGRAS_DEFAULT_PATH, REGRAS_VALIDACAO)

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


def atualizar_configuracoes_regras(novas_regras: dict):
    # recebe um dicionário Python e sobrescreve o 'regras.json'
    print("Log: A atualizar ficheiro de regras de negócio...")
    try:
        # REGRAS_VALIDACAO é o caminho para o 'regras.json'
        with open(REGRAS_VALIDACAO, 'w', encoding='utf-8') as f:
            # Usa json.dump() para escrever o dicionário no ficheiro
            # indent=4 torna o ficheiro legível
            json.dump(novas_regras, f, indent=4)

        print("Log: Ficheiro de regras atualizado com sucesso.")
        return True

    except TypeError as e:
        # Erro se 'novas_regras' não for um formato válido
        print(f"Erro ao atualizar regras (Tipo de dados): {e}")
        abort(400, description=f"JSON de regras inválido: {e}")
    except (IOError, OSError) as e:
        # Erro se o servidor não tiver permissão para escrever no ficheiro
        print(f"Erro ao atualizar regras (IO): {e}")
        abort(500, description=f"Erro interno ao escrever no ficheiro de regras: {e}")


def resetar_regras_para_default():
    # força a cópia do 'regras_default.json' por cima do 'regras_atuais.json'
    try:
        print("Log: A restaurar regras de negócio para o padrão...")
        shutil.copyfile(REGRAS_DEFAULT_PATH, REGRAS_VALIDACAO)
        print("Log: Regras restauradas com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao restaurar regras: {e}")
        abort(500, description="Erro interno ao restaurar as regras.")


def exportar_dados_para_csv():
    # Lê todos os dados persistidos, achata e converte
    # para uma string no formato CSV
    print("Log: Iniciando exportação para CSV...")

    # obter os dados (reutiliza a nossa função do GET)
    todos_os_dados = ler_dados_persistidos()

    # "achata" (Flatten) os dados
    # transforma a lista de estufas (com listas de leituras)
    # numa lista simples onde cada item é uma leitura

    lista_achatada = []
    for estufa_data in todos_os_dados:
        estufa_id = estufa_data.get('estufa_id')
        for leitura in estufa_data.get('leituras', []):
            # Cria um novo dicionário "plano" para cada linha do CSV
            linha = {
                'estufa_id': estufa_id,
                'leitura_id': leitura.get('id'),
                'dataHora': leitura.get('dataHora'),
                'sensorRef': leitura.get('sensorRef'),
                'tipo': leitura.get('tipo'),
                'valor': leitura.get('valor')
            }
            lista_achatada.append(linha)

    # se não houver dados, retorna uma string vazia
    if not lista_achatada:
        print("Log: Sem dados para exportar para CSV.")
        return ""

    # converter para DataFrame e depois para CSV
    try:
        df = pd.DataFrame(lista_achatada)

        # Garante a ordem correta das colunas
        df = df[['estufa_id', 'leitura_id', 'dataHora', 'sensorRef', 'tipo', 'valor']]

        # Converte para string CSV.
        # Usamos ';' como separador e ',' como decimal (bom para Excel em PT/BR)
        csv_string = df.to_csv(index=False, sep=';', decimal=',')

        print("Log: Exportação CSV gerada com sucesso.")
        return csv_string

    except Exception as e:
        print(f"Erro ao converter dados para CSV: {e}")
        abort(500, description="Erro interno ao gerar o ficheiro CSV.")


def excluir_todas_as_leituras():
    # Exclui permanentemente todos os ficheiros .xml da pasta DATA_DIR.
    print("Log: Recebida ordem para excluir todos os dados...")
    try:
        ficheiros_excluidos = 0
        for ficheiro in os.listdir(DATA_DIR):
            if ficheiro.endswith('.xml'):
                filepath = os.path.join(DATA_DIR, ficheiro)
                os.remove(filepath)
                ficheiros_excluidos += 1

        print(f"Log: {ficheiros_excluidos} ficheiros excluídos.")
        return {"message": f"{ficheiros_excluidos} ficheiros de leitura foram excluídos com sucesso."}

    except Exception as e:
        print(f"Erro crítico ao excluir ficheiros: {e}")
        abort(500, description="Erro interno ao tentar excluir os dados.")
