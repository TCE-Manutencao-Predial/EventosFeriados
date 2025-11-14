#!/bin/bash
# =============================================================================
# SCRIPT DE EXECUÇÃO - EVENTOS E FERIADOS
# =============================================================================
# Executa o servidor web em modo desenvolvimento
# Versão: 2.0.0
# =============================================================================

set -e

# Carrega configurações do .env.deploy
source ./scripts/config.sh

echo "🚀 Iniciando servidor Eventos e Feriados..."
echo "   Backend: $ROOT_BACKEND"
echo "   Porta: $PORT"
echo ""

cd $ROOT_BACKEND

# Executa waitress diretamente
./.venv/bin/waitress-serve --host 127.0.0.1 --port $PORT $APP_NAME:app
