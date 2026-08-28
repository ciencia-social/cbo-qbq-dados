# Pipeline

Transforma as fontes oficiais em `fontes/` nos dados canônicos de `dados/`,
valida os contratos e gera os `derivados/`. Qualquer pessoa reproduz o
dataset executando, na raiz do repositório:

```bash
python3 pipeline/extrair_qbq.py     # XLSX oficial do QBQ -> dados/qbq/*.json
python3 pipeline/validar_schema.py  # JSON Schemas (draft 2020-12)
python3 pipeline/validar.py         # contratos: integridade referencial, escalas, particionamento
python3 pipeline/derivar.py         # dados/ -> derivados/ (CSV + SQLite)
```

Dependências: Python 3.10+, `openpyxl` (extração) e `jsonschema>=4.18`
(validação de formato).

Fases futuras (ver roadmap no README da raiz): `extrair_cbo.py` (CSVs oficiais
da CBO), `extrair_alteracoes.py` (histórico de alterações) e `verificar.py`
(conferência caractere a caractere entre dados/ e fontes/, nos moldes do
bncc-dados).
