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
    nome = request.form['nome']
    tipo = request.form['tipo']
    saldo_inicial = float(request.form['saldo_inicial'] or 0.0)

    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("""
        INSERT INTO contas (nome, tipo, saldo_inicial, saldo)
        VALUES (%s, %s, %s, %s)
    """, (nome, tipo, saldo_inicial, saldo_inicial))
    conexao.commit()
    cursor.close()
    conexao.close()

    flash(f'Conta {nome} criada com sucesso!', 'success')
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
        # Trava de segurança do SQL (Não deixa excluir conta se tiver transação amarrada nela)
        flash('Não é possível excluir esta conta porque existem transações vinculadas a ela.', 'danger')
    finally:
        cursor.close()
        conexao.close()
    return redirect(url_for('contas.listar'))


@contas_bp.route('/editar/<int:id>', methods=['POST'])
def editar(id):
    nome = request.form['nome']
    tipo = request.form['tipo']
    saldo = float(request.form['saldo'])

    conexao = obter_conexao()
    cursor = conexao.cursor()
    try:
        cursor.execute("""
            UPDATE contas 
            SET nome = %s, tipo = %s, saldo = %s 
            WHERE id = %s
        """, (nome, tipo, saldo, id))
        conexao.commit()
        flash('Conta atualizada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar conta: {e}', 'danger')
    finally:
        cursor.close()
        conexao.close()

    return redirect(url_for('contas.listar'))
