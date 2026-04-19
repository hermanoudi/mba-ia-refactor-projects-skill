from flask import Blueprint, jsonify, request
from src.controllers import produto_controller

bp = Blueprint("produtos", __name__, url_prefix="/produtos")


@bp.get("/")
def listar():
    return jsonify({"dados": produto_controller.listar(), "sucesso": True})


@bp.get("/busca")
def buscar():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min", type=float)
    preco_max = request.args.get("preco_max", type=float)
    resultados = produto_controller.buscar_por_filtros(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True})


@bp.get("/<int:produto_id>")
def buscar_por_id(produto_id):
    return jsonify({"dados": produto_controller.buscar(produto_id), "sucesso": True})


@bp.post("/")
def criar():
    dados = request.get_json(silent=True) or {}
    produto_id = produto_controller.criar(dados)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@bp.put("/<int:produto_id>")
def atualizar(produto_id):
    dados = request.get_json(silent=True) or {}
    produto_controller.atualizar(produto_id, dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"})


@bp.delete("/<int:produto_id>")
def deletar(produto_id):
    produto_controller.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"})
