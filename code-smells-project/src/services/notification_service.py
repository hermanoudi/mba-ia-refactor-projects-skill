import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def order_created(self, pedido_id, usuario_id):
        logger.info("EMAIL: Pedido %s criado para usuário %s", pedido_id, usuario_id)
        logger.info("SMS: Seu pedido foi recebido!")
        logger.info("PUSH: Novo pedido recebido pelo sistema")

    def order_status_changed(self, pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info("NOTIFICAÇÃO: Pedido %s aprovado — preparar envio.", pedido_id)
        elif novo_status == "cancelado":
            logger.info("NOTIFICAÇÃO: Pedido %s cancelado — devolver estoque.", pedido_id)


notification_service = NotificationService()
