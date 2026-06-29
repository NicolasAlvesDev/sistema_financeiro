import os
from flask import Flask
from dotenv import load_dotenv

# Importando os nossos novos módulos (Blueprints)
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.pluggy import pluggy_bp
from routes.transacoes import transacoes_bp
from routes.contas import contas_bp
from routes.faturas import faturas_bp

# ==========================================================================
# CONFIGURAÇÃO E AMBIENTE SEGURO
# ==========================================================================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get(
    'FLASK_SECRET_KEY', 'chave_padrao_super_segura')

# ==========================================================================
# REGISTRANDO OS MÓDULOS (O Maestro chamando os instrumentos)
# ==========================================================================
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(pluggy_bp)
app.register_blueprint(transacoes_bp)
app.register_blueprint(contas_bp)
app.register_blueprint(faturas_bp)

# ==========================================================================
# INICIALIZAÇÃO LOCAL DO SERVIDOR
# ==========================================================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
