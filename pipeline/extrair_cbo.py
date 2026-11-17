#!/usr/bin/env python3
"""Extrai a espinha enumerativa da CBO 2002 dos CSVs oficiais para
dados/cbo/. Uso: python3 pipeline/extrair_cbo.py

Fontes (fontes/cbo/, cp1252, delimitador ';', colunas CODIGO e TITULO):
grande grupo (1 dígito) -> subgrupo principal (2) -> subgrupo (3) ->
família (4) -> ocupação (6), mais os sinônimos por código de ocupação.

A hierarquia é derivada do prefixo do código e conferida contra o nível
acima; qualquer órfão, código repetido ou título vazio interrompe a extração
com exit 1, em vez de gravar estrutura silenciosamente quebrada.
"""
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "fontes" / "cbo"
DESTINO = RAIZ / "dados" / "cbo"

DATA_VERSAO = "dados-2026.11"
ENCODING_FONTE = "cp1252"

# nome lógico -> (arquivo, dígitos do código, arquivo de saída)
NIVEIS = [
    ("grandes-grupos", "cbo2002-grande-grupo.csv", 1),
    ("subgrupos-principais", "cbo2002-subgrupo-principal.csv", 2),
    ("subgrupos", "cbo2002-subgrupo.csv", 3),
    ("familias", "cbo2002-familia.csv", 4),
]
ARQ_OCUPACAO = "cbo2002-ocupacao.csv"
ARQ_SINONIMO = "cbo2002-sinonimo.csv"

erros = []


def ler_csv(nome):
    """Linhas (codigo, titulo, linha_no_arquivo) de um CSV da CBO.

    Aparar espaços nas pontas é o D002: os títulos dos níveis superiores vêm
    preenchidos com espaços à direita até largura fixa. O conteúdo interno
    não é tocado.
    """
    caminho = FONTES / nome
    bruto = caminho.read_bytes().decode(ENCODING_FONTE)
    linhas = list(csv.reader(bruto.splitlines(), delimiter=";"))
    cabecalho = [c.strip().upper() for c in linhas[0]]
    if cabecalho != ["CODIGO", "TITULO"]:
        erros.append(f"{nome}: cabeçalho inesperado {cabecalho}")
        return []
    registros = []
    for i, linha in enumerate(linhas[1:], start=2):
        if not any(c.strip() for c in linha):
            continue
        if len(linha) != 2:
            erros.append(f"{nome}:{i}: {len(linha)} colunas, esperadas 2")
            continue
        codigo, titulo = linha[0].strip(), linha[1].strip()
        if not codigo or not titulo:
            erros.append(f"{nome}:{i}: código ou título vazio")
            continue
        registros.append((codigo, titulo, i))
    return registros


def checksum(nome):
    return hashlib.sha256((FONTES / nome).read_bytes()).hexdigest()


