import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

class MedicalDiagnosisAI:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.encoder = OneHotEncoder()
        self.model = RandomForestClassifier()
        self.train_model()

    def train_model(self):
        # Preparar os dados de treinamento
        X, y = self.prepare_training_data()
        self.encoder.fit(X)
        X_encoded = self.encoder.transform(X).toarray()
        self.model.fit(X_encoded, y)

    def prepare_training_data(self):
        X = []
        y = []
        max_symptoms = 0

        for categoria, condicoes in self.knowledge_base["categorias"].items():
            for condicao, dados in condicoes.items():
                max_symptoms = max(max_symptoms, len(dados["sintomas"]))

        for categoria, condicoes in self.knowledge_base["categorias"].items():
            for condicao, dados in condicoes.items():
                symptoms = dados["sintomas"] + ["None"] * (max_symptoms - len(dados["sintomas"]))
                X.append(symptoms)
                y.append(categoria + ":" + condicao)

        return X, y

    def analyze_symptoms(self, symptoms, additional_info):
        # Codificar os sintomas
        symptom_vector = symptoms + ["None"] * (self.encoder.n_features_in_ - len(symptoms))
        symptom_vector = self.encoder.transform([symptom_vector]).toarray()[0]

        # Fazer a previsão usando o modelo treinado
        prediction = self.model.predict([symptom_vector])[0]

        # Recuperar os detalhes da condição prevista
        predicted_condition = None
        predicted_category = None
        for categoria, condicoes in self.knowledge_base["categorias"].items():
            for condicao, dados in condicoes.items():
                if categoria + ":" + condicao == prediction:
                    predicted_category = categoria
                    predicted_condition = dados
                    predicted_condition["categoria"] = categoria
                    predicted_condition["condicao"] = condicao
                    break
            if predicted_condition:
                break

        return predicted_condition