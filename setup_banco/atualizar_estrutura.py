import os
from database import obter_conexao
from dotenv import load_dotenv

# Carrega a URL do banco direto do .env protegido
load_dotenv()


def atualizar_banco():
    print("Conectando ao PostgreSQL no Render para atualizar a estrutura...")
    conexao = obter_conexao()
    cursor = conexao.cursor()

    try:
        # 1. Adiciona a coluna para saber para onde foi o dinheiro na transferência
        print("Adicionando coluna 'conta_destino_id' na tabela de transações...")
        cursor.execute("""
            ALTER TABLE transacoes 
            ADD COLUMN IF NOT EXISTS conta_destino_id INTEGER REFERENCES contas(id) ON DELETE SET NULL;
        """)

        # 2. Cria a tabela para gerenciar as contas fixas e assinaturas
        print("Criando tabela de agendamentos (Contas Fixas)...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos (
                id SERIAL PRIMARY KEY,
                descricao VARCHAR(150) NOT NULL,
                valor NUMERIC(10, 2) NOT NULL,
                dia_vencimento INTEGER NOT NULL CHECK (dia_vencimento >= 1 AND dia_vencimento <= 31),
                categoria_id INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
                status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'pago'))
            );
        """)

        conexao.commit()
        print("\n🔥 Sucesso total! Estrutura do banco de dados atualizada no Render.")

    except Exception as e:
        conexao.rollback()
        print(f"\n❌ Erro ao atualizar a estrutura: {e}")
    finally:
        cursor.close()
        conexao.close()


if __name__ == '__main__':
    atualizar_banco()
