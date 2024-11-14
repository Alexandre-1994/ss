import sqlite3
import logging
import os
from flask import current_app, g
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        try:
            db_path = current_app.config['DATABASE_PATH']
            logger.debug(f"Tentando conectar ao banco de dados em: {db_path}")
            
            # Verificar se o diretório existe
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            
            # Habilitar foreign keys
            g.db.execute('PRAGMA foreign_keys = ON')
            
            logger.info("Conexão com banco de dados estabelecida com sucesso")
            return g.db
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
            return None
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        logger.debug("Conexão com banco de dados fechada")

def init_db():
    """Inicializa o banco de dados."""
    try:
        db = get_db()
        if db is not None:
            # Criar tabelas
            db.execute('''
                CREATE TABLE IF NOT EXISTS pacientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    idade INTEGER,
                    genero TEXT,
                    telefone TEXT,
                    email TEXT,
                    endereco TEXT,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            db.execute('''
                CREATE TABLE IF NOT EXISTS consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER,
                    sintomas TEXT,
                    diagnostico TEXT,
                    recomendacao TEXT,
                    urgencia TEXT,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
                )
            ''')
            
            # Inserir alguns dados de exemplo se a tabela estiver vazia
            cursor = db.cursor()
            cursor.execute('SELECT COUNT(*) FROM pacientes')
            if cursor.fetchone()[0] == 0:
                logger.info("Inserindo dados de exemplo")
                insert_sample_data(db)
            
            db.commit()
            logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        if db:
            db.rollback()

def insert_sample_data(db):
    """Insere dados de exemplo no banco de dados."""
    try:
        # Dados de exemplo para pacientes
        pacientes = [
            ('João Silva', 35, 'M', '123-456-789', 'joao@email.com', 'Rua A, 123'),
            ('Maria Santos', 28, 'F', '987-654-321', 'maria@email.com', 'Av B, 456'),
            ('Pedro Oliveira', 42, 'M', '456-789-123', 'pedro@email.com', 'Rua C, 789')
        ]
        
        db.executemany('''
            INSERT INTO pacientes (nome, idade, genero, telefone, email, endereco)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', pacientes)
        
        db.commit()
        logger.info("Dados de exemplo inseridos com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inserir dados de exemplo: {str(e)}")
        db.rollback()

def get_paciente(id):
    """Retorna um paciente específico pelo ID."""
    db = get_db()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM pacientes WHERE id = ?', (id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Erro ao buscar paciente {id}: {str(e)}")
    return None

def get_pacientes():
    """Retorna todos os pacientes."""
    db = get_db()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM pacientes ORDER BY nome')
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erro ao buscar pacientes: {str(e)}")
    return []

def get_consultas_paciente(paciente_id):
    """Retorna todas as consultas de um paciente."""
    db = get_db()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute('''
                SELECT c.*, p.nome as nome_paciente 
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.paciente_id = ?
                ORDER BY c.data DESC
            ''', (paciente_id,))
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erro ao buscar consultas do paciente {paciente_id}: {str(e)}")
    return []

def adicionar_consulta(paciente_id, sintomas, diagnostico, recomendacao, urgencia, observacoes):
    """Adiciona uma nova consulta."""
    db = get_db()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO consultas (
                    paciente_id, sintomas, diagnostico, recomendacao, 
                    urgencia, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                paciente_id,
                json.dumps(sintomas),
                diagnostico,
                recomendacao,
                urgencia,
                observacoes
            ))
            db.commit()
            logger.info(f"Consulta adicionada para o paciente {paciente_id}")
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Erro ao adicionar consulta: {str(e)}")
            db.rollback()
    return None

def init_app(app):
    """Inicializa a aplicação com as configurações do banco de dados."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()