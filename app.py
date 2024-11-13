import logging
logging.basicConfig(filename='app.log', level=logging.ERROR)
from medical_ai_module import MedicalDiagnosisAI
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
import json
import random

app = Flask(__name__)

# Base de conhecimento expandida com categorias e detalhes mais específicos
knowledge_base = {
    "categorias": {
        "cardiologia": {
            "hipertensao": {
                "sintomas": ["dor de cabeça", "tontura", "falta de ar", "visão embaçada"],
                "possivel_condicao": "Hipertensão Arterial",
                "recomendacao": "Monitoramento da pressão arterial e mudanças no estilo de vida",
                "urgencia": "moderada",
                "exames_recomendados": ["Medição de Pressão", "Exame de Sangue", "ECG"],
                "especialista": "Cardiologista",
                "fatores_risco": ["idade", "obesidade", "sedentarismo", "alimentação rica em sal"]
            }
        },
        "infectologia": {
            "malaria": {
                "sintomas": ["febre alta", "calafrios", "suor intenso", "dor muscular", "cansaço"],
                "possivel_condicao": "Malária",
                "recomendacao": "Procurar atendimento médico para teste rápido de malária",
                "urgencia": "alta",
                "exames_recomendados": ["Teste Rápido de Malária", "Exame de Sangue"],
                "especialista": "Infectologista",
                "fatores_risco": ["exposição a mosquitos", "região endêmica"]
            },
            "tuberculose": {
                "sintomas": ["tosse persistente", "perda de peso", "suor noturno", "febre", "fadiga"],
                "possivel_condicao": "Tuberculose",
                "recomendacao": "Procurar atendimento médico e realizar exame de escarro",
                "urgencia": "alta",
                "exames_recomendados": ["Teste de Escarro", "Raio-X de Tórax"],
                "especialista": "Infectologista",
                "fatores_risco": ["contato com infectados", "sistema imunológico enfraquecido"]
            }
        },
        "pneumologia": {
            "bronquite_cronica": {
                "sintomas": ["tosse persistente", "produção de muco", "falta de ar", "fadiga"],
                "possivel_condicao": "Bronquite Crônica",
                "recomendacao": "Evitar exposição a irritantes e buscar atendimento médico",
                "urgencia": "moderada",
                "exames_recomendados": ["Raio-X de Tórax", "Espirometria"],
                "especialista": "Pneumologista",
                "fatores_risco": ["tabagismo", "exposição a poluentes"]
            }
        },
        "gastroenterologia": {
            "diarreia": {
                "sintomas": ["fezes líquidas", "dor abdominal", "náusea", "febre"],
                "possivel_condicao": "Infecção Gastrointestinal",
                "recomendacao": "Manter hidratação e procurar atendimento caso os sintomas persistam",
                "urgencia": "moderada",
                "exames_recomendados": ["Exame de Fezes"],
                "especialista": "Gastroenterologista",
                "fatores_risco": ["água contaminada", "alimentos mal lavados"]
            }
        },
        "dermatologia": {
            "sarampo": {
                "sintomas": ["erupções na pele", "febre alta", "tosse", "conjuntivite"],
                "possivel_condicao": "Sarampo",
                "recomendacao": "Isolamento e procurar atendimento médico",
                "urgencia": "alta",
                "exames_recomendados": ["Exame de Sangue para Anticorpos"],
                "especialista": "Dermatologista",
                "fatores_risco": ["contato com infectados", "não vacinação"]
            }
        },
        "oftalmologia": {
            "conjuntivite": {
                "sintomas": ["olhos vermelhos", "coceira", "sensibilidade à luz", "lacrimejamento"],
                "possivel_condicao": "Conjuntivite",
                "recomendacao": "Evitar contato com os olhos e buscar atendimento",
                "urgencia": "baixa",
                "exames_recomendados": ["Avaliação Clínica"],
                "especialista": "Oftalmologista",
                "fatores_risco": ["contato com infectados", "alergias"]
            }
        }
    }
}

# Instância da IA de diagnóstico médico
medical_ai = MedicalDiagnosisAI(knowledge_base)

# Histórico de diagnósticos para análise
diagnostics_history = []

