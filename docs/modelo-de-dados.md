# Modelo de dados

## Visão geral

Duas camadas sobre a mesma chave — o **código CBO de 6 dígitos**:

1. **CBO** (fase 1, pendente): espinha enumerativa (grande grupo → subgrupo
   principal → subgrupo → família → ocupação → sinônimos) e perfis descritivos
   por família.
2. **QBQ** (esta versão): para cada ocupação classificada, níveis de
   qualificação (1–8) e itens de competência CHA com graus (1–5).

## Entidades

### Ocupação (`dados/qbq/ocupacoes/gg-N.json`)

Particionado pelo primeiro dígito do código (grande grupo CBO), para diffs
revisáveis. Cada registro:

| campo | conteúdo |
|---|---|
| `codigo` | CBO 6 dígitos, string, zero à esquerda (D001) |
| `titulo` | título oficial da ocupação |
| `sintese` | síntese do perfil ocupacional |
| `perfil_ocupacional` | perfil ocupacional descritivo completo |
| `niveis.conhecimento/habilidade/atitude/qualificacao` | escala 1–8 |
| `vigencia` | `{status, desde, ate}` — nunca deletamos registros |
| `fonte` | `{arquivo, aba, linha}` na planilha oficial |

### Competências (`dados/qbq/competencias/gg-N.json`)

Por ocupação: `taxonomia_conhecimento` (qual das duas taxonomias se aplica,
ver D004) e três listas de itens que **referenciam códigos dos vocabulários**:

- `conhecimentos[]`: `codigo`, `profundidade`, `frequencia`, `importancia` (1–5)
- `habilidades[]`: `codigo`, `frequencia`, `importancia`
- `atitudes[]`: `codigo`, `importancia`
- `linha`: linha da planilha-fonte (proveniência por item)
- `descricao`: presente nos itens de balde "outros" (código com segmento
  `90`/`99`), onde o conteúdo real está na descrição da linha e o código pode
  se repetir — e em itens cuja grafia na fonte diverge da canônica (D009)

### Vocabulários (`dados/qbq/vocabularios/*.json`)

Taxonomias controladas, com hierarquia via campo `pai`:

| arquivo | hierarquia | usada por |
|---|---|---|
| `conhecimentos-i.json` | domínio → área → campo → conhecimento | ocupações nível 1–5 |
| `conhecimentos-ii.json` | área → campo → conhecimento → elemento | ocupações nível 6–8 |
| `habilidades.json` | domínio → categoria → habilidade | todas |
| `atitudes.json` | categoria → atitude | todas |

Códigos `*.90` significam "outros" (nota da aba Layout). É o vocabulário
controlado que habilita consultas transversais ("todas as ocupações que
exigem ESTATÍSTICA com importância ≥ 4").

### Não classificadas (`dados/qbq/nao-classificadas.json`)

Cobertura parcial é dado: ocupações CBO sem nível QBQ, com a justificativa
oficial (militares, dirigentes eleitos etc.). Contrato: nenhuma delas pode
aparecer em `ocupacoes/`.

### Verificação (`dados/qbq/verificacao.json`)

Relatório gerado pela extração: checksum da fonte, contagens por conjunto,
divergências de grafia nos vocabulários (D005) e avisos de valores fora de
escala (D006).

## Escalas oficiais (aba Layout do XLSX)

- **Níveis** (ocupação): 1 a 8 — conhecimento, habilidade, atitude e o nível
  de qualificação agregado.
- **Graus** (item CHA): 1 a 5 — profundidade (só conhecimentos), frequência
  de uso (conhecimentos e habilidades) e importância (todos).

## Contratos verificados no CI (pipeline/validar.py)

1. Código com 6 dígitos, único, no arquivo do seu grande grupo
2. Níveis em 1–8; graus em 1–5
3. Hierarquia dos vocabulários íntegra (todo `pai` existe)
4. Toda ocupação em `competencias/` existe em `ocupacoes/`
5. Exatamente uma taxonomia de conhecimento por ocupação
6. Taxonomia coerente com o nível (I ⇔ 1–5, II ⇔ 6–8)
7. Todo item CHA referencia código existente no vocabulário; baldes `90`
   têm `descricao` inline obrigatória (D009)
8. Não-classificadas coerentes: níveis todos nulos e zero competências (D008)
9. Cobertura total: ocupação sem nenhum nível está em `nao-classificadas.json`
