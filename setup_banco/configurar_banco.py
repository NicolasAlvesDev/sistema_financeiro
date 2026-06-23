from database import obter_conexao


def criar_estrutura_avancada():
    print("Atualizando banco com módulos avançados e suporte Open Finance...")
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()

        # Apaga garantindo a ordem correta das dependências (PostgreSQL Dialect)
        cursor.execute("""
        DROP TABLE IF EXISTS orcamentos CASCADE;
        DROP TABLE IF EXISTS transacoes CASCADE;
        DROP TABLE IF EXISTS contas CASCADE;
        DROP TABLE IF EXISTS categorias CASCADE;
        """)

        # 1. CATEGORIAS (Adicionado suporte a mais tipos se necessário)
        cursor.execute("""
        CREATE TABLE categorias (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(50) NOT NULL,
            tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('receita', 'despesa_fixa', 'despesa_variavel', 'aporte', 'investimento'))
        );
        """)

        # 2. CONTAS (Adicionado a coluna 'saldo' para o saldo real dinâmico da API e 'pluggy_account_id')
        cursor.execute("""
        CREATE TABLE contas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(50) NOT NULL,
            tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('corrente', 'poupanca', 'investimento', 'dinheiro', 'passivo')),
            saldo_inicial DECIMAL(10,2) DEFAULT 0.00,
            saldo DECIMAL(10,2) DEFAULT 0.00,
            pluggy_account_id VARCHAR(100) NULL
        );
        """)

        # 3. TRANSAÇÕES (Adicionado as colunas ausentes: conta_destino_id e as FKs corretas)
        cursor.execute("""
        CREATE TABLE transacoes (
            id SERIAL PRIMARY KEY,
            descricao VARCHAR(100) NOT NULL,
            valor DECIMAL(10,2) NOT NULL, 
            data DATE NOT NULL,
            categoria_id INT REFERENCES categorias(id) ON DELETE SET NULL,
            conta_id INT REFERENCES contas(id) ON DELETE CASCADE,
            conta_destino_id INT REFERENCES contas(id) ON DELETE SET NULL
        );
        """)

        # 4. USUÁRIOS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(50) NOT NULL UNIQUE,
            senha_hash VARCHAR(255) NOT NULL
        );
        """)

        # 5. ORÇAMENTOS
        cursor.execute("""
        CREATE TABLE orcamentos (
            id SERIAL PRIMARY KEY,
            categoria_id INT UNIQUE REFERENCES categorias(id) ON DELETE CASCADE,
            limite DECIMAL(10,2) NOT NULL
        );
        """)

        # Mapeamento inicial da massa de dados padrão
        cursor.execute("""
        INSERT INTO contas (nome, tipo, saldo_inicial, saldo) VALUES 
        ('Nubank', 'corrente', 0.00, 0.00),
        ('Reserva de Emergência', 'poupanca', 0.00, 0.00),
        ('Corretora Ações', 'investimento', 0.00, 0.00),
        ('Fatura Cartão', 'passivo', 0.00, 0.00);

        INSERT INTO categorias (id, nome, tipo) VALUES 
        (1, 'Salário', 'receita'),
        (2, 'Alimentação', 'despesa_variavel'),
        (3, 'Aluguel/Moradia', 'despesa_fixa'),
        (4, 'Aporte Futuro', 'aporte')
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO orcamentos (categoria_id, limite) VALUES (2, 600.00) ON CONFLICT DO NOTHING;
        """)

        conexao.commit()
        print("🚀 Tudo pronto! Banco reinstalado na nuvem com suporte a saldos e chaves estrangeiras!")
    except Exception as e:
        print(f"Erro ao atualizar banco: {e}")
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    criar_estrutura_avancada()
