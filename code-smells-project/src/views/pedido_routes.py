from flask import Blueprint, jsonify, request
from src.controllers import pedido_controller, relatorio_controller

bp = Blueprint("pedidos", __name__)


@bp.post("/pedidos")
def criar():
    dados = request.get_json(silent=True) or {}
    resultado = pedido_controller.criar(dados)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@bp.get("/pedidos")
def listar_todos():
    return jsonify({"dados": pedido_controller.listar_todos(), "sucesso": True})


@bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_por_usuario(usuario_id):
    return jsonify({"dados": pedido_controller.listar_por_usuario(usuario_id), "sucesso": True})


@bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status(pedido_id):
    dados = request.get_json(silent=True) or {}
    pedido_controller.atualizar_status(pedido_id, dados)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"})


@bp.get("/relatorios/vendas")
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.vendas(), "sucesso": True})
