#!/usr/bin/env python3
"""Checagens de contrato sobre dados/ (camadas CBO e QBQ). Falha (exit 1)
se algum contrato
for violado. Uso: python3 pipeline/validar.py"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
QBQ = RAIZ / "dados" / "qbq"

RE_CBO = re.compile(r"^\d{6}$")
erros, avisos = [], []


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def normalizar_titulo(s):
    """Título sem acento, caixa ou pontuação, para comparar grafias entre
    camadas sem acusar diferença onde só muda a forma."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def erro(msg):
    erros.append(msg)


def aviso(msg):
    avisos.append(msg)


NIVEIS_CBO = [("grandes-grupos", 1), ("subgrupos-principais", 2),
              ("subgrupos", 3), ("familias", 4)]


def validar_cbo():
    """Contratos da espinha enumerativa (dados/cbo/): formato e unicidade dos
    códigos, hierarquia por prefixo e sinônimos. Devolve as ocupações da CBO,
    usadas depois no cruzamento com o QBQ."""
    CBO = RAIZ / "dados" / "cbo"

    codigos = {}
    for nome, digitos in NIVEIS_CBO:
        doc = carregar(CBO / "estrutura" / f"{nome}.json")
        vistos = set()
        for it in doc["itens"]:
            c = it["codigo"]
            # 1. formato do código no nível
            if len(c) != digitos or not c.isdigit():
                erro(f"cbo/{nome}: código {c!r} não tem {digitos} dígito(s)")
            if c in vistos:
                erro(f"cbo/{nome}: código {c} repetido")
            vistos.add(c)
        if doc["total"] != len(doc["itens"]):
            erro(f"cbo/{nome}: total declarado {doc['total']} != {len(doc['itens'])}")
        codigos[nome] = vistos

    # 2. hierarquia: o pai é o prefixo do código e existe no nível acima
    for (filho, _), (pai_nivel, digitos_pai) in zip(NIVEIS_CBO[1:], NIVEIS_CBO[:-1]):
        for it in carregar(CBO / "estrutura" / f"{filho}.json")["itens"]:
            esperado = it["codigo"][:digitos_pai]
            if it.get("pai") != esperado:
                erro(f"cbo/{filho}: {it['codigo']} declara pai {it.get('pai')!r}, "
                     f"esperado {esperado!r}")
            elif esperado not in codigos[pai_nivel]:
                erro(f"cbo/{filho}: {it['codigo']} sem pai {esperado} em {pai_nivel}")

    ocupacoes, sinonimos = {}, 0
    for arq in sorted((CBO / "ocupacoes").glob("gg-*.json")):
        doc = carregar(arq)
        for o in doc["ocupacoes"]:
            c = o["codigo"]
            # 3. formato e particionamento por grande grupo
            if not RE_CBO.match(c):
                erro(f"cbo: código inválido {c!r} em {arq.name}")
            if c[0] != doc["grande_grupo"]:
                erro(f"cbo: {c} no arquivo errado ({arq.name})")
            if c in ocupacoes:
                erro(f"cbo: ocupação {c} duplicada")
            ocupacoes[c] = o
            # 4. família é o prefixo de 4 dígitos e existe
            if o["familia"] != c[:4]:
                erro(f"cbo: {c} declara família {o['familia']!r}, esperado {c[:4]!r}")
            elif o["familia"] not in codigos["familias"]:
                erro(f"cbo: {c} sem família {o['familia']} em familias.json")
            # 5. sinônimos: sem repetição e sem repetir o próprio título
            vistos = set()
            for s in o["sinonimos"]:
                t = s["titulo"]
                if t in vistos:
                    aviso(f"cbo: {c} repete o sinônimo {t!r}")
                if t.casefold() == o["titulo"].casefold():
                    aviso(f"cbo: {c} tem sinônimo igual ao próprio título ({t!r})")
                vistos.add(t)
                sinonimos += 1
            # 6. vigência coerente
            if o["vigencia"]["status"] == "vigente" and o["vigencia"]["ate"] is not None:
                erro(f"cbo: {c} vigente mas com data final de vigência")
        if doc["total"] != len(doc["ocupacoes"]):
            erro(f"cbo/{arq.name}: total declarado {doc['total']} != {len(doc['ocupacoes'])}")

    return codigos, ocupacoes, sinonimos


