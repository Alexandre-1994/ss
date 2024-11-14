from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from app.database import (
    get_db, get_paciente, get_pacientes, get_consultas_paciente, 
    adicionar_consulta
)
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    try:
        resultado = None
        pacientes = get_pacientes()  # Usando a função auxiliar
        logger.debug(f"Número de pacientes recuperados: {len(pacientes)}")

        if request.method == 'POST':
            paciente_id = request.form.get('paciente_id')
            sintomas_relatados = request.form.getlist('sintomas')
            observacoes = request.form.get('observacoes', '')

            # Validações
            if not paciente_id:
                flash('Selecione um paciente antes de realizar o diagnóstico', 'warning')
                return redirect(url_for('main.index'))

            if not sintomas_relatados:
                flash('Selecione pelo menos um sintoma', 'warning')
                return redirect(url_for('main.index'))

            # Verificar se o paciente existe
            paciente = get_paciente(paciente_id)
            if not paciente:
                flash('Paciente não encontrado', 'danger')
                return redirect(url_for('main.index'))

            # Realizar diagnóstico
            if current_app.medical_ai:
                resultado = current_app.medical_ai.analyze_symptoms(sintomas_relatados)
                logger.debug(f"Resultado da análise: {resultado}")

                if resultado:
                    # Salvar consulta usando função auxiliar
                    consulta_id = adicionar_consulta(
                        paciente_id=paciente_id,
                        sintomas=sintomas_relatados,
                        diagnostico=resultado.get('possivel_condicao'),
                        recomendacao=resultado.get('recomendacao'),
                        urgencia=resultado.get('urgencia'),
                        observacoes=observacoes
                    )

                    if consulta_id:
                        flash('Diagnóstico realizado com sucesso!', 'success')
                    else:
                        flash('Erro ao salvar consulta', 'danger')
                else:
                    flash('Não foi possível determinar um diagnóstico', 'warning')
            else:
                flash('Sistema de diagnóstico não está disponível', 'danger')

        return render_template('index.html',
                             resultado=resultado,
                             pacientes=pacientes,
                             knowledge_base=current_app.knowledge_base)

    except Exception as e:
        logger.exception(f"Erro na rota index: {str(e)}")
        flash('Ocorreu um erro ao processar sua solicitação', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/paciente', methods=['POST'])
def adicionar_paciente():
    try:
        db = get_db()
        if db is not None:
            cursor = db.cursor()
            dados = request.form
            
            # Validações básicas
            if not dados.get('nome'):
                return jsonify({"status": "error", "message": "Nome é obrigatório"}), 400

            # Log dos dados antes da inserção
            logger.debug(f"Preparando para inserir paciente: {dados['nome']}")
            
            cursor.execute('''
                INSERT INTO pacientes (nome, idade, genero, telefone, email, endereco)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                dados['nome'],
                int(dados['idade']) if dados.get('idade') else None,
                dados.get('genero'),
                dados.get('telefone'),
                dados.get('email'),
                dados.get('endereco')
            ))
            
            db.commit()
            last_id = cursor.lastrowid
            logger.debug(f"Paciente inserido com ID: {last_id}")
            
            # Buscar paciente recém-inserido
            cursor.execute('SELECT * FROM pacientes WHERE id = ?', (last_id,))
            paciente = cursor.fetchone()
            
            flash('Paciente adicionado com sucesso!', 'success')
            return jsonify({
                "status": "success", 
                "message": "Paciente adicionado com sucesso",
                "id": last_id,
                "paciente": dict(paciente)
            })
    except Exception as e:
        logger.exception(f"Erro ao adicionar paciente: {str(e)}")
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@main_bp.route('/paciente/<int:id>')
def detalhes_paciente(id):
    try:
        paciente = get_paciente(id)
        if not paciente:
            flash('Paciente não encontrado', 'danger')
            return redirect(url_for('main.index'))
            
        consultas = get_consultas_paciente(id)
        
        return render_template('paciente/detalhes.html',
                             paciente=paciente,
                             consultas=consultas)
    except Exception as e:
        logger.exception(f"Erro ao buscar detalhes do paciente: {str(e)}")
        flash('Erro ao buscar detalhes do paciente', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/paciente/<int:id>/historico')
def historico_paciente(id):
    try:
        paciente = get_paciente(id)
        if not paciente:
            flash('Paciente não encontrado', 'danger')
            return redirect(url_for('main.index'))
        
        consultas = get_consultas_paciente(id)
        
        return render_template('paciente/historico.html',
                             paciente=paciente,
                             consultas=consultas)
            
    except Exception as e:
        logger.exception(f"Erro ao buscar histórico: {str(e)}")
        flash('Erro ao buscar histórico do paciente', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/consultas/<int:paciente_id>')
def consultas_paciente(paciente_id):
    try:
        consultas = get_consultas_paciente(paciente_id)
        
        # Converter para lista de dicionários
        consultas_list = []
        for consulta in consultas:
            consulta_dict = dict(consulta)
            # Converter sintomas de JSON para lista
            if consulta_dict.get('sintomas'):
                consulta_dict['sintomas'] = json.loads(consulta_dict['sintomas'])
            consultas_list.append(consulta_dict)
            
        return jsonify(consultas_list)
            
    except Exception as e:
        logger.exception(f"Erro ao buscar consultas: {str(e)}")
        return jsonify({"error": "Erro ao buscar consultas"}), 500

@main_bp.route('/estatisticas')
def estatisticas():
    try:
        db = get_db()
        if db is not None:
            cursor = db.cursor()
            
            # Total de consultas
            cursor.execute('SELECT COUNT(*) as total FROM consultas')
            total_consultas = cursor.fetchone()['total']
            
            # Consultas por urgência
            cursor.execute('''
                SELECT urgencia, COUNT(*) as count 
                FROM consultas 
                GROUP BY urgencia
            ''')
            urgencias = cursor.fetchall()
            
            # Diagnósticos mais comuns
            cursor.execute('''
                SELECT diagnostico, COUNT(*) as count 
                FROM consultas 
                GROUP BY diagnostico 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            diagnosticos = cursor.fetchall()
            
            return render_template('estatisticas.html',
                                 total_consultas=total_consultas,
                                 urgencias=urgencias,
                                 diagnosticos=diagnosticos)
            
    except Exception as e:
        logger.exception(f"Erro ao gerar estatísticas: {str(e)}")
        flash('Erro ao gerar estatísticas', 'danger')
        return redirect(url_for('main.index'))

# Filtros personalizados
@main_bp.app_template_filter('format_date')
def format_date(date_str):
    try:
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:
            date_obj = date_str
        return date_obj.strftime('%d/%m/%Y %H:%M')
    except Exception:
        return date_str

@main_bp.app_template_filter('format_json')
def format_json(json_str):
    try:
        if isinstance(json_str, str):
            return json.loads(json_str)
        return json_str
    except Exception:
        return json_str