from database import obter_conexao


def migrar_contas():
    print("Conectando ao banco PostgreSQL no Render para atualizar as contas...")
    conexao = obter_conexao()
    cursor = conexao.cursor()

    try:
        # No PostgreSQL, usamos CASCADE direto no TRUNCATE para limpar tabelas relacionadas de forma limpa
        print("Limpando dados antigos das contas...")
        cursor.execute("TRUNCATE TABLE contas RESTART IDENTITY CASCADE;")

        novas_contas = [
            ('Carteira / Dinheiro', 'corrente', 0.00),
            ('Conta Corrente - Nubank', 'corrente', 0.00),
            ('Conta Corrente - Banco do Brasil', 'corrente', 0.00),
            ('Poupança / Cofrinho', 'poupanca', 0.00),
            ('Investimentos Corretora', 'investimento', 0.00),
            ('Fatura Cartão - Nubank', 'passivo', 0.00),
            ('Fatura Cartão - BB', 'passivo', 0.00)
        ]

        print("Inserindo novas contas...")
        cursor.executemany(
            "INSERT INTO contas (nome, tipo, saldo_inicial) VALUES (%s, %s, %s);",
            novas_contas
        )

        conexao.commit()
        print(
            "Sucesso total! Suas novas contas foram registradas com sucesso no PostgreSQL.")

    except Exception as e:
        conexao.rollback()
        print(f"Erro ao migrar contas: {e}")

    finally:
        cursor.close()
        conexao.close()


if __name__ == '__main__':
    migrar_contas()
