# testa a aplicação, simulando requisições
import pytest
from backend.app.main import app

XML_VALIDO = """
<estufa id="E01">
    <sensores>
        <sensor id="S01" tipo="temperatura"><unidade>°C</unidade></sensor>
    </sensores>
    <leituras>
        <leitura id="L01">
            <dataHora>2025-11-10T14:30:00</dataHora>
            <sensorRef ref="S01"/>
            <valor>22.5</valor>
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


# prepara o app para testes
@pytest.fixture
def client():
    # configura um cliente de teste do Flask
    app.config['TESTING'] = True  # modo de teste
    with app.test_client() as client:
        yield client  # disponibiliza o 'client' para os testes


# --- Testes ---
def test_post_leitura_sucesso(client):
    # envia um xml válido e espera um status 201

    response = client.post('/api/leituras',
                           data=XML_VALIDO,
                           content_type='application/xml')

    # verifica se a resposta foi 201 (Created)
    assert response.status_code == 201
    # verifica se a mensagem de sucesso está correta
    assert 'message' in response.json
    assert response.json['message'] == "Leitura recebida e validada (XSD) com sucesso."


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
