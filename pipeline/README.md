# Pipeline

Transforma as fontes oficiais em `fontes/` nos dados canônicos de `dados/`, valida os contratos e gera os `derivados/`. Qualquer pessoa reproduz o dataset executando, na raiz do repositório:

```bash
python3 pipeline/extrair_cbo.py       # CSVs oficiais da CBO -> dados/cbo/*.json
python3 pipeline/extrair_perfis.py    # perfil ocupacional -> dados/cbo/perfis/
python3 pipeline/extrair_qbq.py       # XLSX oficial do QBQ -> dados/qbq/*.json
python3 pipeline/extrair_conceitos.py # PDF de conceitos -> dados/qbq/conceitos/
python3 pipeline/validar_schema.py    # JSON Schemas (draft 2020-12)
python3 pipeline/validar.py           # contratos: integridade referencial, escalas, particionamento
python3 pipeline/derivar.py           # dados/ -> derivados/ (CSV, SQLite, datapackage) e VERSAO.json
```

A ordem importa: `extrair_perfis.py` confere cada ocupação contra a espinha gerada por `extrair_cbo.py`, e `extrair_conceitos.py` usa os rótulos de `dados/qbq/vocabularios/habilidades.json` como âncoras de busca no PDF, então depende de `extrair_qbq.py` ter rodado. Ele falha com exit 1 se algum termo esperado não for localizado — completude verificada, em vez de dado silenciosamente incompleto.

`derivar.py` também escreve `derivados/csv/datapackage.json`, no padrão Frictionless, e `VERSAO.json` na raiz. Os dois são gerados, como os CSVs: o CI recusa divergência byte a byte. A versão, a data da release e os DOI vêm de `pipeline/publicacao.py`, nunca de `datetime.now()` (D020).

Dependências: Python 3.10+, `openpyxl` (extração da planilha), `pypdfium2` (extração do PDF de conceitos) e `jsonschema>=4.18` (validação de formato).

Fases futuras (ver roadmap no README da raiz): `extrair_cbo.py` (CSVs oficiais da CBO), `extrair_alteracoes.py` (histórico de alterações) e `verificar.py` (conferência caractere a caractere entre dados/ e fontes/, nos moldes do bncc-dados).
