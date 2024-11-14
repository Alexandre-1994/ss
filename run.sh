#!/bin/bash

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Configurar variáveis de ambiente
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Executar aplicação
python app.py