# qbq-dados

**O Quadro Brasileiro de Qualificações (QBQ) e a Classificação Brasileira de
Ocupações (CBO) como dados abertos, estruturados e verificáveis.**

Os dados oficiais existem — mas espalhados em planilhas XLSX, sistemas de
consulta e PDFs, sem formato canônico legível por máquina, sem histórico e sem
proveniência. Este repositório resolve isso, nos moldes do
[bncc-dados](https://github.com/bncc-dev/bncc-dados): JSON canônico com
proveniência por registro, pipeline reprodutível e derivados prontos para uso
(CSV e SQLite).

## O que tem aqui (versão `dados-2026.11.1`)

| Conjunto | Conteúdo | Onde |
|---|---|---|
| Espinha CBO | 10 grandes grupos → 49 subgrupos principais → 195 subgrupos → 626 famílias → 2.694 ocupações | `dados/cbo/estrutura/`, `dados/cbo/ocupacoes/` |
| Sinônimos CBO | 7.778 denominações alternativas, em 1.865 ocupações | embutidos na ocupação |
| Perfil ocupacional CBO | 174.296 atividades em 20.723 grandes áreas de competência, para 2.669 ocupações | `dados/cbo/perfis/` |
| Ocupações QBQ | 2.673 ocupações (2.621 com síntese, perfil ocupacional e níveis de qualificação 1–8) | `dados/qbq/ocupacoes/` |
| Competências (CHA) | ~258 mil itens de conhecimento, habilidade e atitude por ocupação, com graus de profundidade, frequência e importância (1–5) | `dados/qbq/competencias/` |
| Vocabulários | Taxonomias controladas de conhecimentos (I e II), habilidades e atitudes | `dados/qbq/vocabularios/` |
| Conceitos | 96 definições oficiais de domínios, categorias e habilidades (PDF de conceitos e terminologia) | `dados/qbq/conceitos/` |
| Não classificadas | 52 ocupações sem nível QBQ, com a justificativa oficial | `dados/qbq/nao-classificadas.json` |
| Derivados | Os mesmos dados em CSV e SQLite, gerados pelo pipeline | `derivados/` |

As duas camadas compartilham a chave (código CBO de 6 dígitos) e **divergem em
64 ocupações**: 25 existem só na CBO, 4 só no QBQ e 35 têm título diferente sob
o mesmo código. Nenhuma é reconciliada — ver
[`docs/cobertura-qbq-cbo.md`](docs/cobertura-qbq-cbo.md) e o D015.

Os perfis descritivos da CBO e o histórico de alterações são as fases
seguintes — ver roadmap abaixo.

## Uso rápido

```python
import json
# ocupações do grande grupo 3 (técnicos de nível médio)
gg3 = json.load(open("dados/qbq/ocupacoes/gg-3.json", encoding="utf-8"))
tecnico = next(o for o in gg3["ocupacoes"] if o["codigo"] == "312105")
print(tecnico["titulo"], "->", tecnico["niveis"]["qualificacao"])
```

```sql
-- qbq.sqlite (anexo do release, ou `python3 pipeline/derivar.py`):
-- do nome de mercado ao código oficial, com o nível de qualificação do QBQ
SELECT s.sinonimo, o.codigo, o.titulo, q.nivel_qualificacao
FROM cbo_sinonimo s
JOIN cbo_ocupacao o      ON o.codigo = s.ocupacao
LEFT JOIN qbq_ocupacao q ON q.codigo = o.codigo
WHERE s.sinonimo LIKE '%programador%'
ORDER BY s.sinonimo;
```

Mais dez consultas comentadas — hierarquia completa, perfil CHA com a
definição oficial de cada termo, agregados por grande grupo, divergências
entre as camadas e similaridade entre ocupações — em
[`docs/consultas.sql`](docs/consultas.sql):

```bash
sqlite3 -box derivados/qbq.sqlite < docs/consultas.sql
```

## Estrutura do repositório

```
fontes/      arquivos oficiais imutáveis, como baixados (com checksum)
schema/      JSON Schemas (draft 2020-12) que definem o contrato dos dados
dados/       dados canônicos em JSON — a fonte de verdade deste repositório
derivados/   CSV, SQLite e dump SQL gerados a partir de dados/ (nunca editar)
pipeline/    scripts que extraem, validam e derivam (ver pipeline/README.md)
docs/        modelo de dados, fontes oficiais, metodologia e versionamento
```

Pontos de modelagem que valem conhecer antes de usar (detalhes em
[docs/modelo-de-dados.md](docs/modelo-de-dados.md)):

- O **código CBO de 6 dígitos** (`"312105"`, com zero à esquerda) é a chave
  primária de tudo e será a chave de junção com a CBO na fase 1.
- O QBQ usa **duas taxonomias de conhecimento distintas**: `conhecimentos-i`
  para ocupações de nível 1–5 e `conhecimentos-ii` (com elementos, tipo CNPq)
  para níveis 6–8.
- Cobertura parcial é dado explícito: o que não tem nível QBQ está em
  `nao-classificadas.json` com a justificativa oficial.
- Registros carregam `vigencia` e `fonte` (arquivo/aba/linha da planilha
  oficial) — nada aqui é inventado, tudo é rastreável.

## Reproduzir

```bash
pip install openpyxl jsonschema
python3 pipeline/extrair_qbq.py && python3 pipeline/validar_schema.py \
  && python3 pipeline/validar.py && python3 pipeline/derivar.py
```

## Roadmap

- [x] **Fase 0-2 — QBQ**: fontes, schemas, ocupações, competências CHA,
  vocabulários e conceitos das habilidades
- [x] **Fase 1 — espinha CBO**: estrutura enumerativa completa (grandes grupos →
      ocupações → sinônimos) a partir dos CSVs oficiais da CBO
- [x] **Fase 3 — perfil ocupacional CBO**: grandes áreas de competência e
      atividades por ocupação
- [ ] **Fase 3b — Livros 1–3 em PDF**: condições gerais de exercício e
      recursos de trabalho, por família
- [ ] **Fase 4 — histórico de alterações** da CBO como dado estruturado
      (`alteracoes.json` + vigência retroativa)
- [ ] **Fase 5 — `qbq-pacotes`**: pacotes Python/R/JS para consumo

## Licenças

- **Dados** (`dados/`, `derivados/`): [CC BY 4.0](dados/LICENSE.md) — o
  conteúdo provém de atos oficiais (art. 8º, IV, Lei 9.610/1998); a
  compilação estruturada é licenciada abertamente.
- **Código** (`pipeline/`, `schema/`): [MIT](LICENSE).

Decisões de modelagem e inconsistências encontradas nas fontes ficam
registradas em [DECISOES.md](DECISOES.md).
