# Modelo de dados

O diagrama conceitual do modelo está no [README](../README.md#como-os-dados-se-encaixam); esta página detalha cada entidade, seus campos e os contratos verificados.

## Visão geral

Duas camadas sobre a mesma chave — o **código CBO de 6 dígitos**:

1. **CBO**: espinha enumerativa (grande grupo → subgrupo principal → subgrupo
   → família → ocupação → sinônimos). Os perfis descritivos por família ficam
   para a fase 3.
2. **QBQ** (esta versão): para cada ocupação classificada, níveis de
   qualificação (1–8) e itens de competência CHA com graus (1–5).

## Entidades — CBO

### Estrutura (`dados/cbo/estrutura/*.json`)

Os quatro níveis superiores, um arquivo por nível, com hierarquia por prefixo
do código:

| arquivo | registros | código |
|---|---|---|
| `grandes-grupos.json` | 10 | 1 dígito |
| `subgrupos-principais.json` | 49 | 2 dígitos |
| `subgrupos.json` | 195 | 3 dígitos |
| `familias.json` | 626 | 4 dígitos |

Cada registro: `codigo` (string, zero à esquerda), `titulo`, `pai` (ausente no
topo) e `fonte` `{arquivo, linha}`. O `pai` é o prefixo do código, verificado
contra o nível acima — na captura de 2026-11-17 não há um único órfão.

### Ocupação CBO (`dados/cbo/ocupacoes/gg-N.json`)

As 2.694 ocupações, particionadas pelo primeiro dígito do código, mesma
convenção da camada QBQ — os dois arquivos do mesmo grande grupo ficam lado a
lado, e o diff de qualquer um deles continua revisável.

| campo | conteúdo |
|---|---|
| `codigo` | CBO 6 dígitos, string (D001) |
| `titulo` | título oficial |
| `familia` | código de 4 dígitos, o pai |
| `sinonimos[]` | `titulo` e `fonte` de cada sinônimo (7.778 no total, em 1.865 ocupações) |
| `vigencia` | `{status, desde, ate}` — registros nunca são deletados |
| `fonte` | `{arquivo, linha}` no CSV oficial |

Sinônimos ficam embutidos na ocupação, e não em arquivo próprio, porque são
atributo dela: todo sinônimo da fonte referencia ocupação existente, e a
proveniência de cada um aponta para o CSV de sinônimos.

### Perfil ocupacional (`dados/cbo/perfis/gg-N.json`)

O que a ocupação faz, como a CBO descreve: as grandes áreas de competência
(GAC) e, dentro de cada uma, as atividades. 174.296 atividades em 2.669
ocupações, particionadas por grande grupo como as demais camadas.

| campo | conteúdo |
|---|---|
| `codigo` | CBO 6 dígitos — a única chave confiável do arquivo de origem (D017) |
| `areas[]` | `sigla` (A–O, Y, Z), `nome` e `atividades[]` |
| `atividades[]` | `numero` como publicado, com lacunas (D017), e `descricao` |
| `fonte` | `{arquivo, linha}` da primeira linha da ocupação no CSV |

A sigla da área **não é taxonomia controlada**: é ordenação dentro da
ocupação. A mesma letra `A` nomeia 588 áreas diferentes ao longo do arquivo,
porque cada ocupação tem o seu conjunto. Duas siglas fogem à regra e são
transversais: `Z` ("demonstrar competências pessoais"), presente em 2.666 das
2.669 ocupações, e `Y`, presente em 535 e com cinco nomes distintos
(comunicar-se, trabalhar com segurança, trabalhar com biossegurança e outros).

As 25 ocupações da espinha sem perfil não são aleatórias: 9 são das forças
armadas, 15 são mandatos eletivos e cargos de direção do poder público
(senador a vice-prefeito) e 1 é `373220`. A fonte não descreve atividades para
mandato político nem para carreira militar.

O eixo `Z` **não** é equivalente da dimensão "atitudes" do QBQ, que é escala de
autonomia e supervisão: ver [perfil-e-atitudes.md](perfil-e-atitudes.md) para a
medida e os termos que existem em uma fonte e não na outra.

## Entidades — QBQ

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

### Conceitos (`dados/qbq/conceitos/<dimensao>.json`)

Definição oficial de cada termo do vocabulário da dimensão, extraída do PDF de
conceitos e terminologia do QBQ — outra fonte, com data e checksum próprios, e
por isso camada separada do vocabulário (D011). Hoje existe
`habilidades.json`, cobrindo 3 domínios, 9 categorias e 84 habilidades.

| campo | conteúdo |
|---|---|
| `dimensao` | vocabulário a que os códigos se referem (ex.: `habilidades`) |
| `fonte` | caminho do arquivo em `fontes/` |
| `<nivel>[]` | `codigo` (do vocabulário), `termo` (rótulo como grafado no PDF), `conceito` (definição transcrita) |
| `divergencias[]` | termos cuja grafia difere entre PDF e planilha; nenhuma das duas é corrigida (D013) |

Baldes "outros" (segmento `90`) não constam: o PDF não os define (D012). O
`conceito` de `01.01` (Comunicação) repete literalmente o do domínio pai —
assim está na fonte, e o validador avisa em vez de corrigir.

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
10. Conceitos: todo termo não-balde do vocabulário tem definição oficial, e
    todo conceito aponta para termo existente (D011, D012)
11. CBO: código com o número de dígitos do nível, único, com `pai` igual ao
    prefixo e existente no nível acima; ocupação no arquivo do seu grande
    grupo, com família existente; sinônimos sem repetição
12. Cruzamento QBQ × CBO: as diferenças entre as duas camadas viram aviso e
    tabela (`derivados/csv/cobertura-qbq-cbo.csv`), nunca correção silenciosa
    (D015) — ver [cobertura-qbq-cbo.md](cobertura-qbq-cbo.md)
13. Perfil: ocupação com perfil existe na espinha e está no arquivo do seu
    grande grupo; siglas de área únicas e ordenadas; numeração de atividade
    não decrescente. Lacunas, repetição e ocupação sem perfil viram aviso —
    são fatos da fonte (D017)
