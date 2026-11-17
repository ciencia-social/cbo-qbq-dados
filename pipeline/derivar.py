#!/usr/bin/env python3
"""Gera derivados/ (CSV e SQLite) a partir de dados/qbq/. Nunca editar
derivados/ à mão. Uso: python3 pipeline/derivar.py"""
import csv
import hashlib
import re
import unicodedata
import json
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
QBQ = RAIZ / "dados" / "qbq"
CBO = RAIZ / "dados" / "cbo"
DER = RAIZ / "derivados"


def normalizar_titulo(s):
    """Mesma normalização do validador: compara grafias entre camadas sem
    acusar diferença onde só muda acento, caixa ou pontuação."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


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


NIVEIS_CBO = [("grandes-grupos", "cbo_grande_grupo", "cbo-grandes-grupos.csv"),
              ("subgrupos-principais", "cbo_subgrupo_principal", "cbo-subgrupos-principais.csv"),
              ("subgrupos", "cbo_subgrupo", "cbo-subgrupos.csv"),
              ("familias", "cbo_familia", "cbo-familias.csv")]


def derivar_cbo(tabelas):
    """Espinha da CBO em tabelas planas: um CSV por nível, um de ocupações e
    um de sinônimos (relação 1:N, por isso fora da linha da ocupação)."""
    for nivel, tabela, csv_nome in NIVEIS_CBO:
        doc = carregar(CBO / "estrutura" / f"{nivel}.json")
        linhas = [[i["codigo"], i["titulo"], i.get("pai")] for i in doc["itens"]]
        tabelas[tabela] = escrever_csv(csv_nome, ["codigo", "titulo", "pai"], linhas)

    ocup, sin = [], []
    for arq in sorted((CBO / "ocupacoes").glob("gg-*.json")):
        for o in carregar(arq)["ocupacoes"]:
            ocup.append([o["codigo"], o["titulo"], o["familia"], o["vigencia"]["status"]])
            for s in o["sinonimos"]:
                sin.append([o["codigo"], s["titulo"]])
    tabelas["cbo_ocupacao"] = escrever_csv(
        "cbo-ocupacoes.csv", ["codigo", "titulo", "familia", "vigencia"], ocup)
    tabelas["cbo_sinonimo"] = escrever_csv(
        "cbo-sinonimos.csv", ["ocupacao", "sinonimo"], sin)
    return {c[0] for c in ocup}


def derivar_cobertura(tabelas, codigos_cbo):
    """Diferenças entre as duas camadas na mesma chave (D015), em tabela: o
    que existe só de um lado e os títulos que divergem onde o código coincide.
    """
    qbq_titulos = {}
    for arq in sorted((QBQ / "ocupacoes").glob("gg-*.json")):
        for o in carregar(arq)["ocupacoes"]:
            qbq_titulos[o["codigo"]] = o["titulo"]
    cbo_titulos = {}
    for arq in sorted((CBO / "ocupacoes").glob("gg-*.json")):
        for o in carregar(arq)["ocupacoes"]:
            cbo_titulos[o["codigo"]] = o["titulo"]

    linhas = []
    for c in sorted(codigos_cbo - set(qbq_titulos)):
        linhas.append([c, "so_cbo", cbo_titulos[c], ""])
    for c in sorted(set(qbq_titulos) - codigos_cbo):
        linhas.append([c, "so_qbq", "", qbq_titulos[c]])
    for c in sorted(codigos_cbo & set(qbq_titulos)):
        if normalizar_titulo(cbo_titulos[c]) != normalizar_titulo(qbq_titulos[c]):
            linhas.append([c, "titulo_divergente", cbo_titulos[c], qbq_titulos[c]])
    linhas.sort()
    tabelas["cobertura_qbq_cbo"] = escrever_csv(
        "cobertura-qbq-cbo.csv", ["codigo", "situacao", "titulo_cbo", "titulo_qbq"], linhas)


def main():
    tabelas = {}
    codigos_cbo = derivar_cbo(tabelas)

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

    derivar_cobertura(tabelas, codigos_cbo)

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
