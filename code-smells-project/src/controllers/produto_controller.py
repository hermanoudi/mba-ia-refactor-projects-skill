from src.models import produto_model
from src.config.settings import VALID_CATEGORIES


def listar():
    return produto_model.get_all()


def buscar(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        raise ValueError("Produto não encontrado")
    return produto


def buscar_por_filtros(termo="", categoria=None, preco_min=None, preco_max=None):
    return produto_model.search(termo, categoria, preco_min, preco_max)


def criar(dados):
    _validar(dados, require_all=True)
    return produto_model.create(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )


def atualizar(produto_id, dados):
    if not produto_model.get_by_id(produto_id):
        raise ValueError("Produto não encontrado")
    _validar(dados, require_all=True)
    produto_model.update(
        produto_id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )


def deletar(produto_id):
    if not produto_model.get_by_id(produto_id):
        raise ValueError("Produto não encontrado")
    produto_model.delete(produto_id)


def _validar(dados, require_all=False):
    if require_all:
        for campo in ("nome", "preco", "estoque"):
            if campo not in dados:
                raise ValueError(f"{campo.capitalize()} é obrigatório")

    if "nome" in dados:
        if len(dados["nome"]) < 2:
            raise ValueError("Nome muito curto")
        if len(dados["nome"]) > 200:
            raise ValueError("Nome muito longo")

    if "preco" in dados and dados["preco"] < 0:
        raise ValueError("Preço não pode ser negativo")

    if "estoque" in dados and dados["estoque"] < 0:
        raise ValueError("Estoque não pode ser negativo")

    categoria = dados.get("categoria", "geral")
    if categoria not in VALID_CATEGORIES:
        raise ValueError(f"Categoria inválida. Válidas: {VALID_CATEGORIES}")
