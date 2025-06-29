# Sistema de Prevenção de Duplicatas de Feriados

## Problema Identificado

O sistema estava criando feriados duplicados quando um feriado era ao mesmo tempo municipal, estadual e nacional (por exemplo, Natal, Independência do Brasil, etc.). Isso acontecia porque:

1. A biblioteca `holidays` retornava feriados nacionais e estaduais juntos
2. Os feriados municipais eram adicionados separadamente
3. Não havia verificação de duplicatas por data

## Solução Implementada

### Hierarquia de Feriados

Foi estabelecida uma hierarquia clara para classificação dos feriados:

1. **Nacional** (prioridade 4) - Feriados válidos em todo o território nacional
2. **Estadual** (prioridade 3) - Feriados válidos apenas no estado (Goiás)
3. **Municipal** (prioridade 2) - Feriados válidos apenas no município (Goiânia)
4. **Customizado** (prioridade 1) - Feriados personalizados adicionados pelo usuário

### Mudanças Implementadas

#### 1. GerenciadorFeriados.py

**Método `_inicializar_feriados_padrao()` reformulado:**
- Primeiro carrega feriados nacionais
- Depois carrega feriados estaduais (apenas se não existir nacional na mesma data)
- Por último carrega feriados municipais (apenas se não existir nacional ou estadual na mesma data)
- Usa um dicionário temporário com chave (ano, mês, dia) para evitar duplicatas

**Novos métodos adicionados:**
- `_verificar_feriado_existente()`: Verifica se já existe feriado em uma data específica
- `_determinar_tipo_hierarquia()`: Determina qual tipo de feriado deve prevalecer
- `remover_duplicatas()`: Remove duplicatas de uma lista existente, mantendo apenas o de maior hierarquia

**Método `adicionar_feriado()` aprimorado:**
- Verifica duplicatas antes de adicionar
- Respeita hierarquia definida
- Substitui feriados de menor prioridade por outros de maior prioridade
- Impede adição de feriados de menor prioridade quando já existe um de maior prioridade

#### 2. api_feriados.py

**Novo endpoint adicionado:**
- `POST /feriados/remover-duplicatas`: Remove duplicatas existentes no sistema

### Como Usar

#### Remover Duplicatas Existentes

```bash
curl -X POST http://localhost:5000/feriados/remover-duplicatas
```

Resposta:
```json
{
  "sucesso": true,
  "mensagem": "Processo concluído. 5 duplicatas removidas.",
  "duplicatas_removidas": 5
}
```

#### Adicionar Novo Feriado

Ao adicionar um feriado, o sistema verificará automaticamente:

```bash
curl -X POST http://localhost:5000/feriados \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Dia do Trabalhador",
    "dia": 1,
    "mes": 5,
    "ano": 2025,
    "hora_inicio": "00:00",
    "hora_fim": "23:59",
    "tipo": "municipal"
  }'
```

Se já existir um feriado nacional ou estadual no dia 1º de maio, o sistema retornará erro:
```json
{
  "erro": "Já existe um feriado nacional na data 01/05/2025: Dia do Trabalhador"
}
```

### Comportamentos

1. **Inicialização sem duplicatas**: Ao inicializar feriados padrão, não haverá duplicatas
2. **Adição respeitando hierarquia**: Novos feriados só são adicionados se não violarem a hierarquia
3. **Substituição por prioridade**: Feriados de maior prioridade podem substituir outros de menor prioridade
4. **Remoção de duplicatas**: Endpoint disponível para limpar duplicatas existentes

### Exemplos de Feriados por Tipo

- **Nacional**: Natal, Ano Novo, Independência do Brasil, Dia do Trabalhador
- **Estadual**: Feriados específicos de Goiás
- **Municipal**: Aniversário de Goiânia (24/10), Nossa Senhora Auxiliadora (24/05)
- **Customizado**: Feriados personalizados adicionados pelo usuário

### Logs

O sistema registra todas as operações:
- Duplicatas removidas
- Feriados substituídos
- Tentativas de adicionar feriados duplicados
