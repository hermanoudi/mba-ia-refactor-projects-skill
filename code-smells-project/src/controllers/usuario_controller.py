from src.models import usuario_model


def listar():
    return usuario_model.get_all()


def buscar(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if not usuario:
        raise ValueError("Usuário não encontrado")
    return usuario


def criar(dados):
    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip()
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValueError("Nome, email e senha são obrigatórios")

    return usuario_model.create(nome, email, senha)


def autenticar(dados):
    email = dados.get("email", "").strip()
    senha = dados.get("senha", "")

    if not email or not senha:
        raise ValueError("Email e senha são obrigatórios")

    usuario = usuario_model.verify_password(email, senha)
    if not usuario:
        raise PermissionError("Email ou senha inválidos")
    return usuario
