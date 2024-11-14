from flask import Flask
from config.settings import DevelopmentConfig
import os
import logging
import json

logger = logging.getLogger(__name__)

def create_app(config_class=DevelopmentConfig):
    # Obter caminho absoluto para o diretório base
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Definir caminhos para templates e static
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    # Logging de caminhos
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Template directory: {template_dir}")
    logger.info(f"Static directory: {static_dir}")
    
    # Criar aplicação Flask
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Carregar configurações
    app.config.from_object(config_class)
    
    # Verificar existência dos diretórios necessários
    if not os.path.exists(template_dir):
        logger.error(f"Template directory not found: {template_dir}")
        os.makedirs(template_dir, exist_ok=True)
        logger.info("Template directory created")
    
    if not os.path.exists(static_dir):
        logger.error(f"Static directory not found: {static_dir}")
        os.makedirs(static_dir, exist_ok=True)
        logger.info("Static directory created")
    
    # Configurar sessão
    app.secret_key = config_class.SECRET_KEY
    
    # Registrar blueprints
    try:
        from app.routes import main_bp
        app.register_blueprint(main_bp)
        logger.info("Main blueprint registered successfully")
    except Exception as e:
        logger.error(f"Error registering blueprint: {str(e)}")
    
    # Inicializar database
    try:
        from app.database import init_app
        init_app(app)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
    
    # Registrar funções úteis para os templates
    @app.context_processor
    def utility_processor():
        return {
            'len': len,
            'str': str,
            'isinstance': isinstance,
            'list': list,
            'enumerate': enumerate
        }
    
    # Registrar manipuladores de erro
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Verificar base de conhecimento
    try:
        knowledge_base_path = os.path.join(base_dir, 'knowledge_base.json')
        if os.path.exists(knowledge_base_path):
            with open(knowledge_base_path, 'r', encoding='utf-8') as file:
                app.knowledge_base = json.load(file)
                logger.info("Knowledge base loaded successfully")
        else:
            logger.warning("Knowledge base file not found")
            app.knowledge_base = {"categorias": {}}
    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}")
        app.knowledge_base = {"categorias": {}}
    
    # Log de verificação final
    logger.info("Application created successfully")
    logger.info(f"Debug mode: {app.debug}")
    logger.info(f"Testing mode: {app.testing}")
    logger.info(f"Template folder: {app.template_folder}")
    logger.info(f"Static folder: {app.static_folder}")
    
    return app