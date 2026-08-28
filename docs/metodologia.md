# Metodologia

Cadeia de confiança, do documento oficial ao dado servido:

```
fonte oficial (gov.br)  →  fontes/ (imutável, checksum)
                        →  pipeline/extrair_*.py (determinístico)
                        →  dados/ (JSON canônico, proveniência por registro)
                        →  pipeline/validar_schema.py + validar.py (contratos)
                        →  derivados/ (CSV, SQLite — gerados, nunca editados)
```

Princípios (herdados do bncc-dados):

1. **Reprodutibilidade**: qualquer pessoa regenera `dados/` e `derivados/`
   rodando o pipeline sobre `fontes/`. O CI confere que o que está commitado
   é exatamente o que o pipeline produz.
2. **Proveniência**: todo registro aponta arquivo, aba e linha de origem.
3. **Sem interpretação silenciosa**: o pipeline não "conserta" a fonte.
   Normalizações são mínimas, documentadas em DECISOES.md; inconsistências
   viram registro em `verificacao.json`, não correção invisível.
4. **Honestidade estrutural**: entidades distintas na fonte permanecem
   distintas no dado (ex.: as duas taxonomias de conhecimento, D004).

Pendente (fase 2+): `verificar.py` com conferência caractere a caractere
entre `dados/` e `fontes/`, nos moldes do `verificacao.json` do bncc-dados.
