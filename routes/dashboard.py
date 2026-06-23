from flask import Blueprint, render_template, request
from datetime import datetime
from database import obter_conexao

# Criando o Blueprint do Dashboard
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    mes_atual = request.args.get('mes', type=int)
    ano_atual = request.args.get('ano', type=int)

    if not mes_atual or not ano_atual:
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year

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

    # 1. MATEMÁTICA AVANÇADA: Fatiando os saldos por categoria
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN tipo IN ('corrente', 'dinheiro') THEN saldo ELSE 0 END), 0) as saldo_disponivel,
            COALESCE(SUM(CASE WHEN tipo IN ('poupanca', 'investimento') THEN saldo ELSE 0 END), 0) as saldo_investido,
            COALESCE(SUM(CASE WHEN tipo = 'passivo' THEN saldo ELSE 0 END), 0) as faturas
        FROM contas
    """)
    patrimonio = cursor.fetchone()

    saldo_disponivel = float(
        patrimonio['saldo_disponivel']) if patrimonio else 0.0
    saldo_investido = float(
        patrimonio['saldo_investido']) if patrimonio else 0.0
    faturas = float(patrimonio['faturas']) if patrimonio else 0.0

    # O Patrimônio Líquido é a soma de tudo que é seu, menos o que você deve
    net_worth = (saldo_disponivel + saldo_investido) - abs(faturas)

    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN cat.tipo = 'receita' THEN t.valor ELSE 0 END), 0) as receitas,
            COALESCE(SUM(CASE WHEN cat.tipo = 'aporte' THEN ABS(t.valor) ELSE 0 END), 0) as aportes
        FROM transacoes t
        JOIN categorias cat ON t.categoria_id = cat.id
        WHERE EXTRACT(MONTH FROM t.data) = %s AND EXTRACT(YEAR FROM t.data) = %s AND t.conta_destino_id IS NULL
    """, (mes_atual, ano_atual))
    fluxo_mes = cursor.fetchone()
    receitas_mes = float(fluxo_mes['receitas']) if fluxo_mes else 0.0
    aportes_mes = float(fluxo_mes['aportes']) if fluxo_mes else 0.0

    taxa_aporte = round((aportes_mes / receitas_mes) *
                        100, 1) if receitas_mes > 0 else 0

    cursor.execute("""
        SELECT c.nome as categoria, o.limite, COALESCE(SUM(ABS(t.valor)), 0) as gasto_atual,
        CASE WHEN o.limite > 0 THEN ROUND((COALESCE(SUM(ABS(t.valor)), 0) / o.limite) * 100) ELSE 0 END as porcentagem
        FROM orcamentos o
        JOIN categorias c ON o.categoria_id = c.id
        LEFT JOIN transacoes t ON c.id = t.categoria_id AND EXTRACT(MONTH FROM t.data) = %s AND EXTRACT(YEAR FROM t.data) = %s AND t.conta_destino_id IS NULL
        GROUP BY c.nome, o.limite
    """, (mes_atual, ano_atual))
    orcamentos = cursor.fetchall()

    cursor.execute("""
        SELECT c.nome as categoria, COALESCE(SUM(ABS(t.valor)), 0) as total
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE c.tipo IN ('despesa_fixa', 'despesa_variavel', 'aporte') AND EXTRACT(MONTH FROM t.data) = %s AND EXTRACT(YEAR FROM t.data) = %s AND t.conta_destino_id IS NULL
        GROUP BY c.nome
        HAVING COALESCE(SUM(ABS(t.valor)), 0) > 0
    """, (mes_atual, ano_atual))
    dados_grafico = cursor.fetchall()

    labels_grafico = [row['categoria'] for row in dados_grafico]
    valores_grafico = [float(row['total']) for row in dados_grafico]

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
                           saldo=net_worth, 
                           saldo_disponivel=saldo_disponivel, 
                           saldo_investido=saldo_investido, 
                           faturas=faturas,
                           taxa_aporte=taxa_aporte, 
                           orcamentos=orcamentos, 
                           transacoes=transacoes_mes,
                           labels_grafico=labels_grafico, 
                           valores_grafico=valores_grafico,
                           nome_mes_exibido=nome_mes_exibido, 
                           mes_ant=mes_anterior, 
                           ano_ant=ano_anterior,
                           mes_prox=mes_proximo, 
                           ano_prox=ano_proximo)
