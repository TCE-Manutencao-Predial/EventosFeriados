# Integração com CLP (Controlador Lógico Programável)

## Visão Geral

O sistema foi expandido para incluir funcionalidades de sincronização com CLPs externos, permitindo:

- Escrita sequencial de dados de feriados e eventos
- Sincronização automática em horários programados (7h00 e 18h00)
- Verificação de integridade dos dados
- Interface web para monitoramento e controle
- Leitura e comparação de dados do CLP

## Arquitetura

### Componentes Principais

1. **SincronizadorCLP** (`app/utils/SincronizadorCLP.py`)
   - Classe principal responsável pela comunicação com a API externa
   - Gerencia escrita sequencial de dados
   - Controla status e backup dos dados
   - Implementa padrão Singleton

2. **AgendadorCLP** (`app/utils/AgendadorCLP.py`)
   - Executa sincronizações automáticas em horários programados
   - Executa em thread separada (daemon)
   - Monitora continuamente os horários de sincronização

3. **API Endpoints** (`app/routes/api_clp.py`)
   - Novos endpoints para controle da sincronização
   - Interface REST para operações manuais
   - Status e monitoramento

4. **Interface Web** (`app/templates/sincronizacao_clp.html`)
   - Dashboard para monitoramento em tempo real
   - Controles manuais de sincronização
   - Visualização de logs e status

## Configuração

### Configurações Hard-coded

O sistema utiliza configurações específicas para o TCE Goiás:

```python
# app/config.py
CLP_CONFIG = {
    'API_BASE_URL': 'https://automacao.tce.go.gov.br/scadaweb/api',
    'CLP_IP': '172.17.85.104',  # IP do CLP Térreo B1
    'AUTH_USER': 'eventosferiados',  # Usuário para autenticação básica
    'AUTH_PASS': 'WzPcMMFU',  # Senha para autenticação básica
    # ... outras configurações
}
```

### 🔐 Autenticação

Todas as operações com a API do CLP utilizam HTTP Basic Authentication:
- **Usuário**: `eventosferiados`
- **Senha**: `WzPcMMFU`

### Variáveis de Ambiente (Opcionais)

Para customizações, você pode usar o arquivo `.env`:

```bash
# URL base da API do CLP (já configurado)
CLP_API_URL=https://automacao.tce.go.gov.br/scadaweb/api

# IP do CLP (já configurado)
CLP_IP=172.17.85.104

# Configurações de timeout
CLP_TIMEOUT=30
CLP_RETRY_COUNT=3

# Sincronização automática
CLP_SYNC_ENABLED=true
CLP_SYNC_TIMES=07:00,18:00

# Configurações de lote
CLP_MAX_ITEMS_PER_BATCH=50
```

### URL da API Externa

A URL da API externa deve ser configurada na variável `CLP_API_URL`. O sistema espera os seguintes endpoints no CLP:

- `GET /status` - Verificação de conectividade
- `GET /ler-dados` - Leitura dos dados atuais
- `POST /escrever-dados` - Escrita sequencial de dados

## Funcionamento

### Sincronização Automática

O sistema executa sincronização automática nos horários configurados (padrão: 7h00 e 18h00):

1. Verifica conectividade com o CLP
2. Prepara dados do ano atual (apenas ano corrente)
3. Faz backup dos dados
4. Escreve dados sequencialmente (feriados primeiro, depois eventos)
5. Verifica integridade comparando dados escritos
6. Atualiza status e logs

### Sincronização Manual

Através da interface web ou API:

1. Acesse `/EventosFeriados/sincronizacao-clp`
2. Use o botão "Sincronizar Agora"
3. Monitore o progresso em tempo real
4. Visualize logs de atividade

### Formato dos Dados

Os dados são enviados no formato:

```json
{
  "tipo": "feriado" | "evento",
  "sequencia": 0,
  "dados": {
    "dia": 25,
    "mes": 12,
    "nome": "Natal",
    "tipo": "nacional"  // apenas para feriados
    // ou
    "hora_inicio": 800,  // 08:00 como inteiro
    "hora_fim": 1200,    // 12:00 como inteiro
    "local": "Auditório Nobre"  // apenas para eventos
  }
}
```

## Endpoints da API

### Status e Controle

- `GET /api/clp/sincronizacao/status` - Status da sincronização
- `POST /api/clp/sincronizacao/executar` - Executa sincronização manual
- `GET /api/clp/conectividade` - Verifica conectividade
- `GET /api/clp/dados-clp` - Lê dados do CLP
- `GET /api/clp/agendador/status` - Status do agendador automático

### Dados Operacionais

- `GET /api/clp/hoje` - Status do dia atual
- `GET /api/clp/data/{dia}/{mes}/{ano}` - Status de data específica
- `GET /api/clp/calendario/{mes}/{ano}` - Calendário resumido
- `GET /api/clp/proximo-evento` - Próximo evento
- `POST /api/clp/verificar-disponibilidade` - Verifica disponibilidade de local

## Monitoramento

### Interface Web

Acesse `/EventosFeriados/sincronizacao-clp` para:

- Visualizar status da conexão em tempo real
- Executar sincronização manual
- Monitorar logs de atividade
- Comparar dados do sistema vs CLP
- Verificar horários de sincronização automática

### Logs

Os logs são salvos em:
- Console da aplicação
- Arquivo `app/logs/eventos_feriados.log`
- Interface web (logs em tempo real)

### Status de Sincronização

O sistema mantém status detalhado em `app/dados/clp_status.json`:

```json
{
  "ultima_sincronizacao": "2025-01-07T10:30:00",
  "ultima_tentativa": "2025-01-07T10:30:00",
  "status": "sincronizado",
  "dados_sincronizados": 45,
  "clp_disponivel": true,
  "versao_dados": 1,
  "erros": []
}
```

## Tratamento de Erros

### Conectividade
- Timeout configurável (padrão: 30s)
- Retry automático (padrão: 3 tentativas)
- Logs detalhados de erros de conexão

### Integridade de Dados
- Verificação pós-escrita
- Comparação de contadores
- Rollback em caso de falha crítica

### Recuperação
- Backup automático antes de cada sincronização
- Status persistente entre reinicializações
- Continuidade após falhas temporárias

## Limitações

1. **Apenas Ano Atual**: O CLP só aceita dados do ano corrente
2. **Escrita Sequencial**: Não suporta escrita em lote (arrays)
3. **Formato Inteiro**: Horários devem ser convertidos para formato HHMM
4. **Tamanho de Strings**: Nomes limitados a 50 caracteres, locais a 30

## Próximos Passos

1. **Configurar URL da API**: Fornecer a URL real da API do CLP
2. **Testes de Integração**: Validar comunicação com CLP real
3. **Ajustes de Formato**: Adaptar formato conforme especificação do CLP
4. **Otimizações**: Melhorar performance conforme necessidade
5. **Monitoramento Avançado**: Alertas e notificações

## Segurança

- Validação de dados antes do envio
- Timeout para evitar travamentos
- Logs de auditoria completos
- Backup automático para recuperação
