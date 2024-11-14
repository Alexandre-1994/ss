import os
from datetime import timedelta

class Config:
    # Diretórios base
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    
    # Criar diretório instance se não existir
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    # Caminhos para arquivos importantes
    DATABASE_PATH = os.path.join(BASE_DIR, 'clinica.db')
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    LOG_FOLDER = os.path.join(BASE_DIR, 'logs')
    
    # Criar diretório de logs se não existir
    os.makedirs(LOG_FOLDER, exist_ok=True)
    
    # Arquivos de log
    LOG_FILENAME = os.path.join(LOG_FOLDER, 'app.log')
    ERROR_LOG_FILENAME = os.path.join(LOG_FOLDER, 'error.log')
    
    # Configurações de segurança
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')
    CSRF_ENABLED = True
    CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY', 'sua-outra-chave-secreta-aqui')
    
    # Configurações de sessão
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Configurações do banco de dados
    SQLITE_DATABASE = DATABASE_PATH
    SQLITE_FOREIGN_KEYS = True
    DATABASE_CONNECT_OPTIONS = {}
    
    # Configurações de aplicação
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True
    DEVELOPMENT = True
    TESTING = False
    
    # Sobrescrever configurações de segurança para desenvolvimento
    SESSION_COOKIE_SECURE = False
    
    # Configurações de logging para desenvolvimento
    LOG_LEVEL = 'DEBUG'
    
    # Configurações de cache para desenvolvimento
    CACHE_TYPE = 'simple'
    
    # Configurações específicas de desenvolvimento
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

class TestingConfig(Config):
    ENV = 'testing'
    TESTING = True
    DEBUG = True
    
    # Usar banco de dados em memória para testes
    DATABASE_PATH = ':memory:'
    
    # Desabilitar CSRF para testes
    WTF_CSRF_ENABLED = False
    
    # Configurações de logging para testes
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Configurações de segurança para produção
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configurações de logging para produção
    LOG_LEVEL = 'ERROR'
    
    # Configurações de cache para produção
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = 6379
    
    # Tempo limite de upload maior para produção
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    
    @classmethod
    def init_app(cls, app):
        # Configurações adicionais de produção
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Configurar logging de produção
        file_handler = RotatingFileHandler(
            cls.ERROR_LOG_FILENAME,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=10
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        app.logger.addHandler(file_handler)

# Função para obter configuração baseada no ambiente
def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig
    }
    return configs.get(env, DevelopmentConfig)