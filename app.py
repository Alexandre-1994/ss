from flask import Flask, render_template, request, jsonify, url_for
from medical_ai_module import MedicalDiagnosisAI
from sklearn.preprocessing import OneHotEncoder
import sqlite3
import logging
from datetime import datetime
import json
import os
from config import DevelopmentConfig

# Criar aplicação Flask
# Criar aplicação Flask
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# Configurar logging
logging.basicConfig(
    filename=app.config['LOG_FILENAME'],
    level=app.config['LOG_LEVEL'],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar logger para console também
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Função para conectar ao banco de dados
def get_db_connection():
    try:
        conn = sqlite3.connect('clinica.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

# Inicialização do banco de dados
def init_db():
    try:
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            
            # Criar tabela de pacientes
            cursor.execute('''
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
            
            # Criar tabela de consultas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER,
                    sintomas TEXT,
                    diagnostico TEXT,
                    recomendacao TEXT,
                    urgencia TEXT,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
                )
            ''')
            
            conn.commit()
            logger.info("Banco de dados inicializado com sucesso")
            return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

# Carregar a base de conhecimento
def load_knowledge_base():
    try:
        with open('knowledge_base.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Erro ao carregar knowledge_base.json: {str(e)}")
        return {"categorias": {}}

# Calcular idade
def calcular_idade(data_nascimento):
    nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d')
    hoje = datetime.now()
    idade = hoje.year - nascimento.year
    if hoje.month < nascimento.month or (hoje.month == nascimento.month and hoje.day < nascimento.day):
        idade -= 1
    return idade

# Inicialização global
knowledge_base = load_knowledge_base()
medical_ai = None
diagnostics_history = []
estado_atual = {
    "sintomas_verificados": [],
    "dados_do_paciente": {}
}

# Inicializar medical_ai
try:
    medical_ai = MedicalDiagnosisAI(knowledge_base)
    logger.info("MedicalDiagnosisAI inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar MedicalDiagnosisAI: {str(e)}")

# Suas rotas continuam aqui...
# Rotas para gerenciar pacientes
@app.route('/paciente/<int:id>', methods=['GET'])
def obter_paciente(id):
    try:
        logger.debug(f"Buscando paciente com ID: {id}")
        
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pacientes WHERE id = ?', (id,))
            paciente = cursor.fetchone()
            conn.close()
            
            if paciente:
                logger.debug(f"Paciente encontrado: {paciente['nome']}")
                return jsonify({
                    "id": paciente['id'],
                    "nome": paciente['nome'],
                    "idade": paciente['idade'],
                    "genero": paciente['genero'],
                    "telefone": paciente['telefone'],
                    "email": paciente['email'],
                    "endereco": paciente['endereco']
                })
                
        logger.warning(f"Paciente com ID {id} não encontrado")
        return jsonify({"message": "Paciente não encontrado"}), 404
        
    except Exception as e:
        logger.exception(f"Erro ao buscar paciente: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/paciente/<int:id>', methods=['DELETE'])
def excluir_paciente(id):
    try:
        logger.debug(f"Tentando excluir paciente com ID: {id}")
        
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM pacientes WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            
            logger.info(f"Paciente com ID {id} excluído com sucesso")
            return jsonify({"status": "success", "message": "Paciente excluído com sucesso"})
            
    except Exception as e:
        logger.exception(f"Erro ao excluir paciente: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    API endpoint para estatísticas do sistema
    """
    try:
        logger.debug("Gerando estatísticas do sistema")
        
        stats = {
            'total_diagnosticos': len(diagnostics_history),
            'diagnosticos_por_categoria': {
                categoria: diagnostics_history.count(categoria)
                for categoria in knowledge_base["categorias"].keys()
            }
        }
        
        logger.debug(f"Estatísticas geradas: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        logger.exception(f"Erro ao gerar estatísticas: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reiniciar', methods=['POST'])
def reiniciar_verificacao():
    try:
        logger.debug("Reiniciando verificação")
        
        global estado_atual
        estado_atual = {
            "sintomas_verificados": [],
            "dados_do_paciente": {}
        }
        
        logger.info("Verificação reiniciada com sucesso")
        return jsonify({"status": "reiniciado com sucesso"}), 200
        
    except Exception as e:
        logger.exception(f"Erro ao reiniciar verificação: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/consulta', methods=['POST'])
def adicionar_consulta():
    try:
        logger.debug(f"Dados recebidos para nova consulta: {request.form}")
        
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            dados = request.form
            
            cursor.execute('''
                INSERT INTO consultas (paciente_id, sintomas, diagnostico, 
                                     recomendacao, urgencia, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                dados['paciente_id'],
                dados['sintomas'],
                dados['diagnostico'],
                dados['recomendacao'],
                dados['urgencia'],
                dados.get('observacoes', '')
            ))
            
            last_id = cursor.lastrowid
            logger.debug(f"Consulta inserida com ID: {last_id}")
            
            conn.commit()
            conn.close()
            return jsonify({
                "status": "success", 
                "message": "Consulta adicionada com sucesso",
                "id": last_id
            })
            
    except Exception as e:
        logger.exception(f"Erro ao adicionar consulta: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/consultas/<int:paciente_id>', methods=['GET'])
def obter_consultas_paciente(paciente_id):
    try:
        logger.debug(f"Buscando consultas do paciente ID: {paciente_id}")
        
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, p.nome as nome_paciente
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.paciente_id = ?
                ORDER BY c.data DESC
            ''', (paciente_id,))
            
            consultas = cursor.fetchall()
            conn.close()
            
            logger.debug(f"Encontradas {len(consultas)} consultas para o paciente")
            
            return jsonify([{
                'id': c['id'],
                'data': c['data'],
                'sintomas': c['sintomas'],
                'diagnostico': c['diagnostico'],
                'recomendacao': c['recomendacao'],
                'urgencia': c['urgencia'],
                'observacoes': c['observacoes'],
                'nome_paciente': c['nome_paciente']
            } for c in consultas])
            
    except Exception as e:
        logger.exception(f"Erro ao buscar consultas: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        resultado = None
        pacientes = []
        
        # Log para desenvolvimento
        logger.debug(f"Método da requisição: {request.method}")
        if request.method == 'POST':
            logger.debug(f"Dados do formulário: {request.form}")
        
        # Obter lista de pacientes
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pacientes ORDER BY nome')
            pacientes = cursor.fetchall()
            conn.close()
            logger.debug(f"Número de pacientes recuperados: {len(pacientes)}")

        if request.method == 'POST':
            sintomas_relatados = request.form.getlist('sintomas')
            info_adicional = request.form.get('info_adicional', '')
            
            logger.debug(f"Sintomas relatados: {sintomas_relatados}")
            logger.debug(f"Informações adicionais: {info_adicional}")
            
            if sintomas_relatados and medical_ai:
                resultado = medical_ai.analyze_symptoms(sintomas_relatados)
                logger.debug(f"Resultado da análise: {resultado}")
                
                if resultado:
                    diagnostics_history.append(resultado["categoria"])
                    logger.debug(f"Diagnóstico adicionado ao histórico: {resultado['categoria']}")

        return render_template('index.html',
                             resultado=resultado,
                             knowledge_base=knowledge_base,
                             diagnostics_history=diagnostics_history,
                             pacientes=pacientes)

    except Exception as e:
        logger.exception(f"Erro na rota index: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/paciente', methods=['POST'])
def adicionar_paciente():
    try:
        logger.debug(f"Dados recebidos para novo paciente: {request.form}")
        
        conn = get_db_connection()
        if conn is not None:
            cursor = conn.cursor()
            dados = request.form
            
            # Log dos dados antes da inserção
            logger.debug(f"Preparando para inserir paciente: {dados['nome']}")
            
            cursor.execute('''
                INSERT INTO pacientes (nome, idade, genero, telefone, email, endereco)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                dados['nome'],
                calcular_idade(dados['data_nascimento']),
                dados['genero'],
                dados.get('telefone'),
                dados.get('email'),
                dados.get('endereco')
            ))
            
            last_id = cursor.lastrowid
            logger.debug(f"Paciente inserido com ID: {last_id}")
            
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "Paciente adicionado com sucesso", "id": last_id})
    except Exception as e:
        logger.exception(f"Erro ao adicionar paciente: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Configuração de inicialização
if __name__ == '__main__':
     with app.app_context():
        logger.info("Iniciando aplicação em modo de desenvolvimento")
        init_db()
        logger.info("Banco de dados inicializado")
        
        # Verificar se knowledge_base foi carregado corretamente
        if knowledge_base.get("categorias"):
            logger.info(f"Base de conhecimento carregada com {len(knowledge_base['categorias'])} categorias")
        else:
            logger.warning("Base de conhecimento vazia ou não carregada corretamente")
        
        # Verificar se medical_ai foi inicializado
        if medical_ai:
            logger.info("Sistema de IA médica inicializado com sucesso")
        else:
            logger.warning("Sistema de IA médica não foi inicializado corretamente")
        
        # Iniciar servidor
        logger.info("Iniciando servidor de desenvolvimento...")
        app.run(host='0.0.0.0', port=5000, debug=True)