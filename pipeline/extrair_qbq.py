#!/usr/bin/env python3
"""Extrai dados/qbq/*.json a partir da planilha oficial em fontes/qbq/.

Fonte: XLSX de download do QBQ (MTE). Abas: Layout, Ocupação, Conhecimento I
(ocupações de nível 1-5), Conhecimento II (níveis 6-8), Habilidade, Atitude,
Ocupações não classificada.

Uso: python3 pipeline/extrair_qbq.py
Dependência: openpyxl
"""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl é necessário: pip install openpyxl")

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "fontes" / "qbq" / "qbq-2025-03.xlsx"
SAIDA = RAIZ / "dados" / "qbq"
DATA_VERSAO = "dados-2026.08"
FONTE_REL = "fontes/qbq/qbq-2025-03.xlsx"


def texto(v):
    """Normaliza texto: só apara as pontas (fidelidade ao conteúdo interno)."""
    if v is None:
        return None
    s = str(v).replace("\r\n", "\n").strip()
    return s or None


def cod(v, zfill=None, strip_pontuacao=False):
    """Normaliza código: apara espaços; opcionalmente zero-padding e remoção
    de pontuação terminal (ver DECISOES.md, entradas 2 e 3)."""
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    if strip_pontuacao:
        s = s.rstrip(".")
    if zfill:
        s = s.zfill(zfill)
    return s or None


def bucket_outros(codigo):
    """Códigos com algum segmento '90' ou '99' são baldes de "outros" (nota
    da aba Layout; confirmado empiricamente): o mesmo código se repete com
    descrições distintas, e o conteúdo real do item está na descrição da
    linha (ver DECISOES.md, D009)."""
    if not codigo:
        return False
    return bool({"90", "99"} & set(codigo.rstrip(".").split(".")))


def grau(v, minimo=1, maximo=5, avisos=None, contexto=""):
    """Converte grau para int; fora da escala vira None e gera aviso."""
    if v is None:
        return None
    try:
        n = int(str(v).strip())
    except ValueError:
        if avisos is not None:
            avisos.append(f"grau não numérico {v!r} em {contexto}")
        return None
    if not (minimo <= n <= maximo):
        if avisos is not None:
            avisos.append(f"grau fora da escala {n} em {contexto}")
        return None
    return n


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def linhas(ws):
    """Itera linhas de dados (a partir da 2) com o número real da linha."""
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if all(c is None or str(c).strip() == "" for c in row):
            continue
        yield i, row


class Vocabulario:
    """Acumula um vocabulário controlado nivel a nivel, canonicalizando a
    descrição mais frequente e registrando divergências entre grafias."""

    def __init__(self):
        self.descricoes = defaultdict(Counter)   # codigo -> Counter(descricao)
        self.pais = defaultdict(Counter)         # codigo -> Counter(codigo_pai)

    def ver(self, codigo, descricao, pai=None):
        if codigo is None:
            return
        if descricao is not None:
            self.descricoes[codigo][descricao] += 1
        if pai is not None:
            self.pais[codigo][pai] += 1

    def registros(self):
        regs, divergencias = [], []
        for codigo in sorted(self.descricoes):
            variantes = self.descricoes[codigo]
            descricao = variantes.most_common(1)[0][0]
            reg = {"codigo": codigo, "descricao": descricao}
            if self.pais.get(codigo):
                pais = self.pais[codigo]
                reg["pai"] = pais.most_common(1)[0][0]
                if len(pais) > 1:
                    divergencias.append({
                        "codigo": codigo, "tipo": "pai",
                        "variantes": dict(pais)})
            if len(variantes) > 1:
                divergencias.append({
                    "codigo": codigo, "tipo": "descricao",
                    "canonica": descricao,
                    "variantes": {k: v for k, v in variantes.most_common()}})
            regs.append(reg)
        return regs, divergencias


def salvar(caminho, obj):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  gravado {caminho.relative_to(RAIZ)}")


