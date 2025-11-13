# testa a aplicação, simulando requisições
import pytest
import os
from backend.app.main import app
from backend.config.settings import DATA_DIR

XML_VALIDO = """
<estufa id="E01">
    <sensores>
        <sensor id="S01" tipo="temperatura"><unidade>°C</unidade></sensor>
        <sensor id="S02" tipo="pH"><unidade>pH</unidade></sensor>
    </sensores>
    <leituras>
        <leitura id="L01">
            <dataHora>2025-11-10T14:30:00</dataHora>
            <sensorRef ref="S01"/>
            <valor>22.5</valor>
        </leitura>
        <leitura id="L02">
            <dataHora>2025-11-10T14:31:00</dataHora>
            <sensorRef ref="S02"/>
            <valor>6.0</valor>
        </leitura>        
    </leituras>
</estufa>
"""

# esse xml é inválido pq não define o sensor
XML_INVALIDO_XSD = """
<estufa id="E01">
    <leituras>
        <leitura id="L01">
            <dataHora>2025-11-10T14:30:00</dataHora>
            </leitura>
    </leituras>
</estufa>
"""

# esse xml é inválido pq o ph é 5, menor que o min 5.5
XML_INVALIDO_REGRAS = """
<estufa id="E01">
    <sensores>
        <sensor id="S01" tipo="temperatura"><unidade>°C</unidade></sensor>
        <sensor id="S02" tipo="pH"><unidade>pH</unidade></sensor>
    </sensores>
    <leituras>
        <leitura id="L03">
            <dataHora>2025-11-10T14:30:00</dataHora>
            <sensorRef ref="S01"/>
            <valor>22.5</valor>
        </leitura>
        <leitura id="L04">
            <dataHora>2025-11-10T14:31:00</dataHora>
            <sensorRef ref="S02"/>
            <valor>5.0</valor>
        </leitura>
    </leituras>
</estufa>
"""


# prepara o app para testes
@pytest.fixture
def client():
    # configura um cliente de teste do Flask
    # limpa a pasta de dados para garantir que
    # cada teste é 100% isolado.

    app.config['TESTING'] = True  # modo de teste

    # antes de cada teste
    for f in os.listdir(DATA_DIR):
        if f.endswith('.xml'):
            os.remove(os.path.join(DATA_DIR, f))

    with app.test_client() as client:
        yield client  # <-- teste roda aqui

    # depois de cada teste
    for f in os.listdir(DATA_DIR):
        if f.endswith('.xml'):
            os.remove(os.path.join(DATA_DIR, f))


# --- Testes ---
def test_post_leitura_sucesso(client):
    # caminho esperado do ficheiro
    expected_file_path = os.path.join(DATA_DIR, "L01.xml")
    # garante que o ficheiro não existe (a fixture limpou)
    assert not os.path.exists(expected_file_path)

    # envia um xml válido e espera um status 201
    response = client.post('/api/leituras',
                           data=XML_VALIDO,
                           content_type='application/xml')

    # verifica se a resposta foi 201 (Created)
    assert response.status_code == 201
    # verifica se a mensagem de sucesso está correta
    assert 'message' in response.json
    assert response.json['message'] == "Leitura recebida e validada (XSD) com sucesso."
    assert os.path.exists(expected_file_path)


def test_post_leitura_falha_xsd(client):
    # envia um XML que falha na validação xsd
    # espera um status 400
    response = client.post('/api/leituras',
                           data=XML_INVALIDO_XSD,
                           content_type='application/xml')

    # verifica se a resposta foi 400 (Bad Request)
    assert response.status_code == 400
    # verifica se a resposta de erro é um JSON
    assert 'error' in response.json
    # verifica se a mensagem de erro menciona o xsd
    assert "XSD" in response.json['error']['description']