def main():
    cbo_niveis, cbo_ocupacoes, cbo_sinonimos = validar_cbo()

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

    # 11. conceitos (D011): cobertura e integridade referencial contra o
    #     vocabulário da mesma dimensão. Baldes "outros" não têm definição
    #     oficial no PDF (D012) e por isso não devem aparecer aqui.
    total_conceitos = 0
    for arq in sorted((QBQ / "conceitos").glob("*.json")):
        doc = carregar(arq)
        dim = doc["dimensao"]
        if dim not in vocab:
            erro(f"conceitos/{arq.name}: dimensão {dim!r} sem vocabulário correspondente")
            continue
        todos_conceitos = {c["codigo"]: c["conceito"]
                           for nivel in vocab[dim] for c in doc.get(nivel, [])}
        total_conceitos += len(todos_conceitos)
        for nivel, termos in vocab[dim].items():
            conceituados = {c["codigo"]: c["conceito"] for c in doc.get(nivel, [])}
            for cod, conceito in conceituados.items():
                if cod not in termos:
                    erro(f"conceitos/{arq.name}: {nivel} {cod} fora do vocabulário")
                if not conceito.strip():
                    erro(f"conceitos/{arq.name}: {nivel} {cod} com conceito vazio")
                pai = termos.get(cod, {}).get("pai")
                if pai and todos_conceitos.get(pai) == conceito:
                    aviso(f"conceitos/{arq.name}: {cod} repete a definição do pai "
                          f"{pai} — o PDF as traz idênticas")
            for cod in termos:
                balde = "90" in cod.split(".")
                if balde and cod in conceituados:
                    erro(f"conceitos/{arq.name}: balde {cod} com conceito (D012)")
                if not balde and cod not in conceituados:
                    erro(f"conceitos/{arq.name}: {nivel} {cod} sem conceito oficial")
        for d in doc.get("divergencias", []):
            aviso(f"conceitos/{arq.name}: grafia do termo {d['codigo']} difere entre PDF "
                  f"({d['termo_pdf']!r}) e planilha ({d['termo_planilha']!r}) (D013)")

    # 12. cruzamento QBQ × CBO (D015): as duas camadas vêm de capturas
    #     diferentes da mesma classificação, então as diferenças são fato das
    #     fontes, não defeito do dataset. Ficam como aviso agregado; a lista
    #     completa é derivados/csv/cobertura-qbq-cbo.csv.
    so_cbo = sorted(set(cbo_ocupacoes) - set(ocupacoes))
    so_qbq = sorted(set(ocupacoes) - set(cbo_ocupacoes))
    if so_cbo:
        aviso(f"{len(so_cbo)} ocupações da espinha da CBO sem registro no QBQ "
              f"(ex.: {', '.join(so_cbo[:3])}) — D015")
    if so_qbq:
        aviso(f"{len(so_qbq)} ocupações do QBQ ausentes da espinha da CBO "
              f"({', '.join(so_qbq)}) — D015")
    divergentes = [c for c in sorted(set(ocupacoes) & set(cbo_ocupacoes))
                   if normalizar_titulo(ocupacoes[c]["titulo"])
                   != normalizar_titulo(cbo_ocupacoes[c]["titulo"])]
    if divergentes:
        aviso(f"{len(divergentes)} ocupações com título diferente entre QBQ e CBO "
              f"(ex.: {divergentes[0]}) — D015")

    print(f"CBO: {len(cbo_ocupacoes)} ocupações | {cbo_sinonimos} sinônimos | "
          f"{len(cbo_niveis['familias'])} famílias, {len(cbo_niveis['subgrupos'])} subgrupos, "
          f"{len(cbo_niveis['subgrupos-principais'])} subgrupos principais, "
          f"{len(cbo_niveis['grandes-grupos'])} grandes grupos")
    print(f"QBQ: {len(ocupacoes)} ocupações | com competências: {total_comp} "
          f"| não classificadas: {nc['total']} | conceitos: {total_conceitos}")
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
