#!/usr/bin/env python3
"""Extrai os conceitos (definições oficiais) de domínios, categorias e
habilidades do PDF de conceitos e terminologia do QBQ para
dados/qbq/conceitos/habilidades.json.

Depende de dados/qbq/vocabularios/habilidades.json — rode extrair_qbq.py
antes. Os rótulos do vocabulário são as âncoras da extração: cada termo é
procurado no texto do PDF em ordem de código, e a definição é o texto entre
um termo e o seguinte. Isso torna a completude verificável — se um termo
esperado não for localizado, o script falha em vez de gravar dado
silenciosamente incompleto.

O texto do pdfium sai na ordem do content stream, que neste documento é, por
página: a tabela HABILIDADES/DEFINIÇÃO primeiro e os cabeçalhos de domínio e
categoria depois. O parser respeita essa ordem página a página.

Uso: python3 pipeline/extrair_conceitos.py
"""
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

try:
    import pypdfium2 as pdfium
except ImportError:
    sys.exit("pypdfium2 é necessário: pip install pypdfium2")

RAIZ = Path(__file__).resolve().parent.parent
FONTE = "fontes/qbq/conceitos-habilidades-2025-06.pdf"
VOCABULARIO = "dados/qbq/vocabularios/habilidades.json"
SAIDA = "dados/qbq/conceitos/habilidades.json"

# Cabeçalho repetido da tabela e marcadores de bloco de cabeçalho.
RE_CABECALHO_TABELA = re.compile(r"HABILIDADES\s+DEFINI[ÇC][ÃA]O", re.I)
RE_MARCADOR_BLOCO = re.compile(r"\d\s*\.\s*Dom[íi]nio|[a-z]\s*\)\s*Categoria", re.I)
# Título do documento, que aparece no topo de cada página.
RE_TITULO_DOC = re.compile(r"Defini[çc][ãa]o\s+de\s+Habilidades", re.I)
# Marcadores em coordenadas normalizadas ("a) Categoria" -> "A CATEGORIA").
RE_MARCADOR_NORM = re.compile(r"\b(?:[A-Z] CATEGORIA|\d DOMINIO)\b")

erros = []


def eh_balde(codigo):
    """Códigos com segmento 90 são baldes de "outros" (D009) e não têm
    definição oficial no PDF."""
    return "90" in codigo.split(".")


