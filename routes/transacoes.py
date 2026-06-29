from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import obter_conexao
from datetime import date

transacoes_bp = Blueprint('transacoes', __name__)


@transacoes_bp.route('/extrato')
def extrato():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    filtro_tipo = request.args.get('tipo', '')
    filtro_conta = request.args.get('conta_id', '')

    query = """
        SELECT t.id, t.descricao, t.valor, t.data, c.nome as categoria, co.nome as conta, co_dest.nome as conta_destino, t.conta_destino_id
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
        parametros.extend([filtro_conta, filtro_conta])

    query += " ORDER BY t.data DESC"

    cursor.execute(query, tuple(parametros))
    transacoes_filtradas = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM contas")
    contas = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('extrato.html', transacoes=transacoes_filtradas, contas=contas, filtro_tipo=filtro_tipo, filtro_conta=filtro_conta)


@transacoes_bp.route('/nova-transacao', methods=['GET', 'POST'])
def nova_transacao():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        tipo_mov = request.form['tipo_movimentacao']

        # Garante que despesa e transferência entrem com sinal negativo no extrato
        if tipo_mov in ['despesa', 'transferencia']:
            valor = -abs(valor)
        else:
            # Garante que receita seja estritamente positiva
            valor = abs(valor)

        data = request.form['data']
        categoria_id = request.form['categoria_id'] if request.form['categoria_id'] != "" else None
        conta_id = request.form['conta_id'] if request.form['conta_id'] != "" else None
        conta_destino_id = request.form['conta_destino_id'] if (
            tipo_mov == 'transferencia' and request.form['conta_destino_id'] != "") else None

        try:
            # 1. Insere o registro no extrato de transações
            cursor.execute("""
                INSERT INTO transacoes (descricao, valor, data, categoria_id, conta_id, conta_destino_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (descricao, valor, data, categoria_id, conta_id, conta_destino_id))

            # 2. ATUALIZAÇÃO AUTOMÁTICA DE SALDOS NAS CONTAS
            if tipo_mov == 'transferencia' and conta_destino_id:
                # Se for transferência: tira da origem (valor é negativo) e põe no destino (sinal invertido)
                cursor.execute(
                    "UPDATE contas SET saldo = saldo + %s WHERE id = %s", (valor, conta_id))
                cursor.execute(
                    "UPDATE contas SET saldo = saldo + %s WHERE id = %s", (abs(valor), conta_destino_id))
            else:
                # Se for receita ou despesa comum: altera direto a conta vinculada
                if conta_id:
                    cursor.execute(
                        "UPDATE contas SET saldo = saldo + %s WHERE id = %s", (valor, conta_id))

            conexao.commit()
            flash('Transação registrada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao registrar transação: {e}', 'danger')
        finally:
            cursor.close()
            conexao.close()

        return redirect(url_for('dashboard.index'))

    cursor.execute("SELECT id, nome FROM categorias")
    categorias = cursor.fetchall()
    cursor.execute("SELECT id, nome FROM contas")
    contas = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('nova_transacao.html', categories=categorias, categorias=categorias, contas=contas)


@transacoes_bp.route('/agendamentos', methods=['GET', 'POST'])
def agendamentos():
    conexao = obter_conexao()
    cursor = conexao.cursor()

    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        dia = int(request.form['dia_vencimento'])
        cat_id = request.form['categoria_id'] if request.form['categoria_id'] != "" else None

        cursor.execute("INSERT INTO agendamentos (descricao, valor, dia_vencimento, categoria_id) VALUES (%s, %s, %s, %s)",
                       (descricao, valor, dia, cat_id))
        conexao.commit()
        flash('Conta agendada!', 'success')
        return redirect(url_for('transacoes.agendamentos'))

    cursor.execute(
        "SELECT a.*, c.nome as categoria FROM agendamentos a LEFT JOIN categorias c ON a.categoria_id = c.id ORDER BY a.dia_vencimento ASC")
    lista_agendamentos = cursor.fetchall()

    cursor.execute(
        "SELECT id, nome FROM categorias WHERE tipo IN ('despesa_fixa', 'despesa_variavel')")
    categorias = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('agendamentos.html', agendamentos=lista_agendamentos, categorias=categorias)


@transacoes_bp.route('/agendamentos/deletar/<int:id>', methods=['POST'])
def deletar_agendamento(id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM agendamentos WHERE id = %s", (id,))
    conexao.commit()
    cursor.close()
    conexao.close()
    flash('Agendamento removido!', 'success')
    return redirect(url_for('transacoes.agendamentos'))


@transacoes_bp.route('/agendamento/<int:id>/pagar', methods=['POST'])
def marcar_agendamento_pago(id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute(
        "UPDATE agendamentos SET status = 'pago' WHERE id = %s", (id,))
    conexao.commit()
    cursor.close()
    conexao.close()
    flash('Conta paga!', 'success')
    return redirect(url_for('transacoes.agendamentos'))
