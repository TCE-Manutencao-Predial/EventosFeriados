#!/bin/bash
# =============================================================================
# GERADOR DE ARQUIVO DE SERVIÇO SYSTEMD
# =============================================================================
# Gera o arquivo .service a partir do template usando variáveis do .env.deploy
# Versão: 2.0.0
# =============================================================================

set -e

# Carrega configurações
if [ -f ".env.deploy" ]; then
    source .env.deploy
else
    echo "❌ ERRO: Arquivo .env.deploy não encontrado!"
    exit 1
fi

TEMPLATE_FILE="scripts/eventos_feriados.service.template"
OUTPUT_FILE="scripts/${SERVICE_NAME}"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ ERRO: Template não encontrado: $TEMPLATE_FILE"
    exit 1
fi

echo "🔧 Gerando arquivo de serviço systemd..."
echo "   Template: $TEMPLATE_FILE"
echo "   Output: $OUTPUT_FILE"

# Exporta variáveis necessárias para envsubst
export PROJECT_NAME_DISPLAY
export ROOT_BACKEND
export RESTART_SEC
export PROJECT_NAME

# Gera o arquivo usando envsubst
envsubst < "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "✅ Arquivo de serviço gerado com sucesso!"
echo "   Arquivo: $OUTPUT_FILE"
echo ""
echo "📋 Conteúdo gerado:"
echo "----------------------------------------"
cat "$OUTPUT_FILE"
echo "----------------------------------------"
