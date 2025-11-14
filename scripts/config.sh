#!/bin/bash
# =============================================================================
# CONFIGURAÇÃO DE DEPLOY - EVENTOS E FERIADOS
# =============================================================================
# Este arquivo carrega configurações do .env.deploy (fonte única de verdade)
# Versão: 2.0.0
# =============================================================================

# Carrega variáveis de ambiente do .env.deploy
if [ -f ".env.deploy" ]; then
    echo "📝 Carregando configurações de .env.deploy..."
    source .env.deploy
else
    echo "❌ ERRO: Arquivo .env.deploy não encontrado!"
    echo "💡 Execute: make reset-env"
    exit 1
fi

# Validação de variáveis obrigatórias
REQUIRED_VARS=(
    "PROJECT_NAME"
    "SERVICE_NAME"
    "APP_NAME"
    "PORT"
    "ROOT_SOFTWARES"
    "ROOT_BACKEND"
    "ROOT_DATA"
    "ROOT_LOGS"
    "GIT_REPO_NAME"
    "GIT_REPO_OWNER"
    "GIT_REPO_URL"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ ERRO: Variável $var não configurada em .env.deploy"
        exit 1
    fi
done

# Variáveis derivadas para compatibilidade
GIT_REPO_LINK="$GIT_REPO_URL"
LOGS_PATH="$ROOT_LOGS"
HTACCESS_FILE="scripts/htaccess"

echo "✅ Configurações carregadas com sucesso!"
echo "   Projeto: $PROJECT_NAME"
echo "   App: $APP_NAME"
echo "   Porta: $PORT"
echo "   Backend: $ROOT_BACKEND"
echo "   Dados: $ROOT_DATA"
echo "   Logs: $ROOT_LOGS"

