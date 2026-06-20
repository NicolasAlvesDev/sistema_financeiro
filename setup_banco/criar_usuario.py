import getpass
from werkzeug.security import generate_password_hash
from database import obter_conexao


def criar_usuario_admin():
    print("=== Módulo de Segurança: Atualização de Credenciais ===\n")

    # 1. Solicita o usuário de forma interativa, evitando hardcoding
    usuario_desejado = input(
        "Digite o nome de usuário que deseja atualizar: ").strip()

    if not usuario_desejado:
        print("❌ Erro: O nome de usuário não pode estar vazio.")
        return

    # 2. getpass esconde a digitação (o cursor não se move, é normal!)
    senha_desejada = getpass.getpass("Digite a nova senha (invisível): ")
    senha_confirmacao = getpass.getpass("Confirme a nova senha: ")

    # 3. Validação básica de segurança
    if senha_desejada != senha_confirmacao:
        print("❌ Erro: As senhas não coincidem. Operação cancelada.")
        return

    if len(senha_desejada) < 6:
        print("❌ Erro: A senha é muito curta. Use pelo menos 6 caracteres.")
        return

    print("\nConectando ao banco de dados...")
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()

        # Gera o hash seguro usando o Werkzeug
        senha_criptografada = generate_password_hash(senha_desejada)

        # 4. Verifica se o usuário realmente existe antes de tentar atualizar
        cursor.execute(
            "SELECT id FROM usuarios WHERE usuario = %s", (usuario_desejado,))
        usuario_existe = cursor.fetchone()

        if not usuario_existe:
            print(
                f"⚠️ Aviso: O usuário '{usuario_desejado}' não foi encontrado no banco de dados.")
            print(
                "Se esta for a primeira configuração, você precisará fazer um INSERT em vez de UPDATE.")
            return

        # 5. Executa a atualização com a senha já protegida em hash
        cursor.execute(
            "UPDATE usuarios SET senha_hash = %s WHERE usuario = %s",
            (senha_criptografada, usuario_desejado)
        )

        conexao.commit()
        print(
            f"✅ Sucesso! A nova senha do usuário '{usuario_desejado}' foi atualizada e está protegida no servidor.")

    except Exception as e:
        print(f"❌ Erro crítico ao conectar ou atualizar: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexao' in locals():
            conexao.close()


if __name__ == "__main__":
    criar_usuario_admin()
