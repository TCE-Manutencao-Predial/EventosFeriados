# 🎯 PLANO DE REFATORAÇÃO - EVENTOS E FERIADOS v2.0.0

## 📋 Informações Básicas

**Microserviço:** eventos-feriados  
**Porta Atual:** 5045 (hardcoded)  
**Padrão Atual:** Configurações hardcoded + variáveis de ambiente parciais  
**Padrão Destino:** 12-factor app com `.env.deploy`  
**Complexidade:** MÉDIA  
**Tempo Estimado:** 4-6 horas  

**Referências:**
- ✅ ChatGPT (concluído)
- ✅ RFID (concluído)  
- ✅ Controle-NFs (concluído)

---

## 🔍 Análise do Estado Atual

### Configurações Hardcoded Identificadas

**Em `eventos_feriados.py`:**
- `port=5045` (linha 12)
- `debug=True` (linha 12)

**Em `makefile`:**
- `APP_NAME=eventos_feriados` (linha 1)
- `PORT=5045` (linha 2)

**Em `app/config.py`:**
- `DATA_DIR = '/var/softwaresTCE/dados/eventos_feriados'` (linha 11)
- `LOG_DIR = '/var/softwaresTCE/logs/eventos_feriados'` (linha 38)
- `ROUTES_PREFIX = '/EventosFeriados'` (linha 35)
- `SECRET_KEY = 'eventos_feriados_secret_key_2024'` (linha 13 de __init__.py)
- **CLP_CONFIG** (linhas 57-80):
  - `API_BASE_URL` (parcialmente configurável)
  - `CLP_IP = '172.17.85.104'`
  - `AUTH_USER = 'eventosferiados'`
  - `AUTH_PASS = 'WzPcMMFU'` ⚠️ **SENHA HARDCODED!**
  - `TIMEOUT`, `RETRY_COUNT`, `SYNC_TIMES`, etc.

**Em `app/__init__.py`:**
- Importa de `app.config` (precisa migrar para `app.settings`)

### Estrutura de Diretórios
```
eventos-feriados/
├── .env.example          ← EXISTE (mas não usado)
├── .flaskenv             ← Verificar se é usado
├── eventos_feriados.py   ← Hardcoded port
├── makefile              ← Hardcoded APP_NAME, PORT
├── app/
│   ├── __init__.py       ← Importa config
│   ├── config.py         ← TUDO HARDCODED + SENHA!
│   ├── routes/
│   └── utils/
├── scripts/
│   ├── config.sh         ← Verificar
│   ├── deploy.sh         ← Verificar
│   ├── run.sh            ← Verificar
│   └── undeploy.sh
└── docs/
```

---

## 🎯 Objetivos da Refatoração

1. **SEGURANÇA CRÍTICA:** Remover senha hardcoded `AUTH_PASS = 'WzPcMMFU'`
2. **Configuração:** Centralizar tudo em `.env.deploy`
3. **Padrão:** Alinhar com ChatGPT/RFID/Controle-NFs
4. **Manutenibilidade:** Facilitar deployment em diferentes ambientes
5. **Flexibilidade:** Permitir configuração CLP por ambiente

---

## 📝 TAREFAS - CHECKLIST

### Fase 1: Configuração Base (3 tarefas)

- [ ] **1.1** Criar `.env.deploy.template` com 30+ variáveis:
  - Identificação (PROJECT_NAME, SERVICE_NAME, APP_NAME, PORT=5045)
  - Caminhos (ROOT_BACKEND, ROOT_DATA, ROOT_LOGS)
  - Flask (SECRET_KEY, ROUTES_PREFIX, DEBUG)
  - CLP (API_BASE_URL, CLP_IP, AUTH_USER, AUTH_PASS, TIMEOUT, etc.)
  - Git (GIT_REPO_NAME, GIT_REPO_OWNER, GIT_REPO_URL)
  - Deploy (RESTART_SEC, AUTO_HABILITAR_SERVICO)

- [ ] **1.2** Criar `app/settings.py`:
  - Carrega `.env.deploy` com python-dotenv
  - Validação de variáveis obrigatórias
  - Exporta todas as constantes
  - Funções `ensure_directories()`, `setup_logging()`
  - CLP_CONFIG como dict configurável

- [ ] **1.3** Arquivar `app/config.py`:
  - Mover para `docs/legacy/config.py.obsoleto`
  - Criar wrapper em `app/config.py` re-exportando de settings
  - Compatibilidade total com código existente

### Fase 2: Scripts de Deploy (3 tarefas)

- [ ] **2.1** Refatorar `scripts/config.sh`:
  - Carregar `.env.deploy` com validação
  - Listar variáveis obrigatórias
  - Mensagens claras de erro

- [ ] **2.2** Criar `scripts/eventos_feriados.service.template`:
  - Template systemd com variáveis `${VAR}`
  - User=tcego, Group=tcego
  - WorkingDirectory=${ROOT_BACKEND}
  - Restart=always, RestartSec=${RESTART_SEC}

- [ ] **2.3** Criar `scripts/generate-service.sh`:
  - Gera service usando `envsubst`
  - Valida template
  - Preview do resultado

