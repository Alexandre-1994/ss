import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

class MedicalDiagnosisAI:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        # Removido o parâmetro 'sparse'
        self.encoder = OneHotEncoder(handle_unknown='ignore')
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.train_model()
        print("MedicalDiagnosisAI inicializado com sucesso")

    def train_model(self):
        try:
            # Preparar os dados de treinamento
            X, y = self.prepare_training_data()
            print(f"Dados de treinamento preparados - X shape: {len(X)}, y length: {len(y)}")
            
            # Transformar os dados para o formato correto para o OneHotEncoder
            X = [[str(sintoma) for sintoma in sample] for sample in X]
            
            # Fit the encoder and transform the data
            X_encoded = self.encoder.fit_transform(X)
            
            # Converter para array denso se necessário
            if hasattr(X_encoded, 'toarray'):
                X_encoded = X_encoded.toarray()
            
            # Train the model
            self.model.fit(X_encoded, y)
            print("Modelo treinado com sucesso")
            
        except Exception as e:
            print(f"Erro no treinamento do modelo: {str(e)}")
            raise

    def prepare_training_data(self):
        try:
            X = []
            y = []
            max_symptoms = 0

            # Encontrar o número máximo de sintomas
            for categoria, condicoes in self.knowledge_base["categorias"].items():
                for condicao, dados in condicoes.items():
                    max_symptoms = max(max_symptoms, len(dados["sintomas"]))

            print(f"Número máximo de sintomas encontrado: {max_symptoms}")

            # Preparar os dados de treinamento
            for categoria, condicoes in self.knowledge_base["categorias"].items():
                for condicao, dados in condicoes.items():
                    # Preencher com "None" até alcançar max_symptoms
                    symptoms = dados["sintomas"] + ["None"] * (max_symptoms - len(dados["sintomas"]))
                    X.append(symptoms)
                    y.append(f"{categoria}:{condicao}")

            # Converter X para formato numpy array
            X = np.array(X)
            y = np.array(y)

            print(f"Dados preparados - X: {X.shape}, y: {y.shape}")
            return X, y

        except Exception as e:
            print(f"Erro na preparação dos dados: {str(e)}")
            raise

    def analyze_symptoms(self, symptoms):
        try:
            print(f"Analisando sintomas: {symptoms}")
            
            if not symptoms:
                print("Nenhum sintoma fornecido")
                return None

            # Primeira abordagem: correspondência direta
            best_match = None
            max_score = 0

            for categoria, condicoes in self.knowledge_base["categorias"].items():
                for condicao, dados in condicoes.items():
                    # Calcular score de correspondência
                    symptom_set = set(symptoms)
                    condition_set = set(dados["sintomas"])
                    
                    # Calcular métricas
                    intersection = len(symptom_set.intersection(condition_set))
                    union = len(symptom_set.union(condition_set))
                    
                    # Calcular Coeficiente de Jaccard
                    score = intersection / union if union > 0 else 0
                    
                    # Adicionar peso adicional para correspondências exatas
                    if intersection == len(condition_set):
                        score *= 1.5
                    
                    print(f"Avaliando {categoria}-{condicao}: Score = {score}")

                    if score > max_score:
                        max_score = score
                        best_match = dados.copy()
                        best_match["categoria"] = categoria
                        best_match["condicao"] = condicao
                        best_match["confianca"] = round(score * 100, 2)

            # Definir um limite mínimo de confiança (30%)
            if best_match and max_score > 0.3:
                print(f"Melhor correspondência encontrada: {best_match['condicao']} com confiança de {best_match['confianca']}%")
                return best_match
            else:
                print("Nenhuma correspondência satisfatória encontrada")
                return None

        except Exception as e:
            print(f"Erro na análise de sintomas: {str(e)}")
            return None