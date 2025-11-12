# define os caminhos para facilitar a legibilidade
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XSD_PATH = os.path.join(BASE_DIR, "app", "model", "schema.xsd")
DATA_DIR = os.path.join(BASE_DIR, "data")

REGRAS_VALIDACAO = {
    "temperatura": {"min": 12, "max": 25},
    "umidadeAr": {"min": 60, "max": 80},
    "umidadeSolo": {"min": 60, "max": 80},
    "co2": {"min": 350, "max": 1000},
    "luminosidade": {"min": 15000, "max": 50000},
    "pH": {"min": 5.5, "max": 6.5},
    "CE": {"min": 1.2, "max": 1.8}
}