def main():
    print(f"fonte: {FONTE_REL}")
    checksum = sha256(FONTE)
    wb = openpyxl.load_workbook(FONTE, read_only=True)
    avisos = []

    # ------------------------------------------------------------ Ocupação
    ocupacoes = {}
    for i, row in linhas(wb["Ocupação"]):
        codigo = cod(row[0], zfill=6)
        ocupacoes[codigo] = {
            "codigo": codigo,
            "titulo": texto(row[1]),
            "sintese": texto(row[2]),
            "perfil_ocupacional": texto(row[3]),
            "niveis": {
                "conhecimento": grau(row[4], 1, 8, avisos, f"Ocupação!{i}"),
                "habilidade": grau(row[5], 1, 8, avisos, f"Ocupação!{i}"),
                "atitude": grau(row[6], 1, 8, avisos, f"Ocupação!{i}"),
                "qualificacao": grau(row[7], 1, 8, avisos, f"Ocupação!{i}"),
            },
            "vigencia": {"status": "vigente", "desde": DATA_VERSAO, "ate": None},
            "fonte": {"arquivo": FONTE_REL, "aba": "Ocupação", "linha": i},
        }

    # ------------------------------------------- competências por ocupação
    comp = defaultdict(lambda: {"conhecimentos": [], "habilidades": [], "atitudes": []})
    taxonomia_de = {}

    # Conhecimento I (níveis 1-5): domínio > área > campo > conhecimento
    voc_c1 = {"dominios": Vocabulario(), "areas": Vocabulario(),
              "campos": Vocabulario(), "conhecimentos": Vocabulario()}
    for i, row in linhas(wb["Conhecimento I"]):
        codigo = cod(row[0], zfill=6)
        dom, area, campo, conhecimento = cod(row[1]), cod(row[3]), cod(row[5]), cod(row[7])
        voc_c1["dominios"].ver(dom, texto(row[2]))
        voc_c1["areas"].ver(area, texto(row[4]), pai=dom)
        voc_c1["campos"].ver(campo, texto(row[6]), pai=area)
        voc_c1["conhecimentos"].ver(conhecimento, texto(row[8]), pai=campo)
        taxonomia_de.setdefault(codigo, set()).add("conhecimentos-i")
        item = {
            "codigo": conhecimento,
            "profundidade": grau(row[9], 1, 5, avisos, f"Conhecimento I!{i}"),
            "frequencia": grau(row[10], 1, 5, avisos, f"Conhecimento I!{i}"),
            "importancia": grau(row[11], 1, 5, avisos, f"Conhecimento I!{i}"),
            "linha": i,
        }
        item["_desc"] = texto(row[8])
        comp[codigo]["conhecimentos"].append(item)

    # Conhecimento II (níveis 6-8): área > campo > conhecimento > elemento
    voc_c2 = {"areas": Vocabulario(), "campos": Vocabulario(),
              "conhecimentos": Vocabulario(), "elementos": Vocabulario()}
    for i, row in linhas(wb["Conhecimento II"]):
        codigo = cod(row[0], zfill=6)
        area = cod(row[1], strip_pontuacao=True)
        campo, conhecimento, elemento = cod(row[3]), cod(row[5]), cod(row[7])
        voc_c2["areas"].ver(area, texto(row[2]))
        voc_c2["campos"].ver(campo, texto(row[4]), pai=area)
        voc_c2["conhecimentos"].ver(conhecimento, texto(row[6]), pai=campo)
        voc_c2["elementos"].ver(elemento, texto(row[8]), pai=conhecimento)
        taxonomia_de.setdefault(codigo, set()).add("conhecimentos-ii")
        item = {
            "codigo": elemento,
            "profundidade": grau(row[9], 1, 5, avisos, f"Conhecimento II!{i}"),
            "frequencia": grau(row[10], 1, 5, avisos, f"Conhecimento II!{i}"),
            "importancia": grau(row[11], 1, 5, avisos, f"Conhecimento II!{i}"),
            "linha": i,
        }
        item["_desc"] = texto(row[8])
        comp[codigo]["conhecimentos"].append(item)

    # Habilidade: domínio > categoria > habilidade
    voc_h = {"dominios": Vocabulario(), "categorias": Vocabulario(),
             "habilidades": Vocabulario()}
    for i, row in linhas(wb["Habilidade"]):
        codigo = cod(row[0], zfill=6)
        dom, cat, hab = cod(row[1]), cod(row[3]), cod(row[5])
        voc_h["dominios"].ver(dom, texto(row[2]))
        voc_h["categorias"].ver(cat, texto(row[4]), pai=dom)
        voc_h["habilidades"].ver(hab, texto(row[6]), pai=cat)
        item = {
            "codigo": hab,
            "frequencia": grau(row[7], 1, 5, avisos, f"Habilidade!{i}"),
            "importancia": grau(row[8], 1, 5, avisos, f"Habilidade!{i}"),
            "linha": i,
        }
        item["_desc"] = texto(row[6])
        comp[codigo]["habilidades"].append(item)

    # Atitude: categoria > atitude
    voc_a = {"categorias": Vocabulario(), "atitudes": Vocabulario()}
    for i, row in linhas(wb["Atitude"]):
        codigo = cod(row[0], zfill=6)
        cat, ati = cod(row[1]), cod(row[3])
        voc_a["categorias"].ver(cat, texto(row[2]))
        voc_a["atitudes"].ver(ati, texto(row[4]), pai=cat)
        item = {
            "codigo": ati,
            "importancia": grau(row[5], 1, 5, avisos, f"Atitude!{i}"),
            "linha": i,
        }
        item["_desc"] = texto(row[4])
        comp[codigo]["atitudes"].append(item)

    # ------------------------------------------ Ocupações não classificadas
    nao_classificadas = []
    for i, row in linhas(wb["Ocupações não classificada"]):
        nao_classificadas.append({
            "codigo": cod(row[0], zfill=6),
            "titulo": texto(row[1]),
            "justificativa": texto(row[2]),
            "fonte": {"arquivo": FONTE_REL, "aba": "Ocupações não classificada", "linha": i},
        })
    wb.close()

    # ----------------- canonicaliza vocabulários e registra divergências
    vocab_arquivos, divergencias = {}, []
    for nome, vocs in [("conhecimentos-i", voc_c1), ("conhecimentos-ii", voc_c2),
                       ("habilidades", voc_h), ("atitudes", voc_a)]:
        arquivo = {"versao_dados": DATA_VERSAO, "fonte": FONTE_REL}
        for nivel, voc in vocs.items():
            regs, divs = voc.registros()
            arquivo[nivel] = regs
            for d in divs:
                d["vocabulario"] = f"{nome}.{nivel}"
                divergencias.append(d)
        vocab_arquivos[nome] = arquivo

    # ------- descrição inline nos itens (D009): baldes 90/99 sempre; demais
    # itens apenas quando a grafia da linha diverge da canônica do vocabulário
    canon_c = {
        "conhecimentos-i": {r["codigo"]: r["descricao"]
                            for r in vocab_arquivos["conhecimentos-i"]["conhecimentos"]},
        "conhecimentos-ii": {r["codigo"]: r["descricao"]
                             for r in vocab_arquivos["conhecimentos-ii"]["elementos"]},
    }
    canon_h = {r["codigo"]: r["descricao"]
               for r in vocab_arquivos["habilidades"]["habilidades"]}
    canon_a = {r["codigo"]: r["descricao"]
               for r in vocab_arquivos["atitudes"]["atitudes"]}

    def polir(item, canonico):
        desc = item.pop("_desc", None)
        if bucket_outros(item["codigo"]) or (
                desc is not None and desc != canonico.get(item["codigo"])):
            item["descricao"] = desc

    for codigo, dims in comp.items():
        taxos = taxonomia_de.get(codigo, set())
        cc = canon_c.get(next(iter(taxos)), {}) if len(taxos) == 1 else {}
        for it in dims["conhecimentos"]:
            polir(it, cc)
        for it in dims["habilidades"]:
            polir(it, canon_h)
        for it in dims["atitudes"]:
            polir(it, canon_a)

    # -------------------------------------------------------------- gravar
    por_gg = defaultdict(list)
    for codigo in sorted(ocupacoes):
        por_gg[codigo[0]].append(ocupacoes[codigo])
    for gg, regs in sorted(por_gg.items()):
        salvar(SAIDA / "ocupacoes" / f"gg-{gg}.json", {
            "grande_grupo": gg, "versao_dados": DATA_VERSAO,
            "total": len(regs), "ocupacoes": regs})

    comp_por_gg = defaultdict(list)
    for codigo in sorted(comp):
        taxos = sorted(taxonomia_de.get(codigo, []))
        registro = {
            "codigo": codigo,
            "taxonomia_conhecimento": taxos[0] if len(taxos) == 1 else (taxos or None),
            "conhecimentos": comp[codigo]["conhecimentos"],
            "habilidades": comp[codigo]["habilidades"],
            "atitudes": comp[codigo]["atitudes"],
        }
        comp_por_gg[codigo[0]].append(registro)
    for gg, regs in sorted(comp_por_gg.items()):
        salvar(SAIDA / "competencias" / f"gg-{gg}.json", {
            "grande_grupo": gg, "versao_dados": DATA_VERSAO,
            "total": len(regs), "ocupacoes": regs})

    for nome, arquivo in vocab_arquivos.items():
        salvar(SAIDA / "vocabularios" / f"{nome}.json", arquivo)

    salvar(SAIDA / "nao-classificadas.json", {
        "versao_dados": DATA_VERSAO, "total": len(nao_classificadas),
        "ocupacoes": nao_classificadas})

    salvar(SAIDA / "verificacao.json", {
        "versao_dados": DATA_VERSAO,
        "fonte": {"arquivo": FONTE_REL, "sha256": checksum},
        "contagens": {
            "ocupacoes_classificadas": len(ocupacoes),
            "ocupacoes_nao_classificadas": len(nao_classificadas),
            "itens_conhecimento": sum(len(c["conhecimentos"]) for c in comp.values()),
            "itens_habilidade": sum(len(c["habilidades"]) for c in comp.values()),
            "itens_atitude": sum(len(c["atitudes"]) for c in comp.values()),
        },
        "divergencias_vocabulario": divergencias,
        "avisos": avisos,
    })
    print(f"ocupações: {len(ocupacoes)} | não classificadas: {len(nao_classificadas)}")
    print(f"divergências de vocabulário: {len(divergencias)} | avisos: {len(avisos)}")


if __name__ == "__main__":
    main()
