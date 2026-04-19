import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-key-change-in-production')
DATABASE = os.environ.get('DATABASE', 'loja.db')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

VALID_CATEGORIES = ['informatica', 'moveis', 'vestuario', 'geral', 'eletronicos', 'livros']
ORDER_STATUSES = ['pendente', 'aprovado', 'enviado', 'entregue', 'cancelado']
