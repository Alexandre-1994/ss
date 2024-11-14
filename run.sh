#!/bin/bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 -m flask run --host=127.0.0.1 --port=5001
