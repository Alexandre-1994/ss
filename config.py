import logging

class Config:
    # Configurações básicas
    SECRET_KEY = 'chave-desenvolvimento-secreta'
    TESTING = False
    
    # Configurações de logging
    LOG_FILENAME = 'development.log'
    LOG_LEVEL = logging.DEBUG
    
    # Outras configurações
    DATABASE_URI = 'sqlite:///clinica.db'

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    ENV = 'development'
    # Configurações específicas para desenvolvimento
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    ENV = 'production'