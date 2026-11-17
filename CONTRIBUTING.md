# Como contribuir

Há três formulários de issue, um por tipo de contribuição:

| Formulário | Quando usar |
|---|---|
| **Correção de dado** | Um registro diverge da planilha oficial |
| **Mudança normativa** | A fonte oficial mudou (nova publicação ou portaria) |
| **Derivado ou formato** | Pedido de formato de saída, campo de schema ou ajuste em `derivados/` |

Antes de abrir, confira se o caso já é um fato conhecido da fonte registrado em [`DECISOES.md`](DECISOES.md) — especialmente D008 a D010.

- **Erro nos dados?** Abra uma issue apontando o registro (`codigo`) e a divergência em relação à fonte oficial. Se a fonte oficial estiver errada, o dado permanece fiel a ela e a issue vira registro em DECISOES.md.
- **Nunca edite `dados/` ou `derivados/` à mão** — são gerados pelo pipeline. Correções acontecem nos scripts de `pipeline/` (com a decisão documentada).
- PRs de código: rode `python3 pipeline/validar_schema.py && python3 pipeline/validar.py` antes de abrir.
