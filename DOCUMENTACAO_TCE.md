# 📋 Sistema de Sincronização Automática TCE - Documentação

## 🎯 Objetivo
Implementar sincronização automática dos eventos do **Tribunal Pleno** do TCE-GO que ocorrem no **turno vespertino** (a partir das 12h), integrando-os automaticamente ao sistema de eventos.

## ✅ Funcionalidades Implementadas

### 🔄 Sincronização Automática
- **Horário**: Executada diariamente às **8h da manhã**
- **Escopo**: Mês atual e próximo mês
- **Filtros Aplicados**:
  - ✅ Apenas eventos com título iniciando em "Tribunal Pleno"
  - ✅ Apenas eventos no turno vespertino (≥ 12h)
  - ✅ Horário padronizado no sistema: **13h às 18h**
  - ✅ Local fixo: **Plenário**

### 📊 API REST Completa
Endpoints disponíveis em `/api/tce/`:

1. **POST /sincronizar** - Sincronização manual
   - Período atual: `{}`
   - Mês específico: `{"mes": 8, "ano": 2025}`

2. **GET /status** - Status da sincronização
3. **POST /configurar** - Configurar horário e ativação
4. **GET /eventos** - Listar eventos sincronizados
5. **DELETE /eventos/{id}** - Remover evento específico

### 🖥️ Interface Web Completa
- **URL**: `/sincronizacao-tce`
- **Recursos**:
  - ✅ Dashboard com status em tempo real
  - ✅ Configuração de horário e ativação
  - ✅ Sincronização manual (período atual ou mês específico)
  - ✅ Listagem de eventos com filtros
  - ✅ Remoção individual de eventos
  - ✅ Auto-refresh a cada 30 segundos

### 🏗️ Arquitetura Técnica

#### Componentes Principais:
1. **SincronizadorTCE**: Classe principal de sincronização
2. **AgendadorCLP**: Agendador atualizado com suporte ao TCE
3. **api_tce**: Blueprint com endpoints REST
4. **sincronizacao_tce.html**: Interface web responsiva

#### Fluxo de Dados:
```
API TCE (JSON) → SincronizadorTCE → GerenciadorEventos → Sistema
```

#### Identificação de Eventos:
- **ID Pattern**: `tce_tribunal_pleno_YYYYMMDD`
- **Campo Fonte**: `fonte_tce: true`
- **Horário Original**: Armazenado em `hora_original_tce`

### 🔍 Exemplo de Funcionamento

#### Dados da API TCE (agosto/2025):
```json
[
  {"dia": 4, "titulo": "Primeira Câmara: \n Ordinária às 08:00 hora(s)"},
  {"dia": 4, "titulo": "Tribunal Pleno: \n Ordinária às 10:00 hora(s)"},
  {"dia": 13, "titulo": "Tribunal Pleno: \n Ordinária às 15:00 hora(s)"},
  {"dia": 25, "titulo": "Tribunal Pleno: \n Extraordinária às 16:00 hora(s)"}
]
```

#### Eventos Filtrados e Criados:
- ✅ **13/08/2025** - Tribunal Pleno às 15h → **13h às 18h no sistema**
- ❌ 04/08/2025 - Tribunal Pleno às 10h (matutino, filtrado)

### 🛡️ Recursos de Segurança e Controle

#### Prevenção de Duplicatas:
- ✅ Verificação por ID único antes da criação
- ✅ Log detalhado de eventos já existentes

#### Limpeza Automática:
- ✅ Remove eventos TCE que não estão mais na API
- ✅ Mantém histórico de sincronizações

#### Tratamento de Erros:
- ✅ Timeout configurável (30s)
- ✅ Logs detalhados de todas as operações
- ✅ Fallback gracioso em caso de falha

### 📝 Logs e Monitoramento

#### Exemplos de Logs:
```
2025-08-22 08:31:12,247 - EventosFeriados.SincronizadorTCE - INFO - 
Dados obtidos com sucesso da API do TCE para 08/2025 - 13 eventos

2025-08-22 08:31:12,248 - EventosFeriados.SincronizadorTCE - INFO - 
Filtrados 1 eventos do Tribunal Pleno vespertinos

2025-08-22 08:31:12,347 - EventosFeriados.SincronizadorTCE - INFO - 
Evento TCE criado: Tribunal Pleno: Ordinária às 15:00 hora(s) - 13/8/2025
```

### 🧪 Testes Implementados

#### Script de Teste: `teste_sincronizacao_tce.py`
- ✅ Teste de conexão com API
- ✅ Teste de processamento de dados
- ✅ Teste de criação de eventos
- ✅ Teste do agendador
- ✅ Verificação de duplicatas

#### Resultados dos Testes:
```
🎉 Todos os testes passaram! A funcionalidade está pronta para uso.
```

### 🌐 Navegação Web
- **Menu Principal**: Novo botão "TCE" adicionado
- **Ícone**: 🏛️ Building (fa-building)
- **Posição**: Ao lado do botão "CLP"

### ⚙️ Configurações

#### Configurações Padrão:
- **Sincronização**: Habilitada
- **Horário**: 08:00 (diariamente)
- **Timeout API**: 30 segundos
- **URL Base**: `https://catalogodeservicos.tce.go.gov.br/api/pauta/datas`

#### Configurações Personalizáveis:
- ✅ Ativar/desativar sincronização
- ✅ Alterar horário de execução
- ✅ Sincronização manual a qualquer momento

### 📈 Benefícios

1. **Automatização Total**: Zero intervenção manual necessária
2. **Consistência**: Horários padronizados para melhor organização
3. **Flexibilidade**: Sincronização manual disponível
4. **Transparência**: Interface completa para monitoramento
5. **Rastreabilidade**: Logs detalhados de todas as operações
6. **Segurança**: Prevenção de duplicatas e conflitos

### 🚀 Como Usar

#### Via Interface Web:
1. Acesse `/sincronizacao-tce`
2. Configure horário se necessário
3. Execute sincronização manual ou aguarde execução automática
4. Monitore eventos na listagem

#### Via API:
```bash
# Sincronizar período atual
curl -X POST http://localhost:5045/EventosFeriados/api/tce/sincronizar

# Sincronizar mês específico
curl -X POST http://localhost:5045/EventosFeriados/api/tce/sincronizar \
  -H "Content-Type: application/json" \
  -d '{"mes": 8, "ano": 2025}'

# Verificar status
curl http://localhost:5045/EventosFeriados/api/tce/status
```

### 📋 Dependências
- ✅ `requests` (já incluída no requirements.txt)
- ✅ Flask e componentes existentes
- ✅ Bootstrap 5 (interface web)

---

## 🏁 Conclusão

A funcionalidade de sincronização automática do TCE foi implementada com sucesso, oferecendo:

- **Integração Completa** com o sistema existente
- **Interface Intuitiva** para usuários finais
- **API Robusta** para integrações
- **Monitoramento Detalhado** via logs e dashboard
- **Configuração Flexível** adaptável às necessidades

O sistema está **pronto para produção** e irá manter os eventos do Tribunal Pleno sempre atualizados automaticamente! 🎉
