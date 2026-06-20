from database import obter_conexao


def migrar_categorias():
    print("Conectando ao banco para atualizar as categorias...")
    conexao = obter_conexao()
    cursor = conexao.cursor()

    # 1. Limpa categorias antigas (Cuidado: se houver transações atreladas, mude para UPDATE ou trate chaves)
    try:
        cursor.execute("TRUNCATE TABLE categorias RESTART IDENTITY CASCADE;")
    except Exception:
        # Caso o banco seja MySQL ou não suporte CASCADE dessa forma:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE categorias;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 2. Nova lista mapeada com os tipos corretos para não quebrar a lógica do app.py
    novas_categorias = [
        # --- RECEITAS (Entradas) ---
        ('Salário', 'receita'),
        ('Transferência Recebida', 'receita'),
        ('Pix Recebido', 'receita'),
        ('Depósito', 'receita'),
        ('Reembolso', 'receita'),
        ('Investimentos / Resgates', 'receita'),
        ('Rendimentos', 'receita'),
        ('Cashback', 'receita'),
        ('Venda de Produtos', 'receita'),
        ('Venda de Serviços', 'receita'),
        ('Empréstimo Recebido', 'receita'),
        ('Renda Extra / Entregas', 'receita'),
        ('Outros Ganhos', 'receita'),

        # --- DESPESAS (Saídas) ---
        ('Alimentação', 'despesa_variavel'),
        ('Transporte', 'despesa_variavel'),
        ('Manutenção Veicular', 'despesa_variavel'),
        ('Moradia', 'despesa_fixa'),
        ('Contas Fixas', 'despesa_fixa'),
        ('Saúde', 'despesa_variavel'),
        ('Educação', 'despesa_fixa'),
        ('Lazer', 'despesa_variavel'),
        ('Assinaturas e Serviços', 'despesa_fixa'),
        ('Compras Geral', 'despesa_variavel'),
        ('Vestuário', 'despesa_variavel'),
        ('Impostos e Taxas', 'despesa_fixa'),
        # Mapeado como aporte para a Taxa de Aporte
        ('Investimentos / Aportes', 'aporte'),
        ('Seguros', 'despesa_fixa'),
        ('Pix Enviado', 'despesa_variavel'),
        ('Transferência Enviada', 'despesa_variavel'),
        ('Saque', 'despesa_variavel'),
        ('Doações', 'despesa_variavel'),
        ('Outros Gastos', 'despesa_variavel'),

        # --- BANCÁRIAS / AJUSTES ---
        ('Tarifas Bancárias', 'despesa_variavel'),
        ('Juros e Multas', 'despesa_variavel'),
        ('Empréstimos e Financiamentos', 'despesa_fixa'),
        ('Estorno / Ajuste', 'receita')
    ]

    # 3. Inserindo os dados no banco
    cursor.executemany(
        "INSERT INTO categorias (nome, tipo) VALUES (%s, %s);",
        novas_categorias
    )

    conexao.commit()
    cursor.close()
    conexao.close()
    print("Sucesso total! Todas as novas categorias foram cadastradas no banco de dados.")


if __name__ == '__main__':
    migrar_categorias()
