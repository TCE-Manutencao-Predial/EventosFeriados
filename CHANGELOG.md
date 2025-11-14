# CHANGELOG - Sistema de Eventos e Feriados

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [2.0.0] - 2025-11-14

### 🎯 Refatoração Completa - 12-Factor App

Migração de configurações hardcoded para padrão `.env.deploy` (12-factor app methodology).

### ✨ Adicionado

- **.env.deploy.template** - Template de configuração com 40+ variáveis
- **app/settings.py** - Módulo centralizado de configurações
- **app/config.py** - Wrapper para compatibilidade com código legado
- **scripts/eventos_feriados.service.template** - Template systemd dinâmico
- **scripts/generate-service.sh** - Gerador de arquivo de serviço
- **tools/validate-env.py** - Validador de configurações com 189 linhas
- **docs/legacy/** - Diretório para arquivos obsoletos
- **docs/PLANO_REFATORACAO_v2.0.0.md** - Plano de refatoração completo

### 🔧 Modificado

- **eventos_feriados.py** - Usa PORT e DEBUG de settings
- **app/__init__.py** - Importa SECRET_KEY de settings
- **scripts/config.sh** - Carrega .env.deploy com validação
- **scripts/deploy.sh** - Cria ROOT_DATA/ROOT_LOGS, usa generate-service.sh
- **scripts/run.sh** - Executa waitress diretamente (não usa Makefile)
- **makefile** - Carrega .env.deploy, novos targets (validate, reset-env, help)
- **.gitignore** - Adiciona .env.deploy e melhorias gerais
- **README.md** - Atualizado para v2.0.0 com instruções de configuração

### 🔒 Segurança

- **CRÍTICO:** Removida senha hardcoded `CLP_AUTH_PASS = 'WzPcMMFU'`
- Removido `SECRET_KEY` hardcoded do Flask
- Removido `WHATSAPP_API_TOKEN` hardcoded
- Todos os tokens/senhas agora em `.env.deploy` (não versionado)

### 📦 Configurações Externalizadas

**Porta:** 5045 (configurável via PORT)  
**CLP Plenário:** IP 172.17.85.104 (configurável via CLP_IP)  
**CLP Auditório:** IP 172.17.85.123 (configurável via CLP_AUDITORIO_IP)  

**Variáveis principais:**
- `PORT` - Porta do servidor (5045)
- `SECRET_KEY` - Chave secreta Flask
- `CLP_AUTH_PASS` - Senha do CLP (antes hardcoded!)
- `WHATSAPP_API_TOKEN` - Token WhatsApp
- `ROOT_DATA` - Diretório de dados persistentes
- `ROOT_LOGS` - Diretório de logs
- E mais 30+ configurações...

### 🗂️ Arquivado (Legado)

- `docs/legacy/config.py.obsoleto` - Arquivo original movido

### 🎓 Aprendizados Aplicados

Lições dos deploys anteriores (ChatGPT, RFID, Controle-NFs):
- ✅ Wrapper config.py para compatibilidade total
- ✅ Validador robusto com máscaras de segurança
- ✅ Makefile com exports explícitos
- ✅ run.sh executa waitress diretamente
- ✅ Diretórios criados com permissões tcego:tcego
- ✅ Paths absolutos (não usa expansão ${VAR})

### 🚀 Migração

**Para atualizar de v1.x para v2.0.0:**

1. Execute `make reset-env` para criar `.env.deploy`
2. Configure todas as variáveis no `.env.deploy` (**especialmente senhas!**)
3. Execute `make validate` para validar
4. Execute `make deploy` para aplicar mudanças
5. Verifique logs com `make log-follow`

### ⚠️ Breaking Changes

- **PORT:** Não mais hardcoded em `eventos_feriados.py`
- **CLP_AUTH_PASS:** Deve estar em `.env.deploy`
- **SECRET_KEY:** Deve estar em `.env.deploy`
- **Diretórios:** ROOT_DATA e ROOT_LOGS devem estar configurados

### 📋 Compatibilidade

- ✅ Código legado continua funcionando (wrapper config.py)
- ✅ Imports existentes não precisam ser alterados
- ✅ app/utils/* continuam funcionando normalmente
- ✅ CLP_CONFIG e CLP_AUDITORIO_CONFIG preservados
- ✅ Sistema de agendamento mantido

---

## [1.x.x] - Versões Anteriores

Versões anteriores com configurações hardcoded.

### Principais problemas:
- ❌ Senha do CLP em código-fonte
- ❌ SECRET_KEY hardcoded
- ❌ Porta 5045 hardcoded
- ❌ Paths hardcoded em /var/softwaresTCE

---

**Padrão seguido:** [Keep a Changelog](https://keepachangelog.com/)  
**Versionamento:** [Semantic Versioning](https://semver.org/)
