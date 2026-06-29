from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import obter_conexao

contas_bp = Blueprint('contas', __name__, url_prefix='/contas')


@contas_bp.route('/')
def listar():
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM contas ORDER BY tipo, nome")
    lista_contas = cursor.fetchall()
    cursor.close()
    conexao.close()
    return render_template('contas.html', contas=lista_contas)


@contas_bp.route('/nova', methods=['POST'])
def nova():
    try:
        nome = request.form.get('nome')
        tipo = request.form.get('tipo')

        saldo_str = request.form.get('saldo_inicial', '0').replace(',', '.')
        saldo_inicial = float(saldo_str) if saldo_str else 0.0

        limite_str = request.form.get('limite', '0').replace(',', '.')
        limite = float(limite_str) if limite_str else 0.0

        # Captura o dia de vencimento (padrão 10)
        dia_vencimento = int(request.form.get('dia_vencimento') or 10)

        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("""
            INSERT INTO contas (nome, tipo, saldo_inicial, saldo, limite, dia_vencimento)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome, tipo, saldo_inicial, saldo_inicial, limite, dia_vencimento))
        conexao.commit()
        flash(f'Conta {nome} criada com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao criar conta: {e}', 'danger')

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexao' in locals():
            conexao.close()

    return redirect(url_for('contas.listar'))


@contas_bp.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        cursor.execute("DELETE FROM contas WHERE id = %s", (id,))
        conexao.commit()
        flash('Conta removida com sucesso!', 'success')
    except Exception as e:
        flash('Não é possível excluir esta conta porque existem transações vinculadas a ela.', 'danger')
    finally:
        cursor.close()
        conexao.close()
    return redirect(url_for('contas.listar'))


@contas_bp.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    try:
        nome = request.form.get('nome')
        tipo = request.form.get('tipo')

        saldo_str = request.form.get('saldo', '0').replace(',', '.')
        saldo = float(saldo_str) if saldo_str else 0.0

        limite_str = request.form.get('limite', '0').replace(',', '.')
        limite = float(limite_str) if limite_str else 0.0

        # Captura o dia de vencimento na edição
        dia_vencimento = int(request.form.get('dia_vencimento') or 10)

        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("""
            UPDATE contas 
            SET nome = %s, tipo = %s, saldo = %s, limite = %s, dia_vencimento = %s 
            WHERE id = %s
        """, (nome, tipo, saldo, limite, dia_vencimento, id))
        conexao.commit()
        flash('Conta atualizada com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao atualizar conta: {e}', 'danger')

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexao' in locals():
            conexao.close()

    return redirect(url_for('contas.listar'))
