#!/usr/bin/env python3
"""Checagens de contrato sobre dados/qbq/. Falha (exit 1) se algum contrato
for violado. Uso: python3 pipeline/validar.py"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
QBQ = RAIZ / "dados" / "qbq"

RE_CBO = re.compile(r"^\d{6}$")
erros, avisos = [], []


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def erro(msg):
    erros.append(msg)


def aviso(msg):
    avisos.append(msg)


def main():
    ocupacoes = {}
    for arq in sorted((QBQ / "ocupacoes").glob("gg-*.json")):
        doc = carregar(arq)
        for o in doc["ocupacoes"]:
            c = o["codigo"]
            # 1. formato e particionamento do código
            if not RE_CBO.match(c):
                erro(f"código inválido {c!r} em {arq.name}")
            if c[0] != doc["grande_grupo"]:
                erro(f"{c} no arquivo errado ({arq.name})")
            if c in ocupacoes:
                erro(f"código duplicado {c}")
            # 2. níveis na escala 1-8
            for k, v in o["niveis"].items():
                if v is not None and not (1 <= v <= 8):
                    erro(f"nível {k}={v} fora de 1-8 em {c}")
            ocupacoes[c] = o

    nc = carregar(QBQ / "nao-classificadas.json")
    codigos_nc = {o["codigo"] for o in nc["ocupacoes"]}

    vocab = {}
    for nome in ["conhecimentos-i", "conhecimentos-ii", "habilidades", "atitudes"]:
        doc = carregar(QBQ / "vocabularios" / f"{nome}.json")
        vocab[nome] = {nivel: {r["codigo"]: r for r in regs}
                       for nivel, regs in doc.items()
                       if isinstance(regs, list)}

    # 3. hierarquia dos vocabulários: todo pai referenciado existe
    for nome, niveis in vocab.items():
        todos = {c for regs in niveis.values() for c in regs}
        for nivel, regs in niveis.items():
            for r in regs.values():
                if "pai" in r and r["pai"] not in todos:
                    erro(f"pai {r['pai']!r} inexistente ({nome}.{nivel}.{r['codigo']})")

    itens_folha = {
        "conhecimentos-i": vocab["conhecimentos-i"]["conhecimentos"],
        "conhecimentos-ii": vocab["conhecimentos-ii"]["elementos"],
    }

    total_comp = 0
    codigos_comp = set()
    for arq in sorted((QBQ / "competencias").glob("gg-*.json")):
        doc = carregar(arq)
        for oc in doc["ocupacoes"]:
            c = oc["codigo"]
            total_comp += 1
            codigos_comp.add(c)
            # 4. integridade referencial com ocupacoes/
            if c not in ocupacoes:
                erro(f"{c} em competencias/ sem registro em ocupacoes/")
                continue
            taxo = oc["taxonomia_conhecimento"]
            # 5. exatamente uma taxonomia de conhecimento por ocupação
            if oc["conhecimentos"] and taxo not in ("conhecimentos-i", "conhecimentos-ii"):
                erro(f"{c}: taxonomia de conhecimento ambígua ou ausente: {taxo!r}")
                continue
            # 6. taxonomia coerente com o nível (I: 1-5, II: 6-8) — aviso
            nivel = ocupacoes[c]["niveis"]["conhecimento"]
            if oc["conhecimentos"] and nivel is not None:
                esperada = "conhecimentos-i" if nivel <= 5 else "conhecimentos-ii"
                if taxo != esperada:
                    aviso(f"{c}: nível de conhecimento {nivel} mas taxonomia {taxo}")
            # 7. todo item referencia código existente no vocabulário; graus 1-5
            for dim, folha in [("conhecimentos", itens_folha.get(taxo, {})),
                               ("habilidades", vocab["habilidades"]["habilidades"]),
                               ("atitudes", vocab["atitudes"]["atitudes"])]:
                vistos = set()
                for item in oc[dim]:
                    if item["codigo"] not in folha:
                        erro(f"{c}: {dim} {item['codigo']!r} fora do vocabulário")
                    # baldes "outros" (algum segmento 90/99) repetem código
                    # por desenho da fonte, com descrição inline (D009)
                    bucket = bool({"90", "99"}
                                  & set(item["codigo"].rstrip(".").split(".")))
                    if item["codigo"] in vistos and not bucket:
                        aviso(f"{c}: {dim} {item['codigo']} duplicado")
                    if bucket and not item.get("descricao"):
                        erro(f"{c}: {dim} {item['codigo']} (balde 90) sem descrição inline")
                    vistos.add(item["codigo"])
                    for g in ("profundidade", "frequencia", "importancia"):
                        v = item.get(g)
                        if v is not None and not (1 <= v <= 5):
                            erro(f"{c}: {dim}.{item['codigo']}.{g}={v} fora de 1-5")

    # 8. toda ocupação classificada tem competências (aviso se não tiver)
    for c in sorted(set(ocupacoes) - codigos_comp - codigos_nc):
        aviso(f"{c} classificada mas sem itens de competência")

    # 9. coerência das não-classificadas: constam da aba Ocupação (D008),
    #    mas sem nenhum nível e sem itens de competência
    for o in nc["ocupacoes"]:
        c = o["codigo"]
        if c not in ocupacoes:
            erro(f"{c} não classificada ausente de ocupacoes/")
            continue
        if any(v is not None for v in ocupacoes[c]["niveis"].values()):
            erro(f"{c} não classificada mas com nível preenchido")
        if c in codigos_comp:
            erro(f"{c} não classificada mas com itens de competência")

    # 10. cobertura: sem nível nenhum => deveria estar em não-classificadas.
    # Lacuna conhecida da fonte (D010): aviso, não erro.
    for c, o in sorted(ocupacoes.items()):
        if c not in codigos_nc and all(v is None for v in o["niveis"].values()):
            aviso(f"{c} sem nenhum nível e fora de nao-classificadas.json (D010)")

    print(f"ocupações: {len(ocupacoes)} | com competências: {total_comp} "
          f"| não classificadas: {nc['total']}")
    print(f"erros: {len(erros)} | avisos: {len(avisos)}")
    for m in avisos[:20]:
        print("  aviso:", m)
    if len(avisos) > 20:
        print(f"  ... e mais {len(avisos) - 20} avisos")
    for m in erros[:50]:
        print("  ERRO:", m)
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
