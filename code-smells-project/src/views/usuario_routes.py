from flask import Blueprint, jsonify, request
from src.controllers import usuario_controller

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
def listar():
    return jsonify({"dados": usuario_controller.listar(), "sucesso": True})


@bp.get("/usuarios/<int:usuario_id>")
def buscar(usuario_id):
    return jsonify({"dados": usuario_controller.buscar(usuario_id), "sucesso": True})


@bp.post("/usuarios")
def criar():
    dados = request.get_json(silent=True) or {}
    usuario_id = usuario_controller.criar(dados)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


@bp.post("/login")
def login():
    dados = request.get_json(silent=True) or {}
    usuario = usuario_controller.autenticar(dados)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"})
