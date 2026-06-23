from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import obter_conexao

# Criando o Blueprint (O "mini-app" de autenticação)
auth_bp = Blueprint('auth', __name__)

# O Flask chama isso antes de qualquer rota desse ou de outros blueprints


@auth_bp.before_app_request
def proteger_rotas():
    rotas_publicas = ['auth.login', 'static']
    if request.endpoint not in rotas_publicas and 'usuario_id' not in session:
        return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
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
            # Aponta para o novo módulo dashboard
            return redirect(url_for('dashboard.index'))
        else:
            flash('Usuário ou senha incorretos!', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
