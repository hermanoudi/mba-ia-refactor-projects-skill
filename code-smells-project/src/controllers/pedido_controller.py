from src.models import pedido_model, produto_model
from src.config.settings import ORDER_STATUSES
from src.services.notification_service import notification_service


def listar_por_usuario(usuario_id):
    return pedido_model.get_by_usuario(usuario_id)


def listar_todos():
    return pedido_model.get_all()


def criar(dados):
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValueError("usuario_id é obrigatório")
    if not itens:
        raise ValueError("Pedido deve ter pelo menos 1 item")

    itens_com_preco = []
    total = 0.0

    for item in itens:
        produto = produto_model.get_by_id(item["produto_id"])
        if produto is None:
            raise ValueError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")

        preco = produto["preco"]
        total += preco * item["quantidade"]
        itens_com_preco.append({**item, "preco_unitario": preco})

    pedido_id = pedido_model.create(usuario_id, itens_com_preco, total)
    notification_service.order_created(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": round(total, 2)}


def atualizar_status(pedido_id, dados):
    novo_status = dados.get("status", "")
    if novo_status not in ORDER_STATUSES:
        raise ValueError(f"Status inválido. Válidos: {ORDER_STATUSES}")

    pedido_model.update_status(pedido_id, novo_status)
    notification_service.order_status_changed(pedido_id, novo_status)
