# define os caminhos para facilitar a legibilidade
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XSD_PATH = os.path.join(BASE_DIR, "app", "model", "schema.xsd")
DATA_DIR = os.path.join(BASE_DIR, "data")
