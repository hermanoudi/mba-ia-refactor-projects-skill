from src.config.database import get_db


def get_all():
    cursor = get_db().cursor()
    cursor.execute("SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos")
    return [dict(row) for row in cursor.fetchall()]


def get_by_id(produto_id):
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos WHERE id = ?",
        (produto_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def search(termo="", categoria=None, preco_min=None, preco_max=None):
    query = "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos WHERE 1=1"
    params = []

    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor = get_db().cursor()
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def create(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def update(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, categoria=? WHERE id=?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def delete(produto_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def decrement_stock(produto_id, quantidade, cursor):
    cursor.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        (quantidade, produto_id),
    )