# Template HTML com interface moderna e recursos avançados
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Sistema Avançado de Diagnóstico Médico</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
        }
        
        body {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        
        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        
        .symptom-group {
            background-color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .urgency-high {
            color: #dc3545;
            font-weight: bold;
        }
        
        .urgency-moderate {
            color: #ffc107;
            font-weight: bold;
        }
        
        .urgency-low {
            color: #28a745;
            font-weight: bold;
        }
        
        .stats-card {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1 class="display-4">Sistema Avançado de Diagnóstico Médico</h1>
            <p class="lead">Análise inteligente de sintomas com suporte à decisão clínica</p>
        </div>
    </div>

    <div class="container">
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-body">
                        <h3>Avaliação de Sintomas</h3>
                        <form method="POST" id="diagnosticForm">
                            {% for categoria, condicoes in knowledge_base['categorias'].items() %}
                            <div class="symptom-group">
                                <h4>{{ categoria.title() }}</h4>
                                {% for condicao, dados in condicoes.items() %}
                                    {% for sintoma in dados['sintomas'] %}
                                    <div class="form-check">
                                        <input type="checkbox" class="form-check-input" 
                                               name="sintomas" value="{{ sintoma }}" 
                                               id="{{ sintoma|replace(' ', '_') }}">
                                        <label class="form-check-label" 
                                               for="{{ sintoma|replace(' ', '_') }}">
                                            {{ sintoma.title() }}
                                        </label>
                                    </div>
                                    {% endfor %}
                                {% endfor %}
                            </div>
                            {% endfor %}
                            
                            <div class="mb-3">
                                <label class="form-label">Informações Adicionais:</label>
                                <textarea class="form-control" name="info_adicional" 
                                          rows="3" placeholder="Descreva detalhes adicionais relevantes..."></textarea>
                            </div>
                            
                            <button type="submit" class="btn btn-primary">Analisar Sintomas</button>
                        </form>
                    </div>
                </div>
                
                {% if resultado %}
                <div class="card">
                    <div class="card-body">
                        <h3 class="card-title">Análise Detalhada</h3>
                        <div class="alert alert-{% if resultado.urgencia == 'alta' %}danger
                                                {% elif resultado.urgencia == 'moderada' %}warning
                                                {% else %}success{% endif %} mb-3">
                            Nível de Urgência: {{ resultado.urgencia.upper() }}
                        </div>
                        
                        <h4>Possível Condição:</h4>
                        <p class="lead">{{ resultado.possivel_condicao }}</p>
                        
                        <h4>Recomendações:</h4>
                        <ul class="list-group mb-3">
                            <li class="list-group-item">{{ resultado.recomendacao }}</li>
                            {% for exame in resultado.exames_recomendados %}
                            <li class="list-group-item">Exame recomendado: {{ exame }}</li>
                            {% endfor %}
                        </ul>
                        
                        <h4>Especialista Recomendado:</h4>
                        <p>{{ resultado.especialista }}</p>
                        
                        <h4>Fatores de Risco:</h4>
                        <ul class="list-group mb-3">
                            {% for fator in resultado.fatores_risco %}
                            <li class="list-group-item">{{ fator.title() }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h3>Estatísticas do Sistema</h3>
                        <div class="chart-container">
                            <canvas id="diagnosticsChart"></canvas>
                        </div>
                        <div class="stats-card">
                            <h5>Análises Realizadas</h5>
                            <p class="h3">{{ diagnostics_history|length }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.js"></script>
    <script>
        // Configuração do gráfico de diagnósticos
        const ctx = document.getElementById('diagnosticsChart').getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Cardiologia', 'Neurologia', 'Pneumologia'],
                datasets: [{
                    label: 'Diagnósticos por Especialidade',
                    data: [
                        {{ diagnostics_history.count('Cardiologia') }},
                        {{ diagnostics_history.count('Neurologia') }},
                        {{ diagnostics_history.count('Pneumologia') }}
                    ],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(75, 192, 192, 0.2)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(75, 192, 192, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

def analisar_sintomas(sintomas_relatados, info_adicional=""):
    """
    Analisa os sintomas relatados usando um algoritmo mais sofisticado
    que considera múltiplos fatores.
    """
    melhor_correspondencia = None
    max_score = 0

    for categoria, condicoes in knowledge_base["categorias"].items():
        for condicao, dados in condicoes.items():
            score = calcular_score_sintomas(sintomas_relatados, dados["sintomas"])
            
            if score > max_score:
                max_score = score
                melhor_correspondencia = dados.copy()
                melhor_correspondencia["categoria"] = categoria

    if melhor_correspondencia:
        # Registra o diagnóstico no histórico
        diagnostics_history.append(melhor_correspondencia["categoria"])
        return melhor_correspondencia
    
    return None

def calcular_score_sintomas(sintomas_relatados, sintomas_condicao):
    """
    Calcula um score de correspondência entre os sintomas relatados
    e os sintomas conhecidos de uma condição.
    """
    sintomas_relatados_set = set(sintomas_relatados)
    sintomas_condicao_set = set(sintomas_condicao)
    
    # Calcula a interseção e união dos conjuntos
    intersecao = len(sintomas_relatados_set.intersection(sintomas_condicao_set))
    uniao = len(sintomas_relatados_set.union(sintomas_condicao_set))
    
    # Calcula o coeficiente de Jaccard
    if uniao == 0:
        return 0
    return intersecao / uniao

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    if request.method == 'POST':
        sintomas_relatados = request.form.getlist('sintomas')
        info_adicional = request.form.get('info_adicional', '')
        
        if sintomas_relatados:
            resultado = medical_ai.analyze_symptoms(sintomas_relatados, info_adicional)
            
            # Registra o diagnóstico no histórico
            if resultado:
                diagnostics_history.append(resultado["categoria"])
    
    return render_template_string(HTML_TEMPLATE, 
                                resultado=resultado, 
                                knowledge_base=knowledge_base,
                                diagnostics_history=diagnostics_history)

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    API endpoint para estatísticas do sistema
    """
    stats = {
        'total_diagnosticos': len(diagnostics_history),
        'diagnosticos_por_categoria': {
            categoria: diagnostics_history.count(categoria)
            for categoria in knowledge_base["categorias"].keys()
        }
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)