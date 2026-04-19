from flask import Flask, jsonify
from flask_cors import CORS

from src.config import settings
from src.config.database import init_db
from src.middlewares.error_handler import register_error_handlers
from src.views import produto_routes, usuario_routes, pedido_routes


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DATABASE'] = settings.DATABASE
    app.config['DEBUG'] = settings.DEBUG

    CORS(app)
    register_error_handlers(app)
    init_db(app)

    app.register_blueprint(produto_routes.bp)
    app.register_blueprint(usuario_routes.bp)
    app.register_blueprint(pedido_routes.bp)

    @app.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "2.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            }
        })

    @app.get("/health")
    def health():
        from src.config.database import get_db
        cursor = get_db().cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            "versao": "2.0.0",
        })

    return app


if __name__ == "__main__":
    application = create_app()
    print("=" * 50)
    print("SERVIDOR INICIADO — http://localhost:5000")
    print("=" * 50)
    application.run(host="0.0.0.0", port=5000)