def normalizar(s):
    """Uppercase sem acentos, não-alfanuméricos virando espaço."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]+", " ", s).strip().upper()


class Indexado:
    """Texto normalizado com mapa de volta para as posições do original,
    para que o recorte da definição preserve a grafia da fonte."""

    def __init__(self, original):
        self.original = original
        pedacos, mapa = [], []
        espaco_pendente = False
        for i, ch in enumerate(original):
            base = unicodedata.normalize("NFKD", ch)
            base = "".join(c for c in base if not unicodedata.combining(c))
            base = base.upper()
            if base.isalnum():
                if espaco_pendente and pedacos:
                    pedacos.append(" ")
                    mapa.append(i)
                    espaco_pendente = False
                for c in base:
                    pedacos.append(c)
                    mapa.append(i)
            elif base:
                espaco_pendente = True
        self.txt = "".join(pedacos)
        self.mapa = mapa
        # (inicio, fim) de cada palavra em coordenadas normalizadas
        self.palavras = [(m.start(), m.end()) for m in re.finditer(r"\S+", self.txt)]

    def procurar(self, agulha, inicio=0):
        """Posição (em coordenadas normalizadas) de `agulha` a partir de
        `inicio`, ou None."""
        if not agulha:
            return None
        p = self.txt.find(agulha, inicio)
        return None if p < 0 else p

    def termo(self, achado):
        """Rótulo como grafado no original. Inclui o fecha-parêntese, que a
        normalização deixa de fora por não ser alfanumérico."""
        a = self.mapa[achado[0]]
        b = self.mapa[achado[1] - 1] + 1
        vizinho = self.original[b:b + 3]
        if vizinho.strip()[:1] == ")":
            b += vizinho.index(")") + 1
        return self.original[a:b].strip()

    def recortar(self, ini_norm, fim_norm):
        """Texto original entre duas posições normalizadas, limpo."""
        if ini_norm >= len(self.mapa):
            return ""
        a = self.mapa[ini_norm]
        b = self.mapa[fim_norm] if fim_norm < len(self.mapa) else len(self.original)
        bruto = self.original[a:b]
        bruto = RE_CABECALHO_TABELA.sub(" ", bruto)
        bruto = RE_TITULO_DOC.sub(" ", bruto)
        bruto = re.sub(r"\s+", " ", bruto)
        return bruto.strip(" .;:-–\u2013").strip() + "." if bruto.strip(" .;:-–\u2013") else ""


def variantes(descricao):
    """Formas de procurar um rótulo, da mais específica para a menos. O rótulo
    completo vem primeiro para que o parentético, quando o PDF o traz (ex.:
    "Visão de perto (ou a curta distância)"), seja consumido como parte do
    termo e não sobre no texto da definição. A forma sem parentético é o
    fallback para quando o PDF o omite (ex.: 01.03.04)."""
    formas = [descricao]
    sem_parentese = re.sub(r"\([^)]*\)", " ", descricao)
    if normalizar(sem_parentese) != normalizar(descricao):
        formas.append(sem_parentese)
    return [normalizar(f) for f in formas if normalizar(f)]


# Grafias divergem entre a planilha e o PDF por erros de digitação nos dois
# lados (D013), então o casamento exato falha em alguns rótulos. O limiar
# abaixo aceita divergência de poucos caracteres; toda diferença encontrada é
# registrada em `divergencias` no arquivo de saída, para auditoria.
LIMIAR_SIMILARIDADE = 0.90


def localizar(pagina, termo, cursor, limite):
    """Ocorrência de `termo` na janela [cursor, limite) do texto normalizado.
    Tenta casamento exato de cada variante; se nenhuma casar, procura a janela
    de palavras mais à esquerda com similaridade >= LIMIAR_SIMILARIDADE.
    Retorna (inicio, fim) em coordenadas normalizadas, ou None."""
    for forma in variantes(termo):
        p = pagina.procurar(forma, cursor)
        if p is not None and p + len(forma) <= limite:
            return p, p + len(forma)

    forma = variantes(termo)[0]
    n_palavras = len(forma.split())
    palavras = [(a, b) for a, b in pagina.palavras if a >= cursor and b <= limite]
    for k in (n_palavras, n_palavras - 1, n_palavras + 1):
        if k < 1:
            continue
        for i in range(len(palavras) - k + 1):
            ini, fim = palavras[i][0], palavras[i + k - 1][1]
            candidato = pagina.txt[ini:fim]
            if SequenceMatcher(None, forma, candidato).ratio() >= LIMIAR_SIMILARIDADE:
                return ini, fim
    return None


divergencias = []


def anotar_divergencia(nivel, item, pagina, achado):
    """Registra quando a grafia do rótulo no PDF difere da do vocabulário
    (que vem da planilha). Nenhuma das duas é corrigida: o dado guarda as
    duas e aponta a diferença (D013)."""
    no_pdf = pagina.termo(achado)
    if normalizar(no_pdf) not in variantes(item["descricao"]):
        divergencias.append({
            "nivel": nivel,
            "codigo": item["codigo"],
            "termo_pdf": no_pdf,
            "termo_planilha": item["descricao"],
        })


def main():
    voc = json.load(open(RAIZ / VOCABULARIO, encoding="utf-8"))
    doc = pdfium.PdfDocument(RAIZ / FONTE)
    paginas = [Indexado(doc[i].get_textpage().get_text_range()) for i in range(len(doc))]

    # Âncoras esperadas, em ordem de código. Baldes ficam de fora: o PDF não
    # os define (D012).
    esperados = {
        "dominios": [d for d in voc["dominios"] if not eh_balde(d["codigo"])],
        "categorias": [c for c in voc["categorias"] if not eh_balde(c["codigo"])],
        "habilidades": [h for h in voc["habilidades"] if not eh_balde(h["codigo"])],
    }
    conceitos = {k: [] for k in esperados}
    fila_hab = list(esperados["habilidades"])
    fila_dom = list(esperados["dominios"])
    fila_cat = list(esperados["categorias"])

    for pagina in paginas:
        # A página se divide em: parte da tabela | parte dos cabeçalhos.
        m = RE_MARCADOR_BLOCO.search(pagina.original)
        corte = len(pagina.txt)
        if m:
            # posição do marcador em coordenadas normalizadas
            for pos, orig in enumerate(pagina.mapa):
                if orig >= m.start():
                    corte = pos
                    break

        # --- tabela: consome habilidades enquanto os rótulos aparecerem ---
        cursor, pendente = 0, None
        while fila_hab:
            achado = localizar(pagina, fila_hab[0]["descricao"], cursor, corte)
            if achado is None:
                break
            item = fila_hab.pop(0)
            anotar_divergencia("habilidade", item, pagina, achado)
            if pendente:
                codigo, termo, inicio_def = pendente
                conceitos["habilidades"].append({
                    "codigo": codigo, "termo": termo,
                    "conceito": pagina.recortar(inicio_def, achado[0])})
            pendente = (
                item["codigo"],
                pagina.termo(achado),
                achado[1],
            )
            cursor = achado[1]
        if pendente:
            codigo, termo, inicio_def = pendente
            conceitos["habilidades"].append({
                "codigo": codigo, "termo": termo,
                "conceito": pagina.recortar(inicio_def, corte)})

        # --- cabeçalhos, guiados pelos marcadores "N. Domínio"/"x) Categoria".
        # Ancorar no marcador (e não só no nome) evita casar uma categoria na
        # menção que a definição do domínio faz dela — a definição do domínio 2
        # cita "habilidades operacionais, organizacionais e interpessoais"
        # antes dos cabeçalhos dessas mesmas categorias. O bloco de cada
        # marcador termina onde o próximo começa, o que também mantém o "x)"
        # seguinte fora do texto da definição.
        marcadores = [(m.start(), m.end(), m.group())
                      for m in RE_MARCADOR_NORM.finditer(pagina.txt) if m.start() >= corte]
        for i, (_, fim_marcador, texto_marcador) in enumerate(marcadores):
            fim_bloco = marcadores[i + 1][0] if i + 1 < len(marcadores) else len(pagina.txt)
            eh_dominio = "DOMINIO" in texto_marcador
            fila = fila_dom if eh_dominio else fila_cat
            if not fila:
                continue
            item = fila[0]
            achado = localizar(pagina, item["descricao"], fim_marcador, fim_bloco)
            if achado is None:
                continue
            fila.pop(0)
            anotar_divergencia("domínio" if eh_dominio else "categoria", item, pagina, achado)
            conceitos["dominios" if eh_dominio else "categorias"].append({
                "codigo": item["codigo"],
                "termo": pagina.termo(achado),
                "conceito": pagina.recortar(achado[1], fim_bloco),
            })

    # --- completude: nada pode sobrar nas filas ---
    for nivel, fila in (("domínio", fila_dom), ("categoria", fila_cat), ("habilidade", fila_hab)):
        for item in fila:
            erros.append(f"{nivel} {item['codigo']} ({item['descricao']}) não localizado no PDF")
    for nivel, itens in conceitos.items():
        for it in itens:
            if not it["conceito"]:
                erros.append(f"{nivel} {it['codigo']} localizado sem texto de definição")

    if erros:
        for e in erros[:30]:
            print("  ERRO:", e)
        sys.exit(f"extração incompleta: {len(erros)} problema(s)")

    saida = {
        "versao_dados": voc["versao_dados"],
        "fonte": FONTE,
        "dimensao": "habilidades",
        "dominios": conceitos["dominios"],
        "categorias": conceitos["categorias"],
        "habilidades": conceitos["habilidades"],
        "divergencias": sorted(divergencias, key=lambda d: d["codigo"]),
    }
    destino = RAIZ / SAIDA
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"gravado {SAIDA}: {len(saida['dominios'])} domínios, "
          f"{len(saida['categorias'])} categorias, {len(saida['habilidades'])} habilidades")


if __name__ == "__main__":
    main()
