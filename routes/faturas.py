from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import obter_conexao
from datetime import datetime, date, timedelta

faturas_bp = Blueprint('faturas', __name__, url_prefix='/faturas')


def calcular_vencimento_util(dia_configurado, mes, ano):
    try:
        data_vencimento = date(ano, mes, dia_configurado)
    except ValueError:
        proximo_mes = date(ano, mes, 1) + timedelta(days=32)
        data_vencimento = date(
            proximo_mes.year, proximo_mes.month, 1) - timedelta(days=1)

    if data_vencimento.weekday() == 5:    # Sábado
        data_vencimento += timedelta(days=2)
    elif data_vencimento.weekday() == 6:  # Domingo
        data_vencimento += timedelta(days=1)

    return data_vencimento.strftime('%d/%m/%Y')


@faturas_bp.route('/')
def index():
    hoje = datetime.today()
    
    # 1. MÁQUINA DO TEMPO: Pega o mês/ano da URL, ou usa o atual se não tiver nada
    mes_atual = int(request.args.get('mes', hoje.month))
    ano_atual = int(request.args.get('ano', hoje.year))

    # Calcula mês anterior e próximo para os botões de navegação
    mes_anterior = mes_atual - 1
    ano_anterior = ano_atual
    if mes_anterior < 1:
        mes_anterior = 12
        ano_anterior -= 1

    mes_proximo = mes_atual + 1
    ano_proximo = ano_atual
    if mes_proximo > 12:
        mes_proximo = 1
        ano_proximo += 1

    meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 
                7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    nome_mes_exibido = f"{meses_pt[mes_atual]} de {ano_atual}".upper()

    conexao = obter_conexao()
    cursor = conexao.cursor()

    cursor.execute("SELECT * FROM contas WHERE tipo = 'passivo'")
    cartoes = cursor.fetchall()

    cursor.execute("SELECT * FROM contas WHERE tipo != 'passivo' ORDER BY nome")
    contas_origem = cursor.fetchall()

    cursor.execute("""
        SELECT t.*, c.nome as categoria_nome
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN contas ct_origem ON t.conta_id = ct_origem.id
        LEFT JOIN contas ct_destino ON t.conta_destino_id = ct_destino.id
        WHERE (ct_origem.tipo = 'passivo' OR ct_destino.tipo = 'passivo')
          AND EXTRACT(MONTH FROM t.data) = %s 
          AND EXTRACT(YEAR FROM t.data) = %s
        ORDER BY t.data DESC
    """, (mes_atual, ano_atual))
    transacoes_cartao = cursor.fetchall()

    # Projeção dos próximos 3 meses a partir do mês visualizado
    meses_nomes_curtos = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 
                          7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    
    projecoes = []
    for i in range(1, 4):
        m = mes_atual + i
        y = ano_atual
        if m > 12:  
            m -= 12
            y += 1
        
        cursor.execute("""
            SELECT ABS(COALESCE(SUM(t.valor), 0)) as total
            FROM transacoes t
            JOIN contas ct ON t.conta_id = ct.id
            WHERE ct.tipo = 'passivo' 
              AND EXTRACT(MONTH FROM t.data) = %s 
              AND EXTRACT(YEAR FROM t.data) = %s
        """, (m, y))
        
        resultado = cursor.fetchone()
        
        if isinstance(resultado, dict) or hasattr(resultado, 'keys'):
            total_mes = float(resultado.get('total') or 0.0)
        elif resultado:
            total_mes = float(resultado[0] if resultado[0] else 0.0)
        else:
            total_mes = 0.0
            
        projecoes.append({
            'mes_num': m,
            'ano_num': y,
            'rotulo': f"{meses_nomes_curtos[m]} {y}",
            'total': total_mes
        })

    cursor.close()
    conexao.close()

    gasto_atual = sum(abs(float(c.get('saldo') or 0.0)) for c in cartoes)
    limite_total = sum(float(c.get('limite') or 0.0) for c in cartoes)
    
    dia_configurado = 10
    if cartoes:
        dia_configurado = int(cartoes[0].get('dia_vencimento') or 10)
    
    data_vencimento_real = calcular_vencimento_util(dia_configurado, mes_atual, ano_atual)

    if limite_total == 0:
        limite_total = 1.0 
        
    disponivel = limite_total - gasto_atual
    porcentagem_uso = (gasto_atual / limite_total) * 100

    return render_template('faturas.html', 
                           cartoes=cartoes, 
                           contas_origem=contas_origem, 
                           transacoes=transacoes_cartao,
                           gasto_atual=gasto_atual,
                           limite_total=limite_total,
                           disponivel=disponivel,
                           porcentagem_uso=porcentagem_uso,
                           projecoes=projecoes,
                           data_vencimento=data_vencimento_real,
                           nome_mes_exibido=nome_mes_exibido,
                           mes_ant=mes_anterior, ano_ant=ano_anterior,
                           mes_prox=mes_proximo, ano_prox=ano_proximo)


