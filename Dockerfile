# ===================================================================
# Dockerfile - Eventos e Feriados
# ===================================================================
# Microserviço para gerenciamento de calendário institucional
# Base: Alpine Linux com Python 3.12 (imagem mínima ~50MB)
# Porta: 5000 (porta padrão para todos os microserviços no Docker)
# Nota: Sistema legado fora do Docker usa portas específicas (5045)
# ===================================================================

# Imagem base oficial do Python otimizada (Alpine para tamanho reduzido)
FROM python:3.12-alpine

# Metadados da imagem (visíveis via docker inspect)
LABEL maintainer="TCE Manutenção Predial"
LABEL app="eventos-feriados"
LABEL version="1.0.0"
LABEL description="Sistema de gerenciamento de eventos e feriados"

# Variáveis de ambiente para otimização do Python
ENV PYTHONUNBUFFERED=1 \
    # Não gera arquivos .pyc (bytecode) - reduz espaço em disco
    PYTHONDONTWRITEBYTECODE=1 \
    # Não armazena cache do pip - reduz tamanho da imagem
    PIP_NO_CACHE_DIR=1 \
    # Nome da aplicação (usado em logs e monitoramento)
    APP_NAME=eventos-feriados \
    # Porta de escuta do serviço (5000 para todos no Docker)
    APP_PORT=5000

# Instalar dependências de compilação do sistema operacional
# gcc: compilador C necessário para alguns pacotes Python
# musl-dev: biblioteca C padrão para Alpine
# libffi-dev: biblioteca FFI necessária para criptografia e SSL
RUN apk add --no-cache gcc musl-dev libffi-dev

# Define diretório de trabalho dentro do container
WORKDIR /app

# Copiar apenas requirements primeiro (aproveita cache do Docker em builds subsequentes)
# Se requirements.txt não mudar, essa camada é reutilizada
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da aplicação
# Feito depois das dependências para otimizar rebuild
COPY . .

# Instalar o pacote em modo de desenvolvimento se pyproject.toml existir
# O modo editable (-e) permite desenvolvimento local
RUN if [ -f "pyproject.toml" ]; then pip install --no-cache-dir -e .; fi

# Criar usuário não-root para segurança (princípio do menor privilégio)
# UID/GID 1000 combina com usuários padrão em muitos sistemas Linux
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Criar diretórios para dados e logs com permissões corretas
# Estrutura: /var/softwaresTCE/eventos-feriados/{dados,logs}
# Cada serviço tem sua própria pasta isolada
RUN mkdir -p /var/softwaresTCE/eventos-feriados/dados \
             /var/softwaresTCE/eventos-feriados/logs && \
    chown -R appuser:appuser /var/softwaresTCE /app

# Mudar para usuário não-root (IMPORTANTE: a partir daqui sem privilégios de root)
USER appuser

# Documentar porta exposta (não publica, apenas documentação)
EXPOSE 5000

# Health check para Docker e orchestradores (Kubernetes, Docker Swarm)
# Verifica se o serviço está respondendo HTTP
# - Verifica a cada 30 segundos
# - Espera até 10 segundos por resposta
# - Aguarda 40s após start para primeira verificação
# - 3 falhas consecutivas = unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/ || exit 1

# Comando padrão de inicialização
# waitress-serve: servidor WSGI de produção (melhor que Flask dev server)
# --host=0.0.0.0: escuta em todas as interfaces (necessário para Docker)
# --port=5000: porta padrão para todos os microserviços Flask
# EventosFeriados:app: módulo:variável da aplicação Flask
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "EventosFeriados:app"]