### Fase 3: Código Python (3 tarefas)

- [ ] **3.1** Atualizar `eventos_feriados.py`:
  - Importar PORT e DEBUG de `app.settings`
  - Remover hardcoded `port=5045`
  - Usar `app.run(debug=DEBUG, port=PORT)`

- [ ] **3.2** Atualizar `app/__init__.py`:
  - Mudar imports de `app.config` para `app.settings`
  - SECRET_KEY de settings
  - ROUTES_PREFIX de settings
  - Manter lógica intacta

- [ ] **3.3** Verificar outros módulos:
  - `app/utils/*.py` - imports de config
  - Atualizar todos para usar `app.settings`

### Fase 4: Build e Deploy (3 tarefas)

- [ ] **4.1** Atualizar `makefile`:
  - Carregar `.env.deploy` com `include`
  - Exportar APP_NAME, PORT, SERVICE_NAME
  - Novos targets: validate, reset-env, service-*, log-follow
  - Remover hardcoded APP_NAME/PORT

- [ ] **4.2** Atualizar `scripts/deploy.sh`:
  - Usar `generate-service.sh`
  - Criar ROOT_DATA, ROOT_LOGS com tcego:tcego
  - Remover hardcoded paths

- [ ] **4.3** Atualizar `scripts/run.sh`:
  - Carregar `config.sh`
  - Usar variáveis do `.env.deploy`
  - Executar waitress diretamente (sem Makefile)

### Fase 5: Validação e Documentação (3 tarefas)

- [ ] **5.1** Criar `tools/validate-env.py`:
  - Validar todas as variáveis obrigatórias
  - Validações específicas (PORT 1-65535, paths, etc.)
  - Mascarar valores sensíveis (AUTH_PASS, SECRET_KEY)
  - Relatório detalhado

- [ ] **5.2** Atualizar `.gitignore`:
  - Adicionar `.env.deploy`
  - Manter `.env.example` versionado

- [ ] **5.3** Atualizar documentação:
  - README.md → v2.0.0, instruções de configuração
  - CHANGELOG.md → documentar mudanças breaking
  - Criar REFATORACAO_COMPLETA_v2.0.0.md

---

## 🔧 Detalhes Técnicos

### Variáveis do .env.deploy.template

```bash
# =============================================================================
# CONFIGURAÇÃO DO EVENTOS E FERIADOS - TEMPLATE
# =============================================================================

# --- Identificação do Projeto ---
PROJECT_NAME=eventos_feriados
PROJECT_NAME_DISPLAY="Sistema de Eventos e Feriados"
SERVICE_NAME=eventos_feriados.service
APP_NAME=eventos_feriados

# --- Porta do Servidor ---
PORT=5045

# --- Caminhos do Sistema ---
ROOT_SOFTWARES=/var/softwaresTCE
ROOT_BACKEND=/var/softwaresTCE/eventos_feriados
ROOT_DATA=/var/softwaresTCE/dados/eventos_feriados
ROOT_LOGS=/var/softwaresTCE/logs/eventos_feriados

# --- Flask ---
SECRET_KEY=eventos_feriados_secret_key_CHANGE_THIS_IN_PRODUCTION
ROUTES_PREFIX=/EventosFeriados
DEBUG=false

# --- Configuração CLP ---
CLP_API_URL=https://automacao.tce.go.gov.br/scadaweb/api
CLP_IP=172.17.85.104
CLP_AUTH_USER=eventosferiados
CLP_AUTH_PASS=WzPcMMFU
CLP_TIMEOUT=30
CLP_RETRY_COUNT=3
CLP_SYNC_TIMES=07:00,20:00
CLP_MAX_FERIADOS=20
CLP_SYNC_ENABLED=true

# --- Git ---
GIT_REPO_NAME=eventos-feriados
GIT_REPO_OWNER=TCE-Manutencao-Predial
GIT_REPO_URL=https://github.com/TCE-Manutencao-Predial/eventos-feriados.git

# --- Deploy ---
RESTART_SEC=10
AUTO_HABILITAR_SERVICO=true
```

### Estrutura do app/settings.py

