# Migração do Sistema de Autenticação

## Resumo das Alterações

O sistema foi refatorado para utilizar autenticação baseada em API do HelpDesk Monitor, substituindo o arquivo `.htpasswd` do Apache.

### Novo Sistema de Autenticação

**API Externa**: `https://automacao.tce.go.gov.br/helpdeskmonitor`
- Endpoint: `/api/tecnicos/por_funcao/EVENTOS_FERIADOS`
- Retorna técnicos com a função "EVENTOS_FERIADOS"
- Somente técnicos disponíveis (não em férias) têm acesso

**Cache Persistente**: 
- Arquivo: `/var/softwaresTCE/dados/eventos_feriados/usuarios_autorizados_cache.json`
- Validade: 24 horas
- Permite acesso offline quando API indisponível

### Arquivos Criados

1. `app/utils/AuthManager.py` - Gerenciador de autenticação
2. `app/utils/auth_decorators.py` - Decoradores para rotas
3. `app/routes/api_auth.py` - API de gerenciamento de autenticação
4. `scripts/add_auth_decorators.py` - Script auxiliar (pode ser removido)

### Arquivos Modificados

1. `app/__init__.py` - Inicialização do AuthManager e registro do blueprint api_auth
2. `app/routes/web.py` - Todas as rotas protegidas com `@require_auth`
3. `app/routes/api_feriados.py` - Todas as rotas protegidas com `@require_auth_api`
4. `app/routes/api_eventos.py` - Todas as rotas protegidas com `@require_auth_api`
5. `app/routes/api_clp.py` - Todas as rotas protegidas com `@require_auth_api`
6. `app/routes/api_clp_auditorio.py` - Todas as rotas protegidas com `@require_auth_api`

## Instruções de Deploy

### 1. Remover Dependência do .htaccess

O arquivo `.htaccess` não é mais necessário para autenticação. Opções:

**Opção A - Remover completamente:**
```bash
# No servidor
cd /var/www/html/EventosFeriados
rm .htaccess
```

**Opção B - Manter apenas redirecionamentos (se houver):**
Editar `.htaccess` removendo as diretivas de autenticação:
```apache
# Remover estas linhas:
AuthType Basic
AuthName "Eventos e Feriados TCE-GO"
AuthUserFile /caminho/para/.htpasswd
Require valid-user
```

### 2. Atualizar Configuração do Apache

Arquivo: `/etc/apache2/sites-available/EventosFeriados.conf` (ou similar)

**Remover bloco de autenticação se existir:**
```apache
# REMOVER:
<Location /EventosFeriados>
    AuthType Basic
    AuthName "Eventos e Feriados"
    AuthUserFile /var/www/.htpasswd
    Require valid-user
</Location>
```

**Manter apenas o ProxyPass:**
```apache
<VirtualHost *:443>
    ServerName automacao.tce.go.gov.br
    
    # Outras configurações SSL...
    
    ProxyPass /EventosFeriados http://localhost:5001/EventosFeriados
    ProxyPassReverse /EventosFeriados http://localhost:5001/EventosFeriados
</VirtualHost>
```

Reiniciar Apache:
```bash
sudo systemctl restart apache2
```

### 3. Verificar Permissões da Pasta de Dados

```bash
# Garantir que o usuário do Flask pode escrever
sudo chown -R www-data:www-data /var/softwaresTCE/dados/eventos_feriados
sudo chmod 755 /var/softwaresTCE/dados/eventos_feriados
```

### 4. Atualizar Scripts de Deploy

Editar `scripts/deploy.sh` e remover/comentar linhas relacionadas ao htpasswd:

```bash
# REMOVER ou COMENTAR:
# cp scripts/htaccess /var/www/html/EventosFeriados/.htaccess
# htpasswd -c /var/www/.htpasswd usuario
```

### 5. Reiniciar Aplicação

```bash
sudo systemctl restart EventosFeriados.service
```

## Testando o Sistema

### 1. Verificar Status da Autenticação

```bash
curl -u seu_usuario:sua_senha \
  https://automacao.tce.go.gov.br/EventosFeriados/api/auth/status
```

