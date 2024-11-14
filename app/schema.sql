-- Eliminar tabelas se existirem
DROP TABLE IF EXISTS consultas;
DROP TABLE IF EXISTS pacientes;

-- Criar tabela de pacientes
CREATE TABLE pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    idade INTEGER,
    genero TEXT,
    telefone TEXT,
    email TEXT,
    endereco TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar tabela de consultas
CREATE TABLE consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER,
    sintomas TEXT,
    diagnostico TEXT,
    recomendacao TEXT,
    urgencia TEXT,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT,
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

-- Inserir alguns dados de exemplo
INSERT INTO pacientes (nome, idade, genero, telefone, email, endereco)
VALUES 
    ('João Silva', 45, 'M', '123-456-789', 'joao@email.com', 'Rua A, 123'),
    ('Maria Santos', 32, 'F', '987-654-321', 'maria@email.com', 'Av B, 456'),
    ('Pedro Oliveira', 28, 'M', '456-789-123', 'pedro@email.com', 'Rua C, 789');