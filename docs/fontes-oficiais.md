# Fontes oficiais

Regra: **nenhum dado entra em `dados/` sem constar aqui** — com URL de origem,
data de captura e checksum. Arquivos em `fontes/` são imutáveis: correção da
fonte oficial = novo arquivo + nova versão de dados.

## QBQ — Quadro Brasileiro de Qualificações

| item | valor |
|---|---|
| Página oficial | <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/quadro-brasileiro-de-qualificacoes-qbq> |
| Arquivo | `fontes/qbq/qbq-2025-03.xlsx` (original: `download.xlsx`) |
| Metadados internos | criado 2022-09-21; modificado 2025-03-18 |
| Capturado em | 2026-08-28 |
| SHA-256 | ver `fontes/README.md` e `dados/qbq/verificacao.json` |

Abas: `Layout` (dicionário de dados), `Ocupação`, `Conhecimento I` (níveis
1–5), `Conhecimento II` (níveis 6–8), `Habilidade`, `Atitude`, `Ocupações não
classificada`.

### Conceitos das habilidades

| item | valor |
|---|---|
| Página oficial | <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/quadro-brasileiro-de-qualificacoes-qbq> |
| Arquivo | `fontes/qbq/conceitos-habilidades-2025-06.pdf` (original: `tabelas-habilidades-qbq-1.pdf`) |
| Metadados internos | criado e modificado 2025-06-10 |
| Capturado em | 2026-08-28 |
| SHA-256 | ver `fontes/README.md` |

Traz a definição oficial de cada domínio, categoria e habilidade — o mesmo
conteúdo que o portal de consulta da FIPE apresenta em
<https://qbqconsulta.fipe.org.br/Conceitos>. O portal é uma aplicação web que
recusa cliente automatizado; o PDF do ministério é a mesma informação em
documento citável e arquivável, e por isso é a fonte usada (D011).

Documento correlato ainda **não** incorporado: a relação de campos de
conhecimento por área (`pdf-relacao-de-campos-de-conhecimento-por-area-1.pdf`,
modificado 2025-06-06) lista os campos de cada área, sem definições — é
estrutura de vocabulário, não conceito, e a taxonomia correspondente já vem da
planilha.

## CBO — Classificação Brasileira de Ocupações (fase 1, pendente)

- Downloads: <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/downloads>
- Histórico de alterações: <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo/servicos/historico-de-alteracoes>

## Instabilidade de URLs do gov.br

URLs do gov.br mudam com reorganizações administrativas. Por isso os arquivos
são arquivados no repositório e cada captura registra a URL vigente na data.
