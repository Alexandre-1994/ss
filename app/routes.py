from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app # type: ignore
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

# Rota para adicionar novo paciente
@main_bp.route('/paciente', methods=['POST'])
def adicionar_paciente():
    try:
        dados = request.form
        db = get_db()
        if db is not None:
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO pacientes (nome, idade, genero, telefone, email, endereco)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                dados['nome'],
                dados['idade'],
                dados['genero'],
                dados.get('telefone'),
                dados.get('email'),
                dados.get('endereco')
            ))
            db.commit()
            return jsonify({
                'status': 'success',
                'message': 'Paciente adicionado com sucesso',
                'id': cursor.lastrowid
            })
    except Exception as e:
        logger.exception(f"Erro ao adicionar paciente: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# Rota de pacientes - aceita GET e POST
@main_bp.route('/pacientes', methods=['GET', 'POST'])
def pacientes():
    try:
        if request.method == 'POST':
            # Lógica para adicionar/editar paciente
            pass
        
        # Lógica para listar pacientes
        db = get_db()
        if db is not None:
            cursor = db.cursor()
            cursor.execute('''
                SELECT 
                    p.*,
                    MAX(c.data) as ultima_consulta
                FROM pacientes p
                LEFT JOIN consultas c ON p.id = c.paciente_id
                GROUP BY p.id
                ORDER BY p.nome
            ''')
            pacientes = cursor.fetchall()
            return render_template('pacientes.html', pacientes=pacientes)
            
    except Exception as e:
        logger.exception(f"Erro ao listar pacientes: {str(e)}")
        flash('Erro ao carregar lista de pacientes', 'danger')
        return redirect(url_for('main.index'))
# Rota para gerenciar um paciente específico - aceita múltiplos métodos
@main_bp.route('/paciente/<int:id>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def paciente(id):
    try:
        if request.method == 'GET':
            # Obter dados do paciente
            db = get_db()
            if db is not None:
                cursor = db.cursor()
                cursor.execute('SELECT * FROM pacientes WHERE id = ?', (id,))
                paciente = cursor.fetchone()
                if paciente:
                    return jsonify(dict(paciente))
            return jsonify({'error': 'Paciente não encontrado'}), 404
            
        elif request.method in ['POST', 'PUT']:
            # Atualizar paciente
            dados = request.form
            db = get_db()
            if db is not None:
                cursor = db.cursor()
                cursor.execute('''
                    UPDATE pacientes 
                    SET nome=?, idade=?, genero=?, telefone=?, email=?, endereco=?
                    WHERE id=?
                ''', (
                    dados['nome'],
                    dados['idade'],
                    dados['genero'],
                    dados.get('telefone'),
                    dados.get('email'),
                    dados.get('endereco'),
                    id
                ))
                db.commit()
                return jsonify({'status': 'success', 'message': 'Paciente atualizado'})
                
        elif request.method == 'DELETE':
            # Excluir paciente
            db = get_db()
            if db is not None:
                cursor = db.cursor()
                cursor.execute('DELETE FROM pacientes WHERE id = ?', (id,))
                db.commit()
                return jsonify({'status': 'success', 'message': 'Paciente excluído'})
                
    except Exception as e:
        logger.exception(f"Erro ao manipular paciente: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

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

@main_bp.route('/historico')
def historico():
    try:
        db = get_db()
        if db is not None:
            cursor = db.cursor()
            
            # Buscar todas as consultas com informações do paciente
            cursor.execute('''
                SELECT 
                    c.*,
                    p.nome as nome_paciente,
                    p.id as paciente_id
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                ORDER BY c.data DESC
            ''')
            consultas = cursor.fetchall()
            
            # Calcular estatísticas
            stats = {
                'total_consultas': len(consultas),
                'urgencias': {
                    'alta': 0,
                    'moderada': 0,
                    'baixa': 0
                }
            }
            
            for consulta in consultas:
                stats['urgencias'][consulta['urgencia'].lower()] += 1
            
            return render_template('historico.html',
                                 consultas=consultas,
                                 stats=stats)
            
    except Exception as e:
        logger.exception(f"Erro ao buscar histórico: {str(e)}")
        flash('Erro ao carregar histórico', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/consulta/<int:id>')
def consulta_detalhes(id):
    try:
        db = get_db()
        if db is not None:
            cursor = db.cursor()
            cursor.execute('''
                SELECT 
                    c.*,
                    p.nome as nome_paciente
                FROM consultas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE c.id = ?
            ''', (id,))
            
            consulta = cursor.fetchone()
            if consulta:
                # Converter consulta para dicionário
                consulta_dict = dict(consulta)
                consulta_dict['sintomas'] = json.loads(consulta_dict['sintomas'])
                return jsonify(consulta_dict)
            
            return jsonify({'error': 'Consulta não encontrada'}), 404
            
    except Exception as e:
        logger.exception(f"Erro ao buscar detalhes da consulta: {str(e)}")
        return jsonify({'error': 'Erro ao buscar detalhes'}), 500
# Rota para histórico
@main_bp.route('/paciente/<int:id>/historico', methods=['GET'])
def historico_paciente(id):
   try:
       # Buscar paciente
       db = get_db()
       if db is not None:
           cursor = db.cursor()
           
           # Buscar dados do paciente
           cursor.execute('''
               SELECT * FROM pacientes WHERE id = ?
           ''', (id,))
           paciente = cursor.fetchone()
           
           if not paciente:
               flash('Paciente não encontrado', 'danger')
               return redirect(url_for('main.pacientes'))
           
           # Buscar consultas do paciente
           cursor.execute('''
               SELECT 
                   c.*,
                   strftime('%d/%m/%Y %H:%M', c.data) as data_formatada
               FROM consultas c
               WHERE c.paciente_id = ?
               ORDER BY c.data DESC
           ''', (id,))
           consultas = cursor.fetchall()
           
           # Calcular estatísticas do paciente
           stats = {
               'total_consultas': len(consultas),
               'urgencias': {
                   'alta': 0,
                   'moderada': 0,
                   'baixa': 0
               },
               'diagnosticos_frequentes': {}
           }
           
           # Processar consultas para estatísticas
           for consulta in consultas:
               # Contagem de urgências
               urgencia = consulta['urgencia'].lower()
               stats['urgencias'][urgencia] = stats['urgencias'].get(urgencia, 0) + 1
               
               # Contagem de diagnósticos
               diagnostico = consulta['diagnostico']
               stats['diagnosticos_frequentes'][diagnostico] = stats['diagnosticos_frequentes'].get(diagnostico, 0) + 1
           
           # Ordenar diagnósticos mais frequentes
           stats['diagnosticos_frequentes'] = dict(
               sorted(
                   stats['diagnosticos_frequentes'].items(), 
                   key=lambda x: x[1], 
                   reverse=True
               )[:5]  # Top 5 diagnósticos
           )
           
           # Buscar última consulta
           ultima_consulta = consultas[0] if consultas else None
           
           return render_template('paciente/historico.html',
                                paciente=paciente,
                                consultas=consultas,
                                stats=stats,
                                ultima_consulta=ultima_consulta)
           
   except Exception as e:
       logger.exception(f"Erro ao buscar histórico do paciente {id}: {str(e)}")
       flash('Erro ao carregar histórico do paciente', 'danger')
       return redirect(url_for('main.pacientes'))

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

@main_bp.route('/estatisticas', methods=['GET'])
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