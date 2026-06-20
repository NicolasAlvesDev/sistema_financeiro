import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import obter_conexao
from dotenv import load_dotenv
import requests

# ==========================================================================
# CONFIGURAÇÃO E AMBIENTE SEGURO
# ==========================================================================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get(
    'FLASK_SECRET_KEY', 'chave_padrao_caso_esqueca_o_env')


@app.before_request
def proteger_rotas():
    rotas_publicas = ['login', 'static']
    if request.endpoint not in rotas_publicas and 'usuario_id' not in session:
        return redirect(url_for('login'))

# ==========================================================================
# ROTAS DE AUTENTICAÇÃO
# ==========================================================================


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        user = cursor.fetchone()
        cursor.close()
        conexao.close()

        if user and check_password_hash(user['senha_hash'], senha):
            session['usuario_id'] = user['id']
            session['usuario_nome'] = user['usuario']
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos!', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================================================
# PAINEL PRINCIPAL (DASHBOARD COM NAVEGAÇÃO TEMPORAL)
# ==========================================================================


@app.route('/')
def dashboard():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    # Captura o mês e ano do filtro na URL. Caso não ache, pega o momento atual.
    mes_atual = request.args.get('mes', type=int)
    ano_atual = request.args.get('ano', type=int)

    if not mes_atual or not ano_atual:
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year

    # Lógica de cálculo dos botões de retroceder e avançar o mês
    if mes_atual == 1:
        mes_anterior, ano_anterior = 12, ano_atual - 1
    else:
        mes_anterior, ano_anterior = mes_atual - 1, ano_atual

    if mes_atual == 12:
        mes_proximo, ano_proximo = 1, ano_atual + 1
    else:
        mes_proximo, ano_proximo = mes_atual + 1, ano_atual

    meses_nome = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    nome_mes_exibido = f"{meses_nome[mes_atual]} de {ano_atual}"

    # 1. NET WORTH ACUMULADO (Ativos - Passivos históricos)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN c.tipo != 'passivo' THEN c.saldo_inicial ELSE 0 END), 0) +
            COALESCE(SUM(CASE WHEN c.tipo != 'passivo' THEN t.valor ELSE 0 END), 0) +
            COALESCE(SUM(CASE WHEN c_dest.tipo != 'passivo' THEN ABS(t.valor) ELSE 0 END), 0) as ativos,
            
            COALESCE(SUM(CASE WHEN c.tipo = 'passivo' THEN c.saldo_inicial ELSE 0 END), 0) +
            COALESCE(SUM(CASE WHEN c.tipo = 'passivo' THEN t.valor ELSE 0 END), 0) +
            COALESCE(SUM(CASE WHEN c_dest.tipo = 'passivo' THEN -ABS(t.valor) ELSE 0 END), 0) as passivos
        FROM contas c
        LEFT JOIN transacoes t ON c.id = t.conta_id
        LEFT JOIN contas c_dest ON t.conta_destino_id = c_dest.id
    """)
    patrimonio = cursor.fetchone()
    ativos = patrimonio['ativos']
    passivos = patrimonio['passivos']
    net_worth = ativos + passivos

    # 2. TAXA DE APORTE DO MÊS SELECIONADO (Foca em aportes puros e descarta transferências)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN cat.tipo = 'receita' THEN t.valor ELSE 0 END), 0) as receitas,
            COALESCE(SUM(CASE WHEN cat.tipo = 'aporte' THEN ABS(t.valor) ELSE 0 END), 0) as aportes
        FROM transacoes t
        JOIN categorias cat ON t.categoria_id = cat.id
        WHERE EXTRACT(MONTH FROM t.data) = %s
          AND EXTRACT(YEAR FROM t.data) = %s
          AND t.conta_destino_id IS NULL
    """, (mes_atual, ano_atual))
    fluxo_mes = cursor.fetchone()
    receitas_mes = fluxo_mes['receitas']
    aportes_mes = fluxo_mes['aportes']

    taxa_aporte = 0
    if recipes_mes := receitas_mes > 0:
        taxa_aporte = round((aportes_mes / receitas_mes) * 100, 1)

    # 3. MONITORAMENTO DE TETO DE GASTOS MENSAL
    cursor.execute("""
        SELECT 
            c.nome as categoria, o.limite, COALESCE(SUM(ABS(t.valor)), 0) as gasto_atual,
            CASE WHEN o.limite > 0 THEN ROUND((COALESCE(SUM(ABS(t.valor)), 0) / o.limite) * 100) ELSE 0 END as porcentagem
        FROM orcamentos o
        JOIN categorias c ON o.categoria_id = c.id
        LEFT JOIN transacoes t ON c.id = t.categoria_id 
            AND EXTRACT(MONTH FROM t.data) = %s
            AND EXTRACT(YEAR FROM t.data) = %s
            AND t.conta_destino_id IS NULL
        GROUP BY c.nome, o.limite
    """, (mes_atual, ano_atual))
    orcamentos = cursor.fetchall()

    # 4. GRÁFICO DE APEXCHARTS (Apenas categorias com saldo consumido no mês)
    cursor.execute("""
        SELECT c.nome as categoria, COALESCE(SUM(ABS(t.valor)), 0) as total
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE c.tipo IN ('despesa_fixa', 'despesa_variavel', 'aporte')
          AND EXTRACT(MONTH FROM t.data) = %s
          AND EXTRACT(YEAR FROM t.data) = %s
          AND t.conta_destino_id IS NULL
        GROUP BY c.nome
        HAVING COALESCE(SUM(ABS(t.valor)), 0) > 0
    """, (mes_atual, ano_atual))
    dados_grafico = cursor.fetchall()

    labels_grafico = [row['categoria'] for row in dados_grafico]
    valores_grafico = [float(row['total']) for row in dados_grafico]

    # Histórico de transações pertencentes somente ao mês selecionado
    cursor.execute("""
        SELECT t.descricao, t.valor, t.data, c.nome as categoria, t.conta_destino_id
        FROM transacoes t 
        LEFT JOIN categorias c ON t.categoria_id = c.id 
        WHERE EXTRACT(MONTH FROM t.data) = %s AND EXTRACT(YEAR FROM t.data) = %s
        ORDER BY t.data DESC
    """, (mes_atual, ano_atual))
    transacoes_mes = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('index.html',
                           saldo=net_worth, ativos=ativos, passivos=abs(
                               passivos),
                           taxa_aporte=taxa_aporte, orcamentos=orcamentos,
                           transacoes=transacoes_mes,
                           labels_grafico=labels_grafico, valores_grafico=valores_grafico,
                           nome_mes_exibido=nome_mes_exibido,
                           mes_ant=mes_anterior, ano_ant=ano_anterior,
                           mes_prox=mes_proximo, ano_prox=ano_proximo)