```python
"""
settings.py - Configuração Centralizada do Sistema Eventos e Feriados
Padrão: 12-factor app
Versão: 2.0.0
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env.deploy
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / '.env.deploy'

if not ENV_FILE.exists():
    print(f"❌ ERRO: Arquivo .env.deploy não encontrado")
    print(f"💡 Execute: make reset-env")
    sys.exit(1)

load_dotenv(ENV_FILE)

# Variáveis obrigatórias
PROJECT_NAME = os.getenv('PROJECT_NAME', 'eventos_feriados')
PORT = int(os.getenv('PORT', '5045'))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY')
ROUTES_PREFIX = os.getenv('ROUTES_PREFIX', '/EventosFeriados')

# Paths
ROOT_BACKEND = os.getenv('ROOT_BACKEND')
ROOT_DATA = os.getenv('ROOT_DATA')
ROOT_LOGS = os.getenv('ROOT_LOGS')
DATA_DIR = ROOT_DATA
LOG_DIR = ROOT_LOGS
LOG_FILE = f"{LOG_DIR}/eventos_feriados.log"

# CLP Configuration
CLP_CONFIG = {
    'API_BASE_URL': os.getenv('CLP_API_URL'),
    'CLP_IP': os.getenv('CLP_IP'),
    'AUTH_USER': os.getenv('CLP_AUTH_USER'),
    'AUTH_PASS': os.getenv('CLP_AUTH_PASS'),
    'TIMEOUT': int(os.getenv('CLP_TIMEOUT', '30')),
    'RETRY_COUNT': int(os.getenv('CLP_RETRY_COUNT', '3')),
    'SYNC_TIMES': os.getenv('CLP_SYNC_TIMES', '07:00,20:00').split(','),
    'MAX_FERIADOS': int(os.getenv('CLP_MAX_FERIADOS', '20')),
    'SYNC_ENABLED': os.getenv('CLP_SYNC_ENABLED', 'true').lower() == 'true',
    'STATUS_FILE': f"{ROOT_DATA}/clp_status.json",
    'BACKUP_FILE': f"{ROOT_DATA}/clp_backup.json",
    # Tags (manter as estruturas complexas)
    'TAGS_FERIADOS': {'DIA': 'N33', 'MES': 'N34'},
    'TAGS_EVENTOS_PLENARIO': {...},
    'TAGS_EVENTOS_AUDITORIO': {...}
}

def ensure_directories():
    """Cria diretórios necessários"""
    for dir_path in [ROOT_DATA, ROOT_LOGS]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configura sistema de logging"""
    # ... implementação
```

---

## ⚠️ Pontos de Atenção

1. **SENHA HARDCODED:** `CLP_AUTH_PASS` está exposta no código!
2. **CLP_CONFIG Complexo:** Estruturas aninhadas (TAGS_*) precisam migrar corretamente
3. **Múltiplos Gerenciadores:** GerenciadorFeriados, GerenciadorEventos, etc. usam config
4. **Integração CLP:** Sistema crítico - testar bem após migração
5. **Agendador:** AgendadorCLP precisa configurações do CLP_CONFIG
6. **Porta 5045:** Não confundir com outras portas! (controle_nfs=4242, chatgpt=5001, etc.)

---

## 🎓 Lições dos Deploys Anteriores

**Do ChatGPT/RFID/Controle-NFs:**
- ✅ Bash quoting correto para valores com espaços
- ✅ Paths absolutos (não usar expansão `${VAR}`)
- ✅ python-dotenv não expande variáveis
- ✅ Criar diretórios no deploy, não no import
- ✅ Permissões tcego:tcego para dados/logs
- ✅ Exportar variáveis explicitamente no Makefile
- ✅ run.sh executa waitress diretamente (não via make)
- ✅ Wrapper config.py para compatibilidade
- ✅ Validador com máscaras de segurança

---

## 📊 Complexidades Específicas

### Configuração CLP (Alta Complexidade)
```python
# Migração de estruturas aninhadas
'TAGS_EVENTOS_PLENARIO': {
    'DIA': 'N60',
    'MES': 'N61',
    'HORA_INICIO': 'N62',
    # ... mais 10+ campos
}
```

**Solução:** Manter estruturas hardcoded em settings.py, mas valores de autenticação/URLs configuráveis.

### Múltiplos Módulos Utils
- GerenciadorFeriados
- GerenciadorEventos
- GerenciadorHistorico
- IntegracaoCLP
- AgendadorCLP
- etc.

**Solução:** Todos migram de `app.config` para `app.settings`

---

## ✅ Critérios de Sucesso

- [ ] Nenhuma senha ou token hardcoded
- [ ] PORT=5045 configurável via .env.deploy
- [ ] `make validate` passa sem erros
- [ ] `make deploy` funciona em produção
- [ ] Agendador CLP continua funcionando
- [ ] Integração CLP mantida
- [ ] Sistema de notificações OK
- [ ] Logs em ROOT_LOGS correto
- [ ] Dados em ROOT_DATA correto
- [ ] Serviço systemd inicia corretamente
- [ ] Documentação completa

---

## 📅 Estimativa de Execução

| Fase | Tarefas | Tempo Estimado |
|------|---------|----------------|
| Fase 1 | 3 | 90 min |
| Fase 2 | 3 | 60 min |
| Fase 3 | 3 | 90 min |
| Fase 4 | 3 | 60 min |
| Fase 5 | 3 | 60 min |
| **TOTAL** | **15** | **6 horas** |

---

## 🚀 Próximos Passos

1. Aguardar aprovação do plano
2. Executar Fase 1 (Configuração Base)
3. Executar Fase 2 (Scripts)
4. Executar Fase 3 (Código Python)
5. Executar Fase 4 (Build/Deploy)
6. Executar Fase 5 (Validação/Docs)
7. Deploy em produção
8. Monitorar por 24h

---

**Status:** 🔴 AGUARDANDO APROVAÇÃO  
**Criado em:** 14/11/2025  
**Autor:** GitHub Copilot