Resposta esperada:
```json
{
  "autenticado": true,
  "usuario": {
    "nome": "Seu Nome",
    "usuario": "seu_usuario",
    "email": "seu@email.com"
  },
  "cache_valido": true,
  "ultima_atualizacao": "2024-01-15T10:30:00"
}
```

### 2. Testar Acesso à Interface Web

```bash
# Deve exigir autenticação HTTP Basic
curl -I https://automacao.tce.go.gov.br/EventosFeriados/
# Status: 401 Unauthorized

# Com credenciais válidas
curl -u seu_usuario:sua_senha \
  https://automacao.tce.go.gov.br/EventosFeriados/
# Status: 200 OK
```

### 3. Listar Usuários Autorizados

```bash
curl -u seu_usuario:sua_senha \
  https://automacao.tce.go.gov.br/EventosFeriados/api/auth/usuarios
```

### 4. Forçar Atualização do Cache

```bash
curl -X POST -u seu_usuario:sua_senha \
  https://automacao.tce.go.gov.br/EventosFeriados/api/auth/cache/atualizar
```

## Gerenciamento de Usuários

### Adicionar Novo Usuário

1. Acessar HelpDesk Monitor: https://automacao.tce.go.gov.br/helpdeskmonitor
2. Ir em "Técnicos" → Editar técnico
3. Adicionar a função "EVENTOS_FERIADOS" nas competências
4. Aguardar 24 horas OU forçar atualização do cache via API

### Remover Acesso de Usuário

1. No HelpDesk Monitor, remover a função "EVENTOS_FERIADOS" do técnico
2. Aguardar 24 horas OU forçar atualização do cache

### Acesso Temporário em Caso de Falha da API

Se a API do HelpDesk Monitor estiver indisponível:
- O sistema usa o cache de 24 horas
- Usuários autorizados continuam tendo acesso
- Após 24 horas sem atualização, pode ser necessário intervir manualmente

**Editar cache manualmente (emergência):**
```bash
sudo nano /var/softwaresTCE/dados/eventos_feriados/usuarios_autorizados_cache.json
```

Estrutura do cache:
```json
{
  "usuarios": [
    {
      "nome": "Nome do Usuário",
      "usuario": "login",
      "email": "email@tce.go.gov.br"
    }
  ],
  "ultima_atualizacao": "2024-01-15T10:30:00"
}
```

## Monitoramento

### Logs do Sistema

```bash
# Ver logs da aplicação
sudo journalctl -u EventosFeriados.service -f

# Ver logs específicos de autenticação
sudo grep "AUTH" /var/softwaresTCE/logs/eventos_feriados/*.log
```

### Verificar Validade do Cache

```bash
# Ver data de última atualização
ls -lh /var/softwaresTCE/dados/eventos_feriados/usuarios_autorizados_cache.json

# Ver conteúdo
cat /var/softwaresTCE/dados/eventos_feriados/usuarios_autorizados_cache.json | jq .
```

## Troubleshooting

### Problema: Usuário autorizado não consegue acessar

1. Verificar se tem a função no HelpDesk Monitor
2. Verificar se não está de férias
3. Forçar atualização do cache
4. Verificar logs da aplicação

### Problema: API do HelpDesk Monitor indisponível

1. Sistema usa cache automaticamente
2. Cache válido por 24 horas
3. Monitorar disponibilidade da API
4. Se necessário, editar cache manualmente

### Problema: Todos os usuários bloqueados

1. Verificar conectividade com API HelpDesk Monitor
2. Verificar se cache existe e está acessível
3. Verificar permissões da pasta de dados
4. Reiniciar aplicação
5. Se necessário, criar cache manualmente

## Rollback (Voltar para .htpasswd)

Se necessário voltar ao sistema anterior:

1. Restaurar configuração do Apache com autenticação
2. Restaurar arquivo `.htaccess`
3. Remover decoradores das rotas (reverter commits)
4. Reiniciar Apache e aplicação

**Não recomendado** - O novo sistema oferece:
- Gerenciamento centralizado via HelpDesk Monitor
- Cache para acesso offline
- Logs detalhados de autenticação
- API para gerenciamento programático
