import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Carrega as variáveis de ambiente protegidas
load_dotenv()


def obter_conexao():
    # Busca a URL exclusivamente do arquivo .env
    DATABASE_URL = os.getenv('DATABASE_URL')

    # Trava a aplicação se a variável não existir, evitando conectar no vazio
    if not DATABASE_URL:
        raise ValueError("Erro de Segurança: A variável DATABASE_URL não foi encontrada no arquivo .env!")

    # O row_factory=dict_row retorna dicionários, facilitando o uso nos templates HTML
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