# -------------------------------------------------------------
# NOVA ROTA: PROCESSAR PAGAMENTO DA FATURA
# -------------------------------------------------------------
@faturas_bp.route('/pagar', methods=['POST'])
def pagar():
    try:
        conta_origem_id = int(request.form['conta_origem_id'])
        conta_cartao_id = int(request.form['conta_cartao_id'])

        valor_str = request.form['valor_pagamento'].replace(',', '.')
        valor = float(valor_str) if valor_str else 0.0

        if valor <= 0:
            flash("O valor do pagamento deve ser maior que zero.", "warning")
            return redirect(url_for('faturas.index'))

        conexao = obter_conexao()
        cursor = conexao.cursor()

        # 1. Retira o dinheiro da conta corrente de origem
        cursor.execute(
            "UPDATE contas SET saldo = saldo - %s WHERE id = %s", (valor, conta_origem_id))

        # 2. Amortiza o saldo devedor do cartão (soma o valor positivo ao saldo negativo)
        cursor.execute(
            "UPDATE contas SET saldo = saldo + %s WHERE id = %s", (valor, conta_cartao_id))

        # 3. Regista no histórico de transações como uma transferência interna
        cursor.execute("""
            INSERT INTO transacoes (descricao, valor, data, conta_id, conta_destino_id)
            VALUES (%s, %s, %s, %s, %s)
        """, ('Pagamento Fatura Cartão', -valor, date.today(), conta_origem_id, conta_cartao_id))

        conexao.commit()
        flash("Pagamento de fatura registado com sucesso!", "success")

    except Exception as e:
        flash(f"Erro ao processar pagamento: {e}", "danger")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexao' in locals():
            conexao.close()

    return redirect(url_for('faturas.index'))


@faturas_bp.route('/ajustar_projecao', methods=['POST'])
def ajustar_projecao():
    try:
        mes = int(request.form['mes'])
        ano = int(request.form['ano'])

        valor_str = request.form['valor_desejado'].replace(',', '.')
        valor_desejado = float(valor_str) if valor_str else 0.0

        conexao = obter_conexao()
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM contas WHERE tipo = 'passivo' LIMIT 1")
        conta_passiva = cursor.fetchone()

        if not conta_passiva:
            flash("Nenhum cartão cadastrado para ajustar.", "warning")
            return redirect(url_for('faturas.index'))

        conta_id = conta_passiva[0] if isinstance(
            conta_passiva, tuple) else conta_passiva['id']

        cursor.execute("""
            SELECT ABS(COALESCE(SUM(t.valor), 0)) as total
            FROM transacoes t
            WHERE t.conta_id = %s 
              AND EXTRACT(MONTH FROM t.data) = %s 
              AND EXTRACT(YEAR FROM t.data) = %s
        """, (conta_id, mes, ano))

        resultado = cursor.fetchone()

        if isinstance(resultado, dict) or hasattr(resultado, 'keys'):
            soma_atual = float(resultado.get('total') or 0.0)
        elif resultado:
            soma_atual = float(resultado[0] if resultado[0] else 0.0)
        else:
            soma_atual = 0.0

        diferenca = valor_desejado - soma_atual

        if diferenca != 0:
            data_ajuste = f"{ano}-{mes:02d}-01"
            valor_inserir = -diferenca

            cursor.execute("""
                INSERT INTO transacoes (descricao, valor, data, conta_id)
                VALUES ('Ajuste Manual de Previsão', %s, %s, %s)
            """, (valor_inserir, data_ajuste, conta_id))
            conexao.commit()
            flash('Previsão ajustada com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao ajustar previsão: {e}', 'danger')
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexao' in locals():
            conexao.close()

    return redirect(url_for('faturas.index'))
