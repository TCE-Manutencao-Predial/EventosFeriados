# =============================================================================
# MAKEFILE - EVENTOS E FERIADOS
# =============================================================================
# Versão: 2.0.0
# =============================================================================

# Carrega variáveis do .env.deploy se existir
ifneq (,$(wildcard .env.deploy))
    include .env.deploy
endif

# Fallback para variáveis se .env.deploy não existir
APP_NAME ?= eventos_feriados
PORT ?= 5045
SERVICE_NAME ?= eventos_feriados.service

# Exporta variáveis para subprocessos
export APP_NAME
export PORT
export SERVICE_NAME

VENV_PYTHON=.venv/bin/python
VENV_PIP=.venv/bin/pip


# =============================================================================
# CONFIGURAÇÃO E SETUP
# =============================================================================

# Cria a venv e instala as dependências
setup:
	python -m venv .venv
	./$(VENV_PIP) install -r requirements.txt
	./$(VENV_PIP) install .

# Valida configurações do .env.deploy
validate:
	@echo "🔍 Validando configurações..."
	@python tools/validate-env.py

# Cria .env.deploy a partir do template
reset-env:
	@if [ -f ".env.deploy" ]; then \
		echo "⚠️  Arquivo .env.deploy já existe!"; \
		echo "   Deseja sobrescrever? (isso apagará suas configurações atuais)"; \
		echo "   Se sim, delete manualmente e execute 'make reset-env' novamente"; \
	else \
		echo "📝 Criando .env.deploy a partir do template..."; \
		cp .env.deploy.template .env.deploy; \
		echo "✅ Arquivo .env.deploy criado!"; \
		echo "💡 Configure as variáveis sensíveis antes do deploy"; \
	fi


# =============================================================================
# DESENVOLVIMENTO
# =============================================================================

# Executa o projeto
run:
	./.venv/bin/waitress-serve --host 127.0.0.1 --port $(PORT) $(APP_NAME):app

# Apaga a venv
clear_venv:
	@if [ -d ".venv" ]; then rm -r .venv; fi


# =============================================================================
# DEPLOY
# =============================================================================

# Realiza o deploy
deploy:
	sudo chmod +x ./scripts/deploy.sh
	./scripts/deploy.sh

undeploy:
	sudo chmod +x ./scripts/undeploy.sh
	./scripts/undeploy.sh


# =============================================================================
# SERVIÇO SYSTEMD
# =============================================================================

service-reload:
	sudo systemctl daemon-reload

service-restart:
	$(MAKE) service-reload
	sudo setenforce 0
	sudo systemctl restart $(SERVICE_NAME)
	sudo setenforce 1

service-status:
	systemctl status $(SERVICE_NAME)

service-start:
	sudo systemctl start $(SERVICE_NAME)

service-stop:
	sudo systemctl stop $(SERVICE_NAME)

service-enable:
	sudo systemctl enable $(SERVICE_NAME)

service-disable:
	sudo systemctl disable $(SERVICE_NAME)


# =============================================================================
# LOGS
# =============================================================================

log:
	sudo journalctl -u $(SERVICE_NAME)

log-follow:
	sudo journalctl -u $(SERVICE_NAME) -f

print_log:
	sudo journalctl -u $(SERVICE_NAME) > service.log


# =============================================================================
# HELP
# =============================================================================

.PHONY: help setup validate reset-env run clear_venv deploy undeploy \
        service-reload service-restart service-status service-start service-stop \
        service-enable service-disable log log-follow print_log

help:
	@echo "Comandos disponíveis:"
	@echo "  make setup           - Cria venv e instala dependências"
	@echo "  make validate        - Valida configurações do .env.deploy"
	@echo "  make reset-env       - Cria .env.deploy a partir do template"
	@echo "  make run             - Executa servidor localmente"
	@echo "  make deploy          - Faz deploy no servidor"
	@echo "  make undeploy        - Remove deploy do servidor"
	@echo "  make service-status  - Status do serviço"
	@echo "  make service-restart - Reinicia o serviço"
	@echo "  make log-follow      - Acompanha logs em tempo real"
