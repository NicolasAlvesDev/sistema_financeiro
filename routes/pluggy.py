import os
import requests
from flask import Blueprint, redirect, url_for, flash
from database import obter_conexao

pluggy_bp = Blueprint('pluggy', __name__)


@pluggy_bp.route('/sincronizar-banco', methods=['POST'])
def sincronizar_banco():
    client_id = os.environ.get('PLUGGY_CLIENT_ID')
    client_secret = os.environ.get('PLUGGY_CLIENT_SECRET')
    item_id = os.environ.get('PLUGGY_ITEM_ID')

    if not client_id or not client_secret or not item_id:
        flash('Algumas chaves da Pluggy não estão configuradas no .env!', 'danger')
        return redirect(url_for('dashboard.index'))

    try:
        auth_response = requests.post(
            "https://api.pluggy.ai/auth", json={"clientId": client_id, "clientSecret": client_secret})
        auth_response.raise_for_status()
        token = auth_response.json().get('apiKey')
        headers = {"X-API-KEY": token, "Content-Type": "application/json"}

        contas_response = requests.get(
            f"https://api.pluggy.ai/accounts?itemId={item_id}", headers=headers)
        contas_response.raise_for_status()
        contas_pluggy = contas_response.json().get('results', [])

        if not contas_pluggy:
            flash('Nenhuma conta ativa foi encontrada.', 'warning')
            return redirect(url_for('dashboard.index'))

        # Procura especificamente a Conta Corrente (BANK)
        conta_corrente = next(
            (c for c in contas_pluggy if c.get('type') == 'BANK'), contas_pluggy[0])
        conta_id_pluggy = conta_corrente['id']
        saldo_real_api = float(conta_corrente.get('balance', 0.0))

        transacoes_response = requests.get(
            f"https://api.pluggy.ai/v2/transactions?accountId={conta_id_pluggy}", headers=headers)
        transacoes_response.raise_for_status()
        transacoes_pluggy = transacoes_response.json().get('results', [])

        conexao = obter_conexao()
        cursor = conexao.cursor()

        # Atualiza apenas a conta local que é do tipo 'corrente'
        cursor.execute("SELECT id FROM contas WHERE tipo = 'corrente' LIMIT 1")
        conta_local = cursor.fetchone()

        if conta_local:
            conta_id_local = conta_local['id']
            cursor.execute("UPDATE contas SET saldo = %s WHERE id = %s",
                           (saldo_real_api, conta_id_local))
        else:
            conta_id_local = None

        novas_transacoes_contador = 0
        for t in transacoes_pluggy:
            descricao = t['description']
            valor = float(t['amount'])
            data_api = t['date'][:10]

            cursor.execute(
                "SELECT id FROM transacoes WHERE descricao = %s AND valor = %s AND data = %s", (descricao, valor, data_api))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO transacoes (descricao, valor, data, conta_id, categoria_id, conta_destino_id)
                    VALUES (%s, %s, %s, %s, NULL, NULL)
                """, (descricao, valor, data_api, conta_id_local))
                novas_transacoes_contador += 1

        conexao.commit()
        cursor.close()
        conexao.close()

        if novas_transacoes_contador > 0:
            flash(
                f'Sincronização concluída! {novas_transacoes_contador} novas transações.', 'success')
        else:
            flash('Seu extrato e saldo real já estão 100% atualizados.', 'info')

    except Exception as e:
        print(f"Erro: {e}")
        flash('Falha ao tentar sincronizar os dados.', 'danger')

    return redirect(url_for('dashboard.index'))
