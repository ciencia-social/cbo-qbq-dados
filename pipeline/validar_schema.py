#!/usr/bin/env python3
"""Valida dados/qbq/*.json contra os JSON Schemas de schema/.
Uso: python3 pipeline/validar_schema.py  (dependência: jsonschema>=4.18)"""
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError:
    sys.exit("jsonschema>=4.18 é necessário: pip install jsonschema")

RAIZ = Path(__file__).resolve().parent.parent


def registro_local():
    """Resolve $refs entre schemas pelos arquivos locais de schema/,
    sem acesso à rede (os $id são apenas identificadores)."""
    recursos = []
    for arq in (RAIZ / "schema").glob("*.json"):
        with open(arq, encoding="utf-8") as f:
            doc = json.load(f)
        recurso = Resource.from_contents(doc)
        recursos.append((doc.get("$id", arq.name), recurso))
        recursos.append((arq.name, recurso))
    return Registry().with_resources(recursos)

MAPA = {
    "schema/cbo-estrutura.schema.json": "dados/cbo/estrutura/*.json",
    "schema/cbo-ocupacoes.schema.json": "dados/cbo/ocupacoes/gg-*.json",
    "schema/cbo-perfis.schema.json": "dados/cbo/perfis/gg-*.json",
    "schema/qbq-ocupacoes.schema.json": "dados/qbq/ocupacoes/gg-*.json",
    "schema/qbq-competencias.schema.json": "dados/qbq/competencias/gg-*.json",
    "schema/qbq-vocabularios.schema.json": "dados/qbq/vocabularios/*.json",
    "schema/qbq-conceitos.schema.json": "dados/qbq/conceitos/*.json",
    "schema/qbq-nao-classificadas.schema.json": "dados/qbq/nao-classificadas.json",
}


def main():
    falhas = 0
    registro = registro_local()
    for schema_rel, padrao in MAPA.items():
        with open(RAIZ / schema_rel, encoding="utf-8") as f:
            validador = Draft202012Validator(json.load(f), registry=registro)
        arquivos = sorted(RAIZ.glob(padrao))
        if not arquivos:
            print(f"AVISO: nenhum arquivo para {padrao}")
            continue
        for arq in arquivos:
            with open(arq, encoding="utf-8") as f:
                doc = json.load(f)
            erros = list(validador.iter_errors(doc))
            for e in erros[:10]:
                caminho = "/".join(str(p) for p in e.absolute_path)
                print(f"ERRO {arq.relative_to(RAIZ)}: /{caminho}: {e.message[:120]}")
            falhas += len(erros)
    print(f"falhas de schema: {falhas}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
