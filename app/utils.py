import sqlite3
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = sqlite3.connect(current_app.config['DATABASE_PATH'])
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

def flash_message(message, category='info'):
    """Helper para padronizar mensagens flash"""
    flash(message, category)
    logger.info(f"Flash message ({category}): {message}")