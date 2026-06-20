import os
import requests
from dotenv import load_dotenv

# Carrega nossas senhas do .env
load_dotenv()

CLIENT_ID = os.getenv('PLUGGY_CLIENT_ID')
CLIENT_SECRET = os.getenv('PLUGGY_CLIENT_SECRET')

# Este é o ID da conexão que você criou no Sandbox!
ITEM_ID = '9ca83e6f-22af-4f3d-95d7-a076bbf8be6d'

def buscar_extrato_bancario():
    print("🔄 1. Autenticando com a Pluggy...")
    
    # 1. Pegando o Token de Acesso
    auth_response = requests.post(
        "https://api.pluggy.ai/auth",
        json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET}
    )
    auth_response.raise_for_status()
    token = auth_response.json().get('apiKey')
    
    headers = {
        "X-API-KEY": token,
        "Content-Type": "application/json"
    }

    print("✅ Token gerado! Buscando contas atreladas à conexão...")

    # 2. Buscando as contas dentro dessa conexão (Item)
    contas_url = f"https://api.pluggy.ai/accounts?itemId={ITEM_ID}"
    contas_response = requests.get(contas_url, headers=headers)
    contas_response.raise_for_status()
    
    contas = contas_response.json().get('results', [])
    
    if not contas:
        print("❌ Nenhuma conta encontrada para este Item.")
        return

    # Vamos pegar a primeira conta da lista (a Conta Corrente com saldo positivo)
    conta_principal = contas[0]
    conta_id = conta_principal['id']
    nome_conta = conta_principal['name']
    saldo = conta_principal['balance']

    print(f"\n🏦 Conta Encontrada: {nome_conta}")
    print(f"💰 Saldo Atual: R$ {saldo}")
    print("-" * 50)
    print("📊 EXTRATO RECENTE:")

    # 3. Buscando as transações exclusivas dessa conta (AGORA USANDO A V2 DA API!)
    transacoes_url = f"https://api.pluggy.ai/v2/transactions?accountId={conta_id}"
    transacoes_response = requests.get(transacoes_url, headers=headers)
    transacoes_response.raise_for_status()
    
    transacoes = transacoes_response.json().get('results', [])

    # Exibindo as 10 últimas transações formatadas
    for t in transacoes[:10]:
        data_formatada = t['date'][:10] # Pega só o YYYY-MM-DD
        descricao = t['description']
        valor = t['amount']
        
        # Lógica visual simples para o terminal
        if valor > 0:
            print(f"🟢 {data_formatada} | + R$ {abs(valor):.2f} | {descricao}")
        else:
            print(f"🔴 {data_formatada} | - R$ {abs(valor):.2f} | {descricao}")

    print("-" * 50)
    print("🚀 Sucesso! Esses dados já estão em formato JSON, prontos para ir pro seu banco de dados!")

if __name__ == '__main__':
    buscar_extrato_bancario()