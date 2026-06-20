import os
import requests
from dotenv import load_dotenv

# 1. Carrega o nosso "cofre" de senhas
load_dotenv()

CLIENT_ID = os.getenv('PLUGGY_CLIENT_ID')
CLIENT_SECRET = os.getenv('PLUGGY_CLIENT_SECRET')

# Fail-fast: Trava na hora se esquecermos de configurar o .env
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("❌ Erro de Arquitetura: Chaves da Pluggy não encontradas no arquivo .env!")

def testar_conexao_pluggy():
    print("🔄 Iniciando comunicação com o servidor da Pluggy...")

    # 2. Rota de Autenticação (Trocando o ID e Secret por um Token de Acesso temporário)
    auth_url = "https://api.pluggy.ai/auth"
    auth_payload = {
        "clientId": CLIENT_ID,
        "clientSecret": CLIENT_SECRET
    }

    try:
        # Faz o POST (igual fazemos no formulário HTML, mas via código)
        auth_response = requests.post(auth_url, json=auth_payload)
        auth_response.raise_for_status() # Verifica se o servidor devolveu algum erro HTTP

        # A Pluggy devolve um JSON. Nós pegamos só o valor do 'apiKey'
        token = auth_response.json().get('apiKey')
        print("✅ Sucesso Absoluto! Token de acesso gerado com segurança e sem expor senhas.")

        # 3. Teste Prático: Vamos pedir para a Pluggy listar os bancos de mentira (Sandbox)
        print("\n🏦 Buscando bancos de teste (Sandbox) disponíveis para conexão...")
        
        connectors_url = "https://api.pluggy.ai/connectors?sandbox=true"
        # Para acessar os dados, passamos o Token no "Cabeçalho" (Header) da requisição
        headers = {
            "X-API-KEY": token,
            "Content-Type": "application/json"
        }

        connectors_response = requests.get(connectors_url, headers=headers)
        connectors_response.raise_for_status()

        bancos = connectors_response.json().get('results', [])
        
        print(f"✅ {len(bancos)} instituições Sandbox encontradas prontas para uso. Aqui estão algumas:")
        for banco in bancos[:5]: # Mostra só os 5 primeiros para o terminal ficar limpo
            print(f" 🔹 {banco['name']} (ID da Instituição: {banco['id']})")

        print("\n🚀 A ponte está estruturada perfeitamente, Nicolas! O Open Finance é real.")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro na comunicação de rede: {e}")
        if e.response is not None:
            print(f"Detalhes que a Pluggy devolveu: {e.response.text}")

if __name__ == '__main__':
    testar_conexao_pluggy()