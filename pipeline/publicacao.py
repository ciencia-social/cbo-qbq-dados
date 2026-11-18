"""Constantes da publicação corrente.

`VERSAO.json` e `derivados/csv/datapackage.json` são gerados a partir daqui.
A data é a da release, não o relógio: um carimbo de `datetime.now()` quebraria
a regeneração byte a byte conferida no CI.

Os DOI vêm do depósito Zenodo de `dados-2026.11.2` (registro 24353525).
`DOI_CONCEITO` é o da obra contínua; `DOI_VERSAO` fixa essa publicação.
`VERSAO.json` grava os dois. O `doi` do CITATION.cff é o de versão.
"""
import json
from pathlib import Path

VERSAO_DADOS = "dados-2026.11.2"
VERSAO_SCHEMA = "schema-v0.3.0"
DATA_RELEASE = "2026-11-18"

DOI_CONCEITO = "10.5281/zenodo.24353524"
DOI_VERSAO = "10.5281/zenodo.24353525"

REPOSITORIO = "https://github.com/ciencia-social/cbo-qbq-dados"
SITE = "https://cbo.ciencia.social"

LICENCA_DADOS = "CC-BY-4.0"
LICENCA_CODIGO = "MIT"

# Vocabulário do Zenodo para a mesma licença CC BY 4.0. O campo de lá não
# aceita o identificador SPDX.
LICENCA_ZENODO = "cc-by-4.0"

AUTOR_ZENODO = "Fernandes, Wil"
AUTOR_FAMILY = "Fernandes"
AUTOR_GIVEN = "Wil"
ORCID = "0009-0008-3477-5521"

# Chaves e ordem das contagens que validar.py imprime e VERSAO.json repete.
CHAVES_CONTAGEM = (
    "cbo_grandes_grupos",
    "cbo_subgrupos_principais",
    "cbo_subgrupos",
    "cbo_familias",
    "cbo_ocupacoes",
    "cbo_sinonimos",
    "cbo_atividades",
    "qbq_ocupacoes",
    "qbq_com_competencias",
    "qbq_nao_classificadas",
    "qbq_conceitos",
)


def _versao_unica(arquivos, camada):
    if not arquivos:
        raise ValueError(f"camada {camada} sem arquivos em dados/")
    versoes = {}
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            doc = json.load(f)
        versao = doc.get("versao_dados")
        if not versao:
            raise ValueError(f"{arq} sem versao_dados")
        versoes.setdefault(versao, 0)
        versoes[versao] += 1
    if len(versoes) != 1:
        detalhe = ", ".join(f"{v} ({n} arquivos)" for v, n in sorted(versoes.items()))
        raise ValueError(f"camada {camada} declara mais de uma versao_dados: {detalhe}")
    return next(iter(versoes))


def camadas_nos_dados(raiz):
    """Versão em que cada camada foi gerada (D016), lida dos arquivos.

    As três chaves são as que o serviço já usa: espinha da CBO, perfil
    ocupacional e QBQ. Perfil é separado da espinha de propósito — os dois
    estão sob dados/cbo/ e não compartilham a versão.
    """
    raiz = Path(raiz)
    cbo = raiz / "dados" / "cbo"
    qbq = raiz / "dados" / "qbq"
    espinha = [cbo / "verificacao.json"]
    espinha += sorted((cbo / "estrutura").glob("*.json"))
    espinha += sorted((cbo / "ocupacoes").glob("*.json"))
    perfil = sorted((cbo / "perfis").glob("*.json"))
    qbq_arqs = sorted(qbq.rglob("*.json"))
    return {
        "cbo_espinha": _versao_unica(espinha, "cbo_espinha"),
        "cbo_perfil": _versao_unica(perfil, "cbo_perfil"),
        "qbq": _versao_unica(qbq_arqs, "qbq"),
    }
