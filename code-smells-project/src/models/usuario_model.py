from werkzeug.security import generate_password_hash, check_password_hash
from src.config.database import get_db


def get_all():
    cursor = get_db().cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [dict(row) for row in cursor.fetchall()]


def get_by_id(usuario_id):
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
        (usuario_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def get_by_email(email):
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def create(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    db.commit()
    return cursor.lastrowid


def verify_password(email, senha):
    user = get_by_email(email)
    if user and check_password_hash(user["senha"], senha):
        return {"id": user["id"], "nome": user["nome"], "email": user["email"], "tipo": user["tipo"]}
    return None