def test_post_leitura_falha_regras_negocio(client):
    # xml válido no xsd, mas falha nas regras de negócio
    # deve chamar o alerta
    response = client.post('/api/leituras',
                           data=XML_INVALIDO_REGRAS,
                           content_type='application/xml')

    # chamado para o alerta de sensor fora da faixa
    assert response.status_code == 201
    # verifica se o ficheiro foi criado
    assert os.path.exists(os.path.join(DATA_DIR, "L03.xml"))


def test_post_leitura_falha_conflito_409(client):
    # conflito de duplicidade, tem dois xml com mesmo id
    # espera um status 409

    # primeira chamada
    response1 = client.post('/api/leituras',
                            data=XML_VALIDO,
                            content_type='application/xml')
    # Garante que a primeira chamada foi bem-sucedida
    assert response1.status_code == 201
    assert os.path.exists(os.path.join(DATA_DIR, "L01.xml"))

    # segunda chamada (ID duplicado)
    # envia o mesmo XML da primeira chamada
    response2 = client.post('/api/leituras',
                            data=XML_VALIDO,
                            content_type='application/xml')

    # verifica a falha de conflito
    assert response2.status_code == 409
    assert 'error' in response2.json
    assert "Conflito" in response2.json['error']['description']


def test_get_leituras(client):
    # Testa o GET /api/leituras.
    # cria dados válidos (POST) e verifica
    # se o GET os retorna corretamente.

    # cria os dados e garante q o ambiente tá limpo
    test_file_path = os.path.join(DATA_DIR, "L01.xml")
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

    # envia o xml válido para ser persistido
    response_post = client.post('/api/leituras',
                                data=XML_VALIDO,
                                content_type='application/xml')

    assert response_post.status_code == 201

    # chama o GET
    response_get = client.get('/api/leituras')

    # --- Asserts ---
    assert response_get.status_code == 200
    # A resposta é uma lista?
    assert isinstance(response_get.json, list)
    # A lista deve conter 1 item (o ficheiro que acabámos de criar)
    assert len(response_get.json) == 1
    # Verifica o conteúdo da resposta
    dados_estufa = response_get.json[0]
    assert dados_estufa['estufa_id'] == 'E01'
    # Verifica se as duas leituras do XML_VALIDO estão lá
    assert len(dados_estufa['leituras']) == 2
    assert dados_estufa['leituras'][0]['id'] == 'L01'
    assert dados_estufa['leituras'][0]['valor'] == 22.5
    assert dados_estufa['leituras'][1]['id'] == 'L02'
    assert dados_estufa['leituras'][1]['valor'] == 6.0

    # --- Limpeza ---
    if os.path.exists(test_file_path):
        os.remove(test_file_path)


def test_get_alertas(client):
    # Testa o GET /api/alertas.
    # posta um xml com regra inválida e chama o alerta
    # verifica se o GET retorna só a leitura inválida (a de pH 5.0).

    # ficheiro 100% certo, não deve gerar alertas.
    response_post_1 = client.post('/api/leituras',
                                  data=XML_VALIDO,
                                  content_type='application/xml')
    assert response_post_1.status_code == 201

    # ficheiro com 1 alerta (L03.xml)
    response_post_2 = client.post('/api/leituras',
                                  data=XML_INVALIDO_REGRAS,
                                  content_type='application/xml')
    assert response_post_2.status_code == 201

    # chama GET /api/alertas
    response_get = client.get('/api/alertas')

    # --- Asserts ---
    assert response_get.status_code == 200
    # a resposta é uma lista?
    assert isinstance(response_get.json, list)
    # a lista tem só um alerta?
    assert len(response_get.json) == 1

    # Verifica o conteúdo do alerta
    alerta = response_get.json[0]
    assert alerta['leitura_id'] == 'L04'
    assert alerta['tipo'] == 'pH'
    assert alerta['valor_lido'] == 5.0
    assert alerta['faixa_ideal'] == '5.5 - 6.5'
    assert alerta['ficheiro_origem'] == 'L03.xml'
