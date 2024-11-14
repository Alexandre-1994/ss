from flask import Flask
from config.settings import DevelopmentConfig
from config.settings import get_config
import logging
import os
import json
from app import create_app
from medical_ai_module import MedicalDiagnosisAI

# Configurar logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
app = create_app(get_config())
# Verificar diretório atual
current_dir = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Diretório atual: {current_dir}")

# Criar aplicação
app = create_app(DevelopmentConfig)

# Verificar caminhos importantes
logger.info(f"Template folder: {app.template_folder}")
logger.info(f"Existe? {os.path.exists(app.template_folder)}")
logger.info(f"Static folder: {app.static_folder}")
logger.info(f"Existe? {os.path.exists(app.static_folder)}")

# Carregar base de conhecimento
knowledge_base_path = os.path.join(current_dir, 'knowledge_base.json')
logger.info(f"Procurando knowledge_base.json em: {knowledge_base_path}")

try:
    with open(knowledge_base_path, 'r', encoding='utf-8') as file:
        knowledge_base = json.load(file)
        app.knowledge_base = knowledge_base
        logger.info(f"Base de conhecimento carregada com {len(knowledge_base.get('categorias', {}))} categorias")
except Exception as e:
    logger.error(f"Erro ao carregar knowledge_base.json: {str(e)}")
    app.knowledge_base = {"categorias": {}}

# Inicializar IA médica
try:
    app.medical_ai = MedicalDiagnosisAI(app.knowledge_base)
    logger.info("Sistema de IA médica inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar MedicalDiagnosisAI: {str(e)}")
    app.medical_ai = None

# Registrar funções úteis para os templates
@app.context_processor
def utility_processor():
    return {
        'len': len,
        'str': str,
        'isinstance': isinstance,
        'list': list
    }

if __name__ == '__main__':
    # Verificar estrutura do projeto
    logger.info("Verificando estrutura do projeto...")
    logger.info(f"Database path: {app.config.get('DATABASE_PATH')}")
    logger.info(f"Template folder: {app.template_folder}")
    logger.info(f"Static folder: {app.static_folder}")
    logger.info(f"Knowledge base: {bool(app.knowledge_base.get('categorias'))}")
    logger.info(f"Medical AI: {bool(app.medical_ai)}")
    
    # Listar templates disponíveis
    if os.path.exists(app.template_folder):
        templates = os.listdir(app.template_folder)
        logger.info(f"Templates encontrados: {templates}")
    else:
        logger.error(f"Diretório de templates não encontrado: {app.template_folder}")
    
    # Executar a aplicação
    app.run(host='0.0.0.0', port=5001, debug=True)