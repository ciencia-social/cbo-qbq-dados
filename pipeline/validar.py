#!/usr/bin/env python3
"""Checagens de contrato sobre dados/ (camadas CBO e QBQ) e sobre os metadados
da publicação (contrato 14, D020). Falha (exit 1) se algum contrato for
violado. Uso: python3 pipeline/validar.py"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from publicacao import (
    AUTOR_FAMILY,
    AUTOR_GIVEN,
    AUTOR_ZENODO,
    CHAVES_CONTAGEM,
    DATA_RELEASE,
    DOI_CONCEITO,
    DOI_VERSAO,
    LICENCA_CODIGO,
    LICENCA_DADOS,
    LICENCA_ZENODO,
    ORCID,
    VERSAO_DADOS,
    VERSAO_SCHEMA,
    camadas_nos_dados,
)

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

    # 13. perfil ocupacional (D017): integridade contra a espinha, siglas e
    #     numeração. Lacunas e repetição na numeração são fatos da fonte e
    #     viram aviso; ocupação sem perfil idem.
    atividades = 0
    com_perfil = set()
    for arq in sorted((CBO / "perfis").glob("gg-*.json")):
        doc = carregar(arq)
        for o in doc["ocupacoes"]:
            c = o["codigo"]
            if c not in ocupacoes:
                erro(f"cbo/perfis: ocupação {c} sem registro na espinha")
            if c[0] != doc["grande_grupo"]:
                erro(f"cbo/perfis: {c} no arquivo errado ({arq.name})")
            if c in com_perfil:
                erro(f"cbo/perfis: ocupação {c} duplicada")
            com_perfil.add(c)
            siglas = [a["sigla"] for a in o["areas"]]
            if siglas != sorted(set(siglas)):
                erro(f"cbo/perfis: {c} com siglas repetidas ou fora de ordem: {siglas}")
            for a in o["areas"]:
                nums = [t["numero"] for t in a["atividades"]]
                atividades += len(nums)
                if nums != sorted(nums):
                    erro(f"cbo/perfis: {c} área {a['sigla']} com numeração fora de ordem")
                if len(nums) != len(set(nums)):
                    aviso(f"cbo/perfis: {c} área {a['sigla']} repete número de "
                          f"atividade (D017)")
        if doc["total"] != len(doc["ocupacoes"]):
            erro(f"cbo/perfis/{arq.name}: total declarado {doc['total']} != "
                 f"{len(doc['ocupacoes'])}")

    if com_perfil:
        sem_perfil = set(ocupacoes) - com_perfil
        if sem_perfil:
            aviso(f"{len(sem_perfil)} ocupações da espinha sem perfil ocupacional "
                  f"(ex.: {', '.join(sorted(sem_perfil)[:3])}) — lacuna da fonte")

    return codigos, ocupacoes, sinonimos, atividades


def _limpar(valor):
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        return valor[1:-1]
    return valor


def ler_cff(texto):
    """Lê os campos planos e o primeiro autor de CITATION.cff.

    O arquivo é escrito à mão nesse formato (chaves no começo da linha,
    primeiro autor indentado). Não puxa PyYAML para o CI.
    """
    campos = {}
    autor = {}
    em_autor = False
    for linha in texto.splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        if linha.startswith("authors:"):
            em_autor = True
            continue
        if em_autor and linha.startswith("  - "):
            resto = linha.strip()[2:]
            if ":" in resto and not autor:
                chave, valor = resto.split(":", 1)
                autor[chave.strip()] = _limpar(valor)
            continue
        if em_autor and linha.startswith("    ") and ":" in linha:
            chave, valor = linha.strip().split(":", 1)
            autor[chave.strip()] = _limpar(valor)
            continue
        if linha[:1].isspace():
            continue
        em_autor = False
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            campos[chave.strip()] = _limpar(valor)
    campos["author"] = autor
    return campos


def _ler_json_metadado(rel):
    caminho = RAIZ / rel
    if not caminho.is_file():
        erro(f"metadados: {rel} ausente")
        return None
    try:
        return carregar(caminho)
    except json.JSONDecodeError as exc:
        erro(f"metadados: {rel} não é JSON válido ({exc})")
        return None


def _exigir_versao(arquivo, achada):
    if achada != VERSAO_DADOS:
        erro(
            f"metadados: {arquivo} declara {achada!r}, "
            f"a versão corrente é {VERSAO_DADOS!r}"
        )


def validar_metadados(contagens):
    """14. Versão única nos metadados, e VERSAO.json fiel a dados/ (D020).

    .zenodo.json, CITATION.cff, VERSAO.json e o datapackage têm de declarar
    a versão desta publicação. VERSAO.json ainda repete as contagens reais
    e a versao_dados de cada camada nos arquivos de dados/ (D016). Os
    arquivos de dados/ guardam a publicação em que a camada foi gerada, não
    a versão corrente — por isso a comparação da versão corrente é com a
    constante do pipeline, e a das camadas é com os JSON de dados/.
    Divergência é erro.
    """
    if tuple(contagens) != CHAVES_CONTAGEM:
        erro("metadados: contagens internas fora da ordem de CHAVES_CONTAGEM")

    zenodo = _ler_json_metadado(".zenodo.json")
    if zenodo is not None:
        if "doi" in zenodo:
            erro(".zenodo.json: o campo doi não deve ser escrito; o Zenodo cunha o identificador")
        _exigir_versao(".zenodo.json", zenodo.get("version"))
        if zenodo.get("license") != LICENCA_ZENODO:
            erro(
                f".zenodo.json: license {zenodo.get('license')!r} discorda de "
                f"{LICENCA_ZENODO!r}, o identificador Zenodo de {LICENCA_DADOS}"
            )
        criadores = zenodo.get("creators") or [{}]
        if criadores[0].get("name") != AUTOR_ZENODO:
            erro(
                f".zenodo.json: creators[0].name {criadores[0].get('name')!r} "
                f"discorda de {AUTOR_ZENODO!r}"
            )
        if criadores[0].get("orcid") != ORCID:
            erro(f".zenodo.json: orcid {criadores[0].get('orcid')!r} discorda de {ORCID!r}")

    cff_caminho = RAIZ / "CITATION.cff"
    cff = None
    if not cff_caminho.is_file():
        erro("metadados: CITATION.cff ausente")
    else:
        cff = ler_cff(cff_caminho.read_text(encoding="utf-8"))
        if "version" not in cff:
            erro("CITATION.cff: campo version ilegível")
        else:
            _exigir_versao("CITATION.cff", cff.get("version"))
        if cff.get("date-released") != DATA_RELEASE:
            erro(
                f"CITATION.cff: date-released {cff.get('date-released')!r} "
                f"discorda da data da release {DATA_RELEASE!r}"
            )
        if cff.get("license") != LICENCA_DADOS:
            erro(f"CITATION.cff: license {cff.get('license')!r} discorda de {LICENCA_DADOS!r}")
        autor = cff.get("author") or {}
        if autor.get("family-names") != AUTOR_FAMILY or autor.get("given-names") != AUTOR_GIVEN:
            erro(
                "CITATION.cff: autoria discorda de "
                f"family-names {AUTOR_FAMILY}, given-names {AUTOR_GIVEN}"
            )
        if ORCID not in (autor.get("orcid") or ""):
            erro(f"CITATION.cff: orcid {autor.get('orcid')!r} não contém {ORCID}")
        doi_cff = cff.get("doi")
        if DOI_VERSAO:
            if doi_cff != DOI_VERSAO:
                erro(f"CITATION.cff: doi {doi_cff!r} discorda do DOI de versão {DOI_VERSAO!r}")
        elif doi_cff:
            erro(
                f"CITATION.cff: doi {doi_cff!r} está preenchido, "
                "mas o DOI de versão ainda não foi reservado"
            )
        if zenodo is not None and cff.get("title") and zenodo.get("title") != cff.get("title"):
            erro("metadados: título de .zenodo.json discorda do de CITATION.cff")

    versao = _ler_json_metadado("VERSAO.json")
    if versao is not None:
        _exigir_versao("VERSAO.json", versao.get("versao_dados"))
        if versao.get("versao_schema") != VERSAO_SCHEMA:
            erro(
                f"VERSAO.json: versao_schema {versao.get('versao_schema')!r} "
                f"discorda de {VERSAO_SCHEMA!r}"
            )
        if versao.get("gerado_em") != DATA_RELEASE:
            erro(
                f"VERSAO.json: gerado_em {versao.get('gerado_em')!r} "
                f"discorda da data da release {DATA_RELEASE!r}"
            )
        if versao.get("licencas") != {"dados": LICENCA_DADOS, "codigo": LICENCA_CODIGO}:
            erro("VERSAO.json: licencas discordam dos identificadores SPDX da publicação")
        doi = versao.get("doi") or {}
        if doi.get("conceito") != DOI_CONCEITO or doi.get("versao") != DOI_VERSAO:
            erro(
                "VERSAO.json: doi discorda das constantes do pipeline "
                f"(conceito {doi.get('conceito')!r}, versao {doi.get('versao')!r})"
            )
        try:
            reais = camadas_nos_dados(RAIZ)
        except ValueError as exc:
            erro(f"VERSAO.json: {exc}")
            reais = None
        declaradas = versao.get("camadas")
        if not isinstance(declaradas, dict):
            erro("VERSAO.json: campo camadas ausente ou ilegível")
        elif reais is not None:
            for chave in reais:
                if declaradas.get(chave) != reais[chave]:
                    erro(
                        f"VERSAO.json: camada {chave}={declaradas.get(chave)!r} "
                        f"discorda dos arquivos de dados/ ({reais[chave]!r})"
                    )
            extras = sorted(set(declaradas) - set(reais))
            if extras:
                erro(f"VERSAO.json: camadas desconhecidas {extras}")
        declaradas_cont = versao.get("contagens")
        if not isinstance(declaradas_cont, dict):
            erro("VERSAO.json: campo contagens ausente ou ilegível")
        else:
            for chave in CHAVES_CONTAGEM:
                if declaradas_cont.get(chave) != contagens[chave]:
                    erro(
                        f"VERSAO.json: contagem {chave}={declaradas_cont.get(chave)!r} "
                        f"discorda da contagem real {contagens[chave]}"
                    )
            extras = sorted(set(declaradas_cont) - set(CHAVES_CONTAGEM))
            if extras:
                erro(f"VERSAO.json: contagens desconhecidas {extras}")

    pacote = _ler_json_metadado("derivados/csv/datapackage.json")
    if pacote is not None:
        _exigir_versao("derivados/csv/datapackage.json", pacote.get("version"))
        licencas = pacote.get("licenses") or []
        nomes = {item.get("name") for item in licencas if isinstance(item, dict)}
        if LICENCA_DADOS not in nomes:
            erro(f"derivados/csv/datapackage.json: licenses não declara {LICENCA_DADOS}")
        for rec in pacote.get("resources") or []:
            if not isinstance(rec, dict):
                erro("derivados/csv/datapackage.json: recurso ilegível")
                continue
            caminho = RAIZ / "derivados" / "csv" / rec.get("path", "")
            if not caminho.is_file():
                erro(f"datapackage: path inexistente {rec.get('path')!r}")
                continue
            with open(caminho, encoding="utf-8", newline="") as f:
                cabecalho = next(csv.reader(f))
            nomes_campos = [c.get("name") for c in rec.get("schema", {}).get("fields", [])]
            if nomes_campos != cabecalho:
                erro(
                    f"datapackage: campos de {rec.get('path')} {nomes_campos} "
                    f"discordam do cabeçalho {cabecalho}"
                )


def main():
    cbo_niveis, cbo_ocupacoes, cbo_sinonimos, cbo_atividades = validar_cbo()

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

    contagens = {
        "cbo_grandes_grupos": len(cbo_niveis["grandes-grupos"]),
        "cbo_subgrupos_principais": len(cbo_niveis["subgrupos-principais"]),
        "cbo_subgrupos": len(cbo_niveis["subgrupos"]),
        "cbo_familias": len(cbo_niveis["familias"]),
        "cbo_ocupacoes": len(cbo_ocupacoes),
        "cbo_sinonimos": cbo_sinonimos,
        "cbo_atividades": cbo_atividades,
        "qbq_ocupacoes": len(ocupacoes),
        "qbq_com_competencias": total_comp,
        "qbq_nao_classificadas": nc["total"],
        "qbq_conceitos": total_conceitos,
    }
    validar_metadados(contagens)

    print(f"CBO: {len(cbo_ocupacoes)} ocupações | {cbo_sinonimos} sinônimos | "
          f"{cbo_atividades} atividades de perfil | "
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
