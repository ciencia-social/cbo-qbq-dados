#!/usr/bin/env python3
"""Gera derivados/ (CSV e SQLite) a partir de dados/qbq/. Nunca editar
derivados/ à mão. Uso: python3 pipeline/derivar.py"""
import csv
import hashlib
import json
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
QBQ = RAIZ / "dados" / "qbq"
DER = RAIZ / "derivados"


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def escrever_csv(nome, colunas, linhas):
    caminho = DER / "csv" / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(colunas)
        w.writerows(linhas)
    print(f"  gravado derivados/csv/{nome} ({len(linhas)} linhas)")
    return colunas, linhas


def main():
    tabelas = {}

    ocup = []
    for arq in sorted((QBQ / "ocupacoes").glob("gg-*.json")):
        for o in carregar(arq)["ocupacoes"]:
            n = o["niveis"]
            ocup.append([o["codigo"], o["titulo"], o["sintese"], o["perfil_ocupacional"],
                         n["conhecimento"], n["habilidade"], n["atitude"], n["qualificacao"],
                         o["vigencia"]["status"]])
    tabelas["qbq_ocupacao"] = escrever_csv(
        "qbq-ocupacoes.csv",
        ["codigo", "titulo", "sintese", "perfil_ocupacional", "nivel_conhecimento",
         "nivel_habilidade", "nivel_atitude", "nivel_qualificacao", "vigencia"], ocup)

    con, hab, ati = [], [], []
    for arq in sorted((QBQ / "competencias").glob("gg-*.json")):
        for oc in carregar(arq)["ocupacoes"]:
            for i in oc["conhecimentos"]:
                con.append([oc["codigo"], oc["taxonomia_conhecimento"], i["codigo"],
                            i.get("profundidade"), i.get("frequencia"),
                            i.get("importancia"), i.get("descricao")])
            for i in oc["habilidades"]:
                hab.append([oc["codigo"], i["codigo"], i.get("frequencia"),
                            i.get("importancia"), i.get("descricao")])
            for i in oc["atitudes"]:
                ati.append([oc["codigo"], i["codigo"], i.get("importancia"),
                            i.get("descricao")])
    tabelas["qbq_conhecimento"] = escrever_csv(
        "qbq-conhecimentos.csv",
        ["ocupacao", "taxonomia", "item", "profundidade", "frequencia",
         "importancia", "descricao"], con)
    tabelas["qbq_habilidade"] = escrever_csv(
        "qbq-habilidades.csv",
        ["ocupacao", "item", "frequencia", "importancia", "descricao"], hab)
    tabelas["qbq_atitude"] = escrever_csv(
        "qbq-atitudes.csv", ["ocupacao", "item", "importancia", "descricao"], ati)

    for nome in ["conhecimentos-i", "conhecimentos-ii", "habilidades", "atitudes"]:
        doc = carregar(QBQ / "vocabularios" / f"{nome}.json")
        linhas = []
        for nivel, regs in doc.items():
            if isinstance(regs, list):
                for r in regs:
                    linhas.append([nome, nivel, r["codigo"], r["descricao"], r.get("pai")])
        tabela = "qbq_vocabulario_" + nome.replace("-", "_")
        tabelas[tabela] = escrever_csv(
            f"qbq-vocabulario-{nome}.csv",
            ["vocabulario", "nivel", "codigo", "descricao", "pai"], linhas)

    conceitos = []
    for arq in sorted((QBQ / "conceitos").glob("*.json")):
        doc = carregar(arq)
        for nivel, regs in doc.items():
            if nivel == "divergencias" or not isinstance(regs, list):
                continue
            for r in regs:
                conceitos.append([doc["dimensao"], nivel, r["codigo"],
                                  r["termo"], r["conceito"]])
    tabelas["qbq_conceito"] = escrever_csv(
        "qbq-conceitos.csv",
        ["vocabulario", "nivel", "codigo", "termo", "conceito"], conceitos)

    nc = [[o["codigo"], o["titulo"], o["justificativa"]]
          for o in carregar(QBQ / "nao-classificadas.json")["ocupacoes"]]
    tabelas["qbq_nao_classificada"] = escrever_csv(
        "qbq-nao-classificadas.csv", ["codigo", "titulo", "justificativa"], nc)

    # SQLite com as mesmas tabelas
    db_path = DER / "qbq.sqlite"
    db_path.unlink(missing_ok=True)
    db = sqlite3.connect(db_path)
    for tabela, (colunas, linhas) in tabelas.items():
        cols = ", ".join(f'"{c}"' for c in colunas)
        db.execute(f'CREATE TABLE {tabela} ({cols})')
        db.executemany(
            f'INSERT INTO {tabela} VALUES ({", ".join("?" * len(colunas))})', linhas)
    db.commit()
    with open(DER / "qbq.sql", "w", encoding="utf-8") as f:
        for linha in db.iterdump():
            f.write(linha + "\n")
    db.close()
    print("  gravado derivados/qbq.sqlite e derivados/qbq.sql")

    # Manifesto dos ativos que NÃO são versionados (vão como anexos de release).
    # Formato compatível com `sha256sum -c`. O CI confere estritamente a linha
    # de qbq.sql (texto, determinístico); ver derivados/README.md sobre o
    # sqlite, cuja identidade byte a byte depende da versão da libsqlite.
    manifesto = DER / "MANIFEST.sha256"
    with open(manifesto, "w", encoding="utf-8") as f:
        for rel in ("qbq.sql", "qbq.sqlite"):
            h = hashlib.sha256((DER / rel).read_bytes()).hexdigest()
            f.write(f"{h}  derivados/{rel}\n")
    print(f"  gravado derivados/MANIFEST.sha256 ({manifesto.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