def gravar(caminho, doc):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    verificacao = {"versao_dados": DATA_VERSAO, "fontes": {}, "contagens": {}}

    # --- níveis superiores -------------------------------------------------
    codigos_por_nivel = {}
    for i, (nome_logico, arquivo, digitos) in enumerate(NIVEIS):
        registros = ler_csv(arquivo)
        vistos = set()
        itens = []
        for codigo, titulo, linha in sorted(registros):
            if len(codigo) != digitos:
                erros.append(f"{arquivo}:{linha}: código {codigo!r} não tem {digitos} dígito(s)")
                continue
            if codigo in vistos:
                erros.append(f"{arquivo}:{linha}: código {codigo} repetido")
                continue
            vistos.add(codigo)
            item = {"codigo": codigo, "titulo": titulo}
            if i > 0:
                pai = codigo[:NIVEIS[i - 1][2]]
                if pai not in codigos_por_nivel[NIVEIS[i - 1][0]]:
                    erros.append(f"{arquivo}:{linha}: {codigo} sem pai {pai} no nível acima")
                item["pai"] = pai
            item["fonte"] = {"arquivo": arquivo, "linha": linha}
            itens.append(item)
        codigos_por_nivel[nome_logico] = vistos
        gravar(DESTINO / "estrutura" / f"{nome_logico}.json", {
            "versao_dados": DATA_VERSAO,
            "fonte": f"fontes/cbo/{arquivo}",
            "nivel": nome_logico,
            "total": len(itens),
            "itens": itens,
        })
        verificacao["fontes"][arquivo] = checksum(arquivo)
        verificacao["contagens"][nome_logico] = len(itens)

    # --- sinônimos, agrupados por ocupação ---------------------------------
    sinonimos = defaultdict(list)
    for codigo, titulo, linha in sorted(ler_csv(ARQ_SINONIMO)):
        sinonimos[codigo].append({
            "titulo": titulo,
            "fonte": {"arquivo": ARQ_SINONIMO, "linha": linha},
        })
    verificacao["fontes"][ARQ_SINONIMO] = checksum(ARQ_SINONIMO)

    # --- ocupações, particionadas por grande grupo -------------------------
    por_gg = defaultdict(list)
    vistos = set()
    total_ocupacoes = 0
    for codigo, titulo, linha in sorted(ler_csv(ARQ_OCUPACAO)):
        if len(codigo) != 6:
            erros.append(f"{ARQ_OCUPACAO}:{linha}: código {codigo!r} não tem 6 dígitos")
            continue
        if codigo in vistos:
            erros.append(f"{ARQ_OCUPACAO}:{linha}: código {codigo} repetido")
            continue
        vistos.add(codigo)
        familia = codigo[:4]
        if familia not in codigos_por_nivel["familias"]:
            erros.append(f"{ARQ_OCUPACAO}:{linha}: {codigo} sem família {familia}")
        por_gg[codigo[0]].append({
            "codigo": codigo,
            "titulo": titulo,
            "familia": familia,
            "sinonimos": sinonimos.pop(codigo, []),
            "vigencia": {"status": "vigente", "desde": DATA_VERSAO, "ate": None},
            "fonte": {"arquivo": ARQ_OCUPACAO, "linha": linha},
        })
        total_ocupacoes += 1
    for codigo, itens in sorted(sinonimos.items()):
        erros.append(f"{ARQ_SINONIMO}: {len(itens)} sinônimo(s) de {codigo}, "
                     f"que não consta de {ARQ_OCUPACAO}")

    for gg, ocupacoes in sorted(por_gg.items()):
        gravar(DESTINO / "ocupacoes" / f"gg-{gg}.json", {
            "grande_grupo": gg,
            "versao_dados": DATA_VERSAO,
            "fonte": f"fontes/cbo/{ARQ_OCUPACAO}",
            "total": len(ocupacoes),
            "ocupacoes": ocupacoes,
        })
    verificacao["fontes"][ARQ_OCUPACAO] = checksum(ARQ_OCUPACAO)
    verificacao["contagens"]["ocupacoes"] = total_ocupacoes
    verificacao["contagens"]["ocupacoes_com_sinonimo"] = sum(
        1 for ocs in por_gg.values() for o in ocs if o["sinonimos"])
    verificacao["contagens"]["sinonimos"] = sum(
        len(o["sinonimos"]) for ocs in por_gg.values() for o in ocs)

    if erros:
        for e in erros[:30]:
            print("  ERRO:", e)
        sys.exit(f"extração da CBO interrompida: {len(erros)} problema(s)")

    gravar(DESTINO / "verificacao.json", verificacao)
    c = verificacao["contagens"]
    print(f"gravado dados/cbo/: {c['grandes-grupos']} grandes grupos, "
          f"{c['subgrupos-principais']} subgrupos principais, {c['subgrupos']} subgrupos, "
          f"{c['familias']} famílias, {c['ocupacoes']} ocupações, "
          f"{c['sinonimos']} sinônimos em {c['ocupacoes_com_sinonimo']} ocupações")


if __name__ == "__main__":
    main()
