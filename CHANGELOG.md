# Changelog

## dados-2026.11 · schema-v0.2.0 (não publicado)

Fase 1: espinha enumerativa da CBO 2002.

- 10 grandes grupos, 49 subgrupos principais, 195 subgrupos, 626 famílias e
  2.694 ocupações, com 7.778 sinônimos em 1.865 delas, a partir dos seis CSVs
  oficiais capturados em 2026-11-17
- Schemas `cbo-estrutura` e `cbo-ocupacoes`, seis contratos novos no validador
  e derivados CSV/SQLite da camada CBO
- Cruzamento das duas camadas na mesma chave: 25 ocupações só na CBO, 4 só no
  QBQ e 35 com título divergente, em `derivados/csv/cobertura-qbq-cbo.csv` e
  `docs/cobertura-qbq-cbo.md`, sem reconciliação (D015)
- `versao_dados` passa a indicar a publicação em que cada camada foi gerada;
  os arquivos do QBQ seguem em `dados-2026.08`, sem regeração (D016)

## dados-2026.08 · schema-v0.1.0 (não publicado)

Primeira estruturação do repositório.

- Extração completa do XLSX oficial do QBQ (modificado 2025-03-18):
  ocupações, competências CHA, vocabulários e não classificadas
- Conceitos oficiais das habilidades (PDF de conceitos e terminologia,
  modificado 2025-06-10): 96 definições de domínios, categorias e habilidades
  em `dados/qbq/conceitos/habilidades.json`
- JSON Schemas (draft 2020-12) e pipeline de extração/validação/derivação
- Derivados: CSV e SQLite