# ==========================================================================
# EXTRATO DETALHADO (COM FILTRO DE TRANSFERÊNCIAS)
# ==========================================================================


@app.route('/extrato')
def extrato():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    filtro_tipo = request.args.get('tipo', '')
    filtro_conta = request.args.get('conta_id', '')

    query = """
        SELECT t.id, t.descricao, t.valor, t.data, c.nome as categoria, 
               co.nome as conta, co_dest.nome as conta_destino, t.conta_destino_id
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN contas co ON t.conta_id = co.id
        LEFT JOIN contas co_dest ON t.conta_destino_id = co_dest.id
        WHERE 1=1
    """
    parametros = []

    if filtro_tipo == 'receita':
        query += " AND t.valor > 0 AND t.conta_destino_id IS NULL"
    elif filtro_tipo == 'despesa':
        query += " AND t.valor < 0 AND t.conta_destino_id IS NULL"
    elif filtro_tipo == 'transferencia':
        query += " AND t.conta_destino_id IS NOT NULL"

    if filtro_conta:
        query += " AND (t.conta_id = %s OR t.conta_destino_id = %s)"
        parametros.append(filtro_conta)
        parametros.append(filtro_conta)

    query += " ORDER BY t.data DESC"

    cursor.execute(query, tuple(parametros))
    transacoes_filtradas = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM contas")
    contas = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('extrato.html', transacoes=transacoes_filtradas, contas=contas, filtro_tipo=filtro_tipo, filtro_conta=filtro_conta)

