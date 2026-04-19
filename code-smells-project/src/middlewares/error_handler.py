import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return {"erro": str(e), "sucesso": False}, 400

    @app.errorhandler(PermissionError)
    def handle_permission_error(e):
        return {"erro": str(e), "sucesso": False}, 401

    @app.errorhandler(404)
    def handle_not_found(e):
        return {"erro": "Recurso não encontrado", "sucesso": False}, 404

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Erro inesperado: %s", e)
        return {"erro": "Erro interno do servidor", "sucesso": False}, 500
