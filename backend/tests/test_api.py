# testa a aplicação, simulando requisições
import pytest
import os
import json
import shutil
from backend.app.main import app
from backend.config.settings import DATA_DIR, REGRAS_VALIDACAO

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
            <valor>3.0</valor>
        </leitura>
    </leituras>
</estufa>
"""
# todos os valores foram modificados
REGRAS_TESTE = {
  "temperatura": {
    "min": 6,
    "max": 30
  },
  "umidadeAr": {
    "min": 50,
    "max": 100
  },
  "umidadeSolo": {
    "min": 40,
    "max": 70
  },
  "co2": {
    "min": 400,
    "max": 1000
  },
  "luminosidade": {
    "min": 14000,
    "max": 40000
  },
  "pH": {
    "min": 4.0,
    "max": 6.0
  },
  "CE": {
    "min": 1.3,
    "max": 1.7
  }
}
REGRAS_DEFAULT = {
  "temperatura": {
    "min": 12,
    "max": 25
  },
  "umidadeAr": {
    "min": 60,
    "max": 80
  },
  "umidadeSolo": {
    "min": 60,
    "max": 80
  },
  "co2": {
    "min": 350,
    "max": 1000
  },
  "luminosidade": {
    "min": 15000,
    "max": 50000
  },
  "pH": {
    "min": 5.5,
    "max": 6.5
  },
  "CE": {
    "min": 1.2,
    "max": 1.8
  }
}

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

    # cria um 'regras.json' de teste limpo
    try:
        with open(REGRAS_VALIDACAO, 'w', encoding='utf-8') as f:
            json.dump(REGRAS_TESTE, f, indent=2)
    except Exception as e:
        print(f"Erro ao criar regras de teste: {e}")

    # roda o teste
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
    assert alerta['valor_lido'] == 3.0
    assert alerta['faixa_ideal'] == '4.0 - 6.0'
    assert alerta['ficheiro_origem'] == 'L03.xml'


def test_get_configuracoes(client):
    # testa o GET /api/configuracoes.
    # verifica se a API retorna as regras de validação corretas
    # que foram definidas no ficheiro 'regras.json'

    # chama GET /api/configuracoes
    response_get = client.get('/api/configuracoes')

    # --- Asserts ---
    assert response_get.status_code == 200
    # Verifica se o JSON retornado é igual
    # ao nosso dicionário de regras de teste (REGRAS_TESTE)
    assert response_get.json == REGRAS_TESTE


def test_post_configuracoes_reset(client):
    # testa o POST /api/configuracoes/reset.

    # muda as regras (PUT)
    response_put = client.put('/api/configuracoes',
                              json=REGRAS_TESTE)
    assert response_put.status_code == 200

    # confirmar a mudança (GET)
    response_get_1 = client.get('/api/configuracoes')
    # confere o primeiro valor que foi modificado
    assert response_get_1.json['temperatura']['min'] == 6

    # chama o reset (POST)
    response_reset = client.post('/api/configuracoes/reset')
    assert response_reset.status_code == 200
    assert response_reset.json['message'] == "Configurações restauradas para o padrão."

    # confirmar o reset (GET)
    response_get_2 = client.get('/api/configuracoes')
    assert response_get_2.status_code == 200
    # O JSON deve ser o de FÁBRICA
    assert response_get_2.json == REGRAS_DEFAULT
    # confere se o primeiro valor voltou ao padrão
    assert response_get_2.json['temperatura']['min'] == 12
