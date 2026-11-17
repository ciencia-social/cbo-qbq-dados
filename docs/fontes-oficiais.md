# Fontes oficiais

Regra: **nenhum dado entra em `dados/` sem constar aqui** — com URL de origem, data de captura e checksum. Arquivos em `fontes/` são imutáveis: correção da fonte oficial = novo arquivo + nova versão de dados.

## QBQ — Quadro Brasileiro de Qualificações

| item | valor |
|---|---|
| Página oficial | <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/quadro-brasileiro-de-qualificacoes-qbq> |
| Arquivo | `fontes/qbq/qbq-2025-03.xlsx` (original: `download.xlsx`) |
| Metadados internos | criado 2022-09-21; modificado 2025-03-18 |
| Capturado em | 2026-08-28 |
| SHA-256 | ver `fontes/README.md` e `dados/qbq/verificacao.json` |

Abas: `Layout` (dicionário de dados), `Ocupação`, `Conhecimento I` (níveis 1–5), `Conhecimento II` (níveis 6–8), `Habilidade`, `Atitude`, `Ocupações não classificada`.

### Conceitos das habilidades

| item | valor |
|---|---|
| Página oficial | <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/quadro-brasileiro-de-qualificacoes-qbq> |
| Arquivo | `fontes/qbq/conceitos-habilidades-2025-06.pdf` (original: `tabelas-habilidades-qbq-1.pdf`) |
| Metadados internos | criado e modificado 2025-06-10 |
| Capturado em | 2026-08-28 |
| SHA-256 | ver `fontes/README.md` |

Traz a definição oficial de cada domínio, categoria e habilidade — o mesmo conteúdo que o portal de consulta da FIPE apresenta em
<https://qbqconsulta.fipe.org.br/Conceitos>. O portal é uma aplicação web que recusa cliente automatizado; o PDF do ministério é a mesma informação em documento citável e arquivável, e por isso é a fonte usada (D011).

Documento correlato ainda **não** incorporado: a relação de campos de conhecimento por área (`pdf-relacao-de-campos-de-conhecimento-por-area-1.pdf`, modificado 2025-06-06) lista os campos de cada área, sem definições — é estrutura de vocabulário, não conceito, e a taxonomia correspondente já vem da planilha.

## CBO — Classificação Brasileira de Ocupações

- Downloads: <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/downloads>
- Histórico de alterações: <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/historico-de-alteracoes>

### Espinha enumerativa (CBO 2002)

Seis CSVs, todos em `cp1252`, delimitador `;`, colunas `CODIGO` e `TITULO`:

| arquivo | registros | nível |
|---|---|---|
| `cbo2002-grande-grupo.csv` | 10 | 1 dígito |
| `cbo2002-subgrupo-principal.csv` | 49 | 2 dígitos |
| `cbo2002-subgrupo.csv` | 195 | 3 dígitos |
| `cbo2002-familia.csv` | 626 | 4 dígitos |
| `cbo2002-ocupacao.csv` | 2.694 | 6 dígitos |
| `cbo2002-sinonimo.csv` | 7.778 | sinônimos, por código de ocupação |

Capturados em 2026-11-17; checksums em `fontes/README.md`. A página de downloads vigente na captura está arquivada junto, como evidência das URLs (D014) — as respostas HTTP não trazem `Last-Modified`.

### Perfil ocupacional (CBO 2002)

| item | valor |
|---|---|
| Arquivo | `fontes/cbo/cbo2002-perfilocupacional.csv` |
| Registros | 174.296 (2.669 ocupações) |
| Colunas | `COD_GRANDE_GRUPO`, `COD_SUBGRUPO_PRINCIPAL`, `COD_SUBGRUPO`, `COD_FAMILIA`, `COD_OCUPACAO`, `SGL_GRANDE_AREA`, `NOME_GRANDE_AREA`, `COD_ATIVIDADE`, `NOME_ATIVIDADE` |
| Capturado em | 2026-11-17 |
| SHA-256 | ver `fontes/README.md` |

Uma grande área de competência (GAC) agrupa as atividades de uma ocupação; as siglas `Y` e `Z` são eixos transversais, presentes em quase toda ocupação. As 25 ocupações da espinha sem perfil são todas do grande grupo 0 (forças armadas, policiais e bombeiros militares) — lacuna da fonte, não do dataset.

O download deste arquivo chegou truncado na primeira tentativa (3 MB de 17,6 MB, conexão interrompida pelo servidor). A conferência de integridade é o `Content-Length` da resposta mais o checksum registrado; refazer a captura exige repetir as duas.

Ainda **não** incorporados, previstos para fases seguintes: os Livros 1–3 em PDF (condições gerais de exercício e recursos de trabalho, por família), as tábuas de conversão (`publico-geral.zip`, `usuario-medio.zip`) e os PDFs anuais de alterações (2012, 2013, 2016, 2018, 2021, 2022 e 2023).

## Instabilidade de URLs do gov.br

URLs do gov.br mudam com reorganizações administrativas. Por isso os arquivos são arquivados no repositório e cada captura registra a URL vigente na data.
