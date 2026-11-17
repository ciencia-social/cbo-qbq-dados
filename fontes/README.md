# Fontes

Arquivos oficiais **imutáveis**, exatamente como baixados. Nunca editar.
Todo arquivo novo entra com registro em `docs/fontes-oficiais.md`.

| arquivo | origem | capturado em | sha256 |
|---|---|---|---|
| `qbq/qbq-2025-03.xlsx` | gov.br/trabalho-e-emprego → QBQ → download (original `download.xlsx`) | 2026-08-28 | `585d5f90b512e30c93c7ecdb539450458aa98f46366fb9c0aa9a02ea6eb66524` |
| `qbq/conceitos-habilidades-2025-06.pdf` | gov.br/trabalho-e-emprego → QBQ → tabelas de habilidades (original `tabelas-habilidades-qbq-1.pdf`) | 2026-08-28 | `59b3b836f736f1cb202fd00fdf1b1e97d13ddf3bc057bc1f8719c7ccd1faa973` |
| `cbo/cbo2002-grande-grupo.csv` | gov.br/trabalho-e-emprego → CBO → downloads | 2026-11-17 | `cad67f4971a9ff1eb47129c1f43e733b792c034b1f9fd18476bed3b14e55da4f` |
| `cbo/cbo2002-subgrupo-principal.csv` | idem | 2026-11-17 | `0e74bcd22818be529eb1c737ecc463c034d730194ecd1f241723c617cc6853b7` |
| `cbo/cbo2002-subgrupo.csv` | idem | 2026-11-17 | `f9c7dd232da09330e248b42c9e2002ba7a1379de7c5479d6e0dbccf62f3fec69` |
| `cbo/cbo2002-familia.csv` | idem | 2026-11-17 | `76a56fa0d2d5844c0f470cca74a560c48400455dff4ec306fb2a2672f8c0f928` |
| `cbo/cbo2002-ocupacao.csv` | idem | 2026-11-17 | `ad6d51d5d139125b15ea746464b2a39fa832ae295cdb6aa63dc7eddf2d2bed00` |
| `cbo/cbo2002-sinonimo.csv` | idem | 2026-11-17 | `d49e700161106e0da7e69083db97d0a94ec6d7feed3ab874da5a0cd175a1ace1` |
| `cbo/cbo2002-perfilocupacional.csv` | idem | 2026-11-17 | `01f2f99f0831d57fae27b90c57d112432350bee80fe55e969f969d4d9d6f7a91` |
| `cbo/pagina-downloads-2026-11-17.html` | página de downloads da CBO, como evidência das URLs vigentes na captura | 2026-11-17 | (evidência de origem, não é dado) |

Arquivos da CBO mantêm o nome original: ao contrário do XLSX e do PDF do QBQ,
as respostas HTTP não trazem data de modificação e os CSVs não têm metadado
interno de versão, então não há data de documento para carregar no nome
(D014). A rastreabilidade fica na data de captura e no checksum.
