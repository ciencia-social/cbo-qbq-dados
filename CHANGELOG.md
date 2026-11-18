# Changelog

## dados-2026.11.2 · schema-v0.3.0 — 2026-11-18

Mesmo dado de `dados-2026.11.1`. O conteúdo não muda: o que esta publicação acrescenta é o identificador persistente, os metadados de citação e a descrição Frictionless dos derivados.

- `.zenodo.json` e `CITATION.cff` para o depósito Zenodo e o botão de citação do GitHub, com autoria Fernandes, Wil e licença CC BY 4.0. O commit de acerto preenche os DOIs cunhados no depósito 24353525: conceito `10.5281/zenodo.24353524` e versão `10.5281/zenodo.24353525`
- `VERSAO.json` e `derivados/csv/datapackage.json`, gerados por `pipeline/derivar.py` e conferidos byte a byte no CI (D020)
- Contrato 14 no validador: a versão declarada nos quatro metadados tem de ser a versão corrente, e divergência é erro
- D019, atribuição com autoria, ano e licença em `dados/LICENSE.md`, e titular do `LICENSE` no nome legal

## dados-2026.11.1 · schema-v0.3.0 — 2026-11-17

Fase 3: perfil ocupacional da CBO.

- 174.296 atividades em 20.723 grandes áreas de competência, para 2.669 ocupações, em `dados/cbo/perfis/` — do CSV oficial capturado em 2026-11-17
- Schema `cbo-perfis`, contrato 13 no validador e as tabelas `cbo_area` e `cbo_atividade` nos derivados
- `docs/perfil-e-atitudes.md`: o eixo transversal Z da CBO ("demonstrar competências pessoais") confrontado com os vocabulários do QBQ — 79,2% das atividades do eixo não têm palavra em comum com as atitudes do QBQ, que são escala de autonomia e não catálogo de comportamento
- D017 (só o código da ocupação é chave no CSV de perfil) e D018 (sufixo sequencial para duas publicações no mesmo mês)
- Seção "Como os dados se encaixam" no README, com diagrama conceitual em Mermaid: a ocupação no centro, a classificação da CBO acima, o perfil ao lado e a qualificação do QBQ abaixo

## dados-2026.11 · schema-v0.2.0 — 2026-11-17

Fase 1: espinha enumerativa da CBO 2002.

- 10 grandes grupos, 49 subgrupos principais, 195 subgrupos, 626 famílias e 2.694 ocupações, com 7.778 sinônimos em 1.865 delas, a partir dos seis CSVs oficiais capturados em 2026-11-17
- Schemas `cbo-estrutura` e `cbo-ocupacoes`, seis contratos novos no validador e derivados CSV/SQLite da camada CBO
- Cruzamento das duas camadas na mesma chave: 25 ocupações só na CBO, 4 só no QBQ e 35 com título divergente, em `derivados/csv/cobertura-qbq-cbo.csv` e `docs/cobertura-qbq-cbo.md`, sem reconciliação (D015)
- `versao_dados` passa a indicar a publicação em que cada camada foi gerada; os arquivos do QBQ seguem em `dados-2026.08`, sem regeração (D016)
- `docs/consultas.sql`: dez consultas comentadas sobre o SQLite, da hierarquia completa ao perfil CHA com a definição oficial de cada termo

## dados-2026.08 · schema-v0.1.0 — 2026-11-17

Primeira estruturação do repositório.

- Extração completa do XLSX oficial do QBQ (modificado 2025-03-18): ocupações, competências CHA, vocabulários e não classificadas
- Conceitos oficiais das habilidades (PDF de conceitos e terminologia, modificado 2025-06-10): 96 definições de domínios, categorias e habilidades em `dados/qbq/conceitos/habilidades.json`
- JSON Schemas (draft 2020-12) e pipeline de extração/validação/derivação
- Derivados: CSV e SQLite