# ==========================================================================
# CADASTRO DE NOVA TRANSAÇÃO OU TRANSFERÊNCIA INTERNA
# ==========================================================================


@app.route('/nova-transacao', methods=['GET', 'POST'])
def nova_transacao():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        tipo_mov = request.form['tipo_movimentacao']

        if tipo_mov == 'despesa' or tipo_mov == 'transferencia':
            valor = -abs(valor)

        data = request.form['data']
        categoria_id = request.form['categoria_id'] if request.form['categoria_id'] != "" else None
        conta_id = request.form['conta_id'] if request.form['conta_id'] != "" else None

        # Mapeia conta de destino apenas se o tipo for transferência interna
        conta_destino_id = request.form['conta_destino_id'] if (
            tipo_mov == 'transferencia' and request.form['conta_destino_id'] != "") else None

        cursor.execute("""
            INSERT INTO transacoes (descricao, valor, data, categoria_id, conta_id, conta_destino_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (descricao, valor, data, categoria_id, conta_id, conta_destino_id))
        conexao.commit()

        cursor.close()
        conexao.close()
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT id, nome FROM categorias")
    categorias = cursor.fetchall()
    cursor.execute("SELECT id, nome FROM contas")
    contas = cursor.fetchall()

    cursor.close()
    conexao.close()
    return render_template('nova_transacao.html', categories=categorias, categorias=categorias, contas=contas)

# ==========================================================================
# GESTÃO DE COMPROMISSOS MENSAIS (CONTAS FIXAS)
# ==========================================================================


@app.route('/agendamentos', methods=['GET', 'POST'])
def agendamentos():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        dia = int(request.form['dia_vencimento'])
        cat_id = request.form['categoria_id'] if request.form['categoria_id'] != "" else None

        cursor.execute("""
            INSERT INTO agendamentos (descricao, valor, dia_vencimento, categoria_id)
            VALUES (%s, %s, %s, %s)
        """, (descricao, valor, dia, cat_id))
        conexao.commit()
        flash('Conta recorrente agendada com sucesso!', 'success')
        return redirect(url_for('agendamentos'))

    cursor.execute("""
        SELECT a.*, c.nome as categoria 
        FROM agendamentos a 
        LEFT JOIN categorias c ON a.categoria_id = c.id
        ORDER BY a.dia_vencimento ASC
    """)
    lista_agendamentos = cursor.fetchall()

    cursor.execute(
        "SELECT id, nome FROM categorias WHERE tipo IN ('despesa_fixa', 'despesa_variavel')")
    categorias = cursor.fetchall()

    cursor.close()
    conexao.close()
    return render_template('agendamentos.html', agendamentos=lista_agendamentos, categorias=categorias)


@app.route('/agendamentos/deletar/<int:id>', methods=['POST'])
def deletar_agendamento(id):
    conexao = obter_conexao()
    cursor = conexao.cursor()

    try:
        cursor.execute("DELETE FROM agendamentos WHERE id = %s", (id,))
        conexao.commit()
        flash('Agendamento removido com sucesso!', 'success')
    except Exception as e:
        conexao.rollback()
        flash(f'Erro ao remover: {e}', 'danger')
    finally:
        cursor.close()
        conexao.close()

    return redirect(url_for('agendamentos'))


@app.route('/agendamento/<int:id>/pagar', methods=['POST'])
def marcar_agendamento_pago(id):
    conexao = obter_conexao()
    cursor = conexao.cursor()

    try:
        cursor.execute("UPDATE agendamentos SET status = 'pago' WHERE id = %s", (id,))
        conexao.commit()
        flash('Conta marcada como paga com sucesso!', 'success')
    except Exception as e:
        print(f"Erro ao marcar conta como paga: {e}")
        conexao.rollback()
        flash('Erro ao atualizar o status da conta.', 'danger')
    finally:
        cursor.close()
        conexao.close()
            
    return redirect(url_for('agendamentos'))

# ==========================================================================
# OPEN FINANCE - SINCRO_AUT_PLUGGY (NUBANK/BB SANDBOX)
# ==========================================================================


@app.route('/sincronizar-banco', methods=['POST'])
def sincronizar_banco():
    client_id = os.environ.get('PLUGGY_CLIENT_ID')
    client_secret = os.environ.get('PLUGGY_CLIENT_SECRET')
    item_id = '9ca83e6f-22af-4f3d-95d7-a076bbf8be6d'

    if not client_id or not client_secret:
        flash('Chaves da Pluggy não configuradas no seu arquivo .env!', 'danger')
        return redirect(url_for('dashboard'))

    try:
        # 1. Autenticação na API da Pluggy
        auth_response = requests.post(
            "https://api.pluggy.ai/auth",
            json={"clientId": client_id, "clientSecret": client_secret}
        )
        auth_response.raise_for_status()
        token = auth_response.json().get('apiKey')
        
        headers = {
            "X-API-KEY": token,
            "Content-Type": "application/json"
        }

        # 2. Busca a conta vinculada à conexão para extrair o accountId
        contas_response = requests.get(f"https://api.pluggy.ai/accounts?itemId={item_id}", headers=headers)
        contas_response.raise_for_status()
        contas_pluggy = contas_response.json().get('results', [])

        if not contas_pluggy:
            flash('Nenhuma conta ativa foi encontrada para esta conexão.', 'warning')
            return redirect(url_for('dashboard'))

        conta_id_pluggy = contas_pluggy[0]['id']

        # 3. Consome a rota v2 mais recente para buscar as transações reais
        transacoes_response = requests.get(f"https://api.pluggy.ai/v2/transactions?accountId={conta_id_pluggy}", headers=headers)
        transacoes_response.raise_for_status()
        transacoes_pluggy = transacoes_response.json().get('results', [])

        # 4. Injeta as informações de forma segura no Banco de Dados local
        conexao = obter_conexao()
        cursor = conexao.cursor()

        # Mecanismo de segurança: busca a primeira conta cadastrada no seu DB para evitar falha de FK
        cursor.execute("SELECT id FROM contas LIMIT 1")
        conta_local = cursor.fetchone()
        conta_id_local = conta_local['id'] if conta_local else None

        novas_transacoes_contador = 0

        for t in transacoes_pluggy:
            descricao = t['description']
            valor = float(t['amount'])
            data_api = t['date'][:10]  # Recorta para o formato YYYY-MM-DD

            # Evita Duplicados: Só faz o INSERT se a transação idêntica não existir no banco
            cursor.execute("""
                SELECT id FROM transacoes 
                WHERE descricao = %s AND valor = %s AND data = %s
            """, (descricao, valor, data_api))
            
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
            flash(f'Sincronização concluída! {novas_transacoes_contador} novas transações importadas automaticamente.', 'success')
        else:
            flash('Seu extrato já está totalmente atualizado com o banco.', 'info')

    except Exception as e:
        print(f"Erro crítico de sincronização: {e}")
        flash('Ocorreu uma falha ao tentar sincronizar os dados com a Pluggy.', 'danger')

    return redirect(url_for('dashboard'))


# ==========================================================================
# INICIALIZAÇÃO LOCAL DO SERVIDOR
# ==========================================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)