#!/usr/bin/env python3
"""Extrai o perfil ocupacional da CBO 2002 (grandes áreas de competência e
atividades por ocupação) para dados/cbo/perfis/.
Uso: python3 pipeline/extrair_perfis.py

Fonte: fontes/cbo/cbo2002-perfilocupacional.csv (cp1252, delimitador ';',
174.296 linhas). Depende de dados/cbo/ocupacoes/ — rode extrair_cbo.py antes:
a espinha é a referência contra a qual toda ocupação do perfil é conferida.

Das nove colunas do CSV, só cinco são usadas: COD_OCUPACAO, SGL_GRANDE_AREA,
NOME_GRANDE_AREA, COD_ATIVIDADE e NOME_ATIVIDADE. As quatro colunas de
hierarquia são desnormalização defasada da fonte e ficam de fora (D017); a
hierarquia vem do prefixo do código da ocupação, como no resto da camada.

Falha com exit 1 se alguma ocupação do perfil não existir na espinha, se o
nome de uma área variar entre linhas da mesma ocupação ou se houver descrição
vazia — dado estruturalmente quebrado não é gravado em silêncio. Lacunas na
numeração das atividades e a repetição conhecida em 513505 são fatos da fonte
(D017): vão para verificacao.json, não para a lista de erros.
"""
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = "fontes/cbo/cbo2002-perfilocupacional.csv"
ESPINHA = RAIZ / "dados" / "cbo" / "ocupacoes"
DESTINO = RAIZ / "dados" / "cbo" / "perfis"

DATA_VERSAO = "dados-2026.11.1"
ENCODING_FONTE = "cp1252"
COLUNAS = ["COD_OCUPACAO", "SGL_GRANDE_AREA", "NOME_GRANDE_AREA",
           "COD_ATIVIDADE", "NOME_ATIVIDADE"]

erros = []


def ler_fonte():
    """Linhas do CSV como dicionários, com o número da linha no arquivo."""
    bruto = (RAIZ / FONTE).read_bytes().decode(ENCODING_FONTE)
    leitor = csv.DictReader(bruto.splitlines(), delimiter=";")
    faltando = [c for c in COLUNAS if c not in (leitor.fieldnames or [])]
    if faltando:
        sys.exit(f"{FONTE}: colunas ausentes: {faltando}")
    for i, r in enumerate(leitor, start=2):
        yield i, r


def codigos_da_espinha():
    codigos = set()
    for arq in sorted(ESPINHA.glob("gg-*.json")):
        doc = json.loads(arq.read_text(encoding="utf-8"))
        codigos.update(o["codigo"] for o in doc["ocupacoes"])
    if not codigos:
        sys.exit("dados/cbo/ocupacoes/ vazio — rode pipeline/extrair_cbo.py antes")
    return codigos


def gravar(caminho, conteudo):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    espinha = codigos_da_espinha()

    # ocupação -> sigla -> {"nome": str, "atividades": [...]}, na ordem do arquivo
    perfis = defaultdict(lambda: defaultdict(lambda: {"nome": None, "atividades": []}))
    linha_inicial = {}
    nomes_de_area = defaultdict(set)
    total_linhas = 0

    for i, r in ler_fonte():
        codigo = r["COD_OCUPACAO"].strip()
        sigla = r["SGL_GRANDE_AREA"].strip()
        nome_area = r["NOME_GRANDE_AREA"].strip()
        numero = r["COD_ATIVIDADE"].strip()
        descricao = r["NOME_ATIVIDADE"].strip()
        total_linhas += 1

        if codigo not in espinha:
            erros.append(f"{FONTE}:{i}: ocupação {codigo} fora da espinha da CBO")
            continue
        if not sigla or not nome_area or not descricao:
            erros.append(f"{FONTE}:{i}: campo obrigatório vazio em {codigo}")
            continue
        if not numero.isdigit():
            erros.append(f"{FONTE}:{i}: número de atividade {numero!r} não numérico")
            continue

        area = perfis[codigo][sigla]
        if area["nome"] is None:
            area["nome"] = nome_area
        elif area["nome"] != nome_area:
            erros.append(f"{FONTE}:{i}: área {sigla} de {codigo} muda de nome "
                         f"({area['nome']!r} -> {nome_area!r})")
            continue
        nomes_de_area[sigla].add(nome_area)
        area["atividades"].append({"numero": int(numero), "descricao": descricao})
        linha_inicial.setdefault(codigo, i)

    if erros:
        for e in erros[:30]:
            print("  ERRO:", e)
        sys.exit(f"extração do perfil interrompida: {len(erros)} problema(s)")

    # --- fatos da fonte, apurados e registrados em vez de corrigidos (D017) ---
    lacunas = repetidos = 0
    for codigo, areas in perfis.items():
        for sigla, area in areas.items():
            nums = [a["numero"] for a in area["atividades"]]
            if len(nums) != len(set(nums)):
                repetidos += 1
            if set(nums) != set(range(1, max(nums) + 1)):
                lacunas += 1

    por_gg = defaultdict(list)
    for codigo in sorted(perfis):
        areas = [{"sigla": s, "nome": perfis[codigo][s]["nome"],
                  "atividades": perfis[codigo][s]["atividades"]}
                 for s in sorted(perfis[codigo])]
        por_gg[codigo[0]].append({
            "codigo": codigo,
            "areas": areas,
            "fonte": {"arquivo": FONTE, "linha": linha_inicial[codigo]},
        })

    for gg in sorted(por_gg):
        gravar(DESTINO / f"gg-{gg}.json", {
            "grande_grupo": gg,
            "versao_dados": DATA_VERSAO,
            "fonte": FONTE,
            "total": len(por_gg[gg]),
            "ocupacoes": por_gg[gg],
        })

    sem_perfil = sorted(espinha - set(perfis))
    atividades = sum(len(a["atividades"]) for o in perfis.values() for a in o.values())
    verificacao = {
        "versao_dados": DATA_VERSAO,
        "fonte": FONTE,
        "sha256_fonte": hashlib.sha256((RAIZ / FONTE).read_bytes()).hexdigest(),
        "contagens": {
            "linhas_lidas": total_linhas,
            "ocupacoes_com_perfil": len(perfis),
            "areas": sum(len(a) for a in perfis.values()),
            "atividades": atividades,
        },
        "siglas": {s: sorted(n) for s, n in sorted(nomes_de_area.items())
                   if len(n) <= 5},
        "ocupacoes_sem_perfil": sem_perfil,
        "numeracao": {
            "pares_com_lacuna": lacunas,
            "pares_com_numero_repetido": repetidos,
        },
    }
    gravar(DESTINO / "verificacao.json", verificacao)

    c = verificacao["contagens"]
    print(f"gravado dados/cbo/perfis/: {c['ocupacoes_com_perfil']} ocupações, "
          f"{c['areas']} áreas, {c['atividades']} atividades "
          f"({len(sem_perfil)} ocupações da espinha sem perfil)")


if __name__ == "__main__":
    main()
