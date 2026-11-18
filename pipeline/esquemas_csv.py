"""Descrição das colunas de derivados/csv/, usada por derivar.py ao gravar
o datapackage. O arquivo JSON não se edita: muda-se aqui e regenera.

Códigos da CBO são string — inteiro apagaria o zero à esquerda (D001).
Graus e níveis são integer. Chave primária só onde a repetição é erro de
contrato, não aviso: sinônimo, atividade e item de competência podem repetir
por fato da fonte (D009, D017).
"""


def campo(nome, tipo, descricao):
    return {"name": nome, "type": tipo, "description": descricao}


def fk(campos, recurso, refs):
    if isinstance(campos, str):
        campos = [campos]
    if isinstance(refs, str):
        refs = [refs]
    return {"fields": campos, "reference": {"resource": recurso, "fields": refs}}


# O CSV é gravado com o terminador padrão do módulo csv, que é CRLF.
DIALETO = {"delimiter": ",", "header": True, "lineTerminator": "\r\n"}

CODIGO = (
    "Código CBO deste nível, preservado como texto. "
    "Inteiro apagaria o zero à esquerda (D001)."
)
CODIGO_OCUPACAO = (
    "Código CBO da ocupação, seis dígitos, preservado como texto "
    "para não perder o zero à esquerda (D001)."
)
TITULO = "Título oficial, como publicado na fonte."
PAI = "Código do nível imediatamente acima. Vazio na raiz."


def _campos_vocabulario():
    return [
        campo(
            "vocabulario",
            "string",
            "Nome do vocabulário: conhecimentos-i, conhecimentos-ii, habilidades ou atitudes.",
        ),
        campo("nivel", "string", "Nível do termo dentro do vocabulário (domínio, categoria, elemento ou equivalente)."),
        campo("codigo", "string", "Código do termo, preservado como texto. Pode se repetir entre níveis."),
        campo("descricao", "string", "Descrição oficial do termo."),
        campo("pai", "string", "Código do termo pai. Vazio na raiz do vocabulário."),
    ]


def _nivel_cbo(titulo, descricao, pai_recurso=None):
    spec = {
        "title": titulo,
        "description": descricao,
        "fields": [
            campo("codigo", "string", CODIGO),
            campo("titulo", "string", TITULO),
            campo("pai", "string", PAI),
        ],
        "primaryKey": ["codigo"],
    }
    if pai_recurso:
        spec["foreignKeys"] = [fk("pai", pai_recurso, "codigo")]
    return spec


ESQUEMAS = {
    "cbo_grande_grupo": {
        "path": "cbo-grandes-grupos.csv",
        **_nivel_cbo(
            "Grandes grupos da CBO",
            "Primeiro nível da hierarquia da CBO: um dígito, dez grupos.",
        ),
    },
    "cbo_subgrupo_principal": {
        "path": "cbo-subgrupos-principais.csv",
        **_nivel_cbo(
            "Subgrupos principais da CBO",
            "Segundo nível da hierarquia da CBO, dois dígitos.",
            "cbo_grande_grupo",
        ),
    },
    "cbo_subgrupo": {
        "path": "cbo-subgrupos.csv",
        **_nivel_cbo(
            "Subgrupos da CBO",
            "Terceiro nível da hierarquia da CBO, três dígitos.",
            "cbo_subgrupo_principal",
        ),
    },
    "cbo_familia": {
        "path": "cbo-familias.csv",
        **_nivel_cbo(
            "Famílias da CBO",
            "Quarto nível da hierarquia da CBO, quatro dígitos. "
            "A família é o prefixo do código da ocupação.",
            "cbo_subgrupo",
        ),
    },
    "cbo_area": {
        "path": "cbo-areas.csv",
        "title": "Grandes áreas de competência da CBO",
        "description": (
            "Frentes de trabalho do perfil ocupacional, uma linha por "
            "par ocupação e sigla."
        ),
        "fields": [
            campo("ocupacao", "string", CODIGO_OCUPACAO),
            campo("sigla", "string", "Sigla da grande área de competência, como publicada."),
            campo("nome", "string", "Nome da grande área de competência."),
        ],
        "primaryKey": ["ocupacao", "sigla"],
        "foreignKeys": [fk("ocupacao", "cbo_ocupacao", "codigo")],
    },
    "cbo_atividade": {
        "path": "cbo-atividades.csv",
        "title": "Atividades do perfil ocupacional da CBO",
        "description": (
            "Atividades de cada grande área de competência. O número é o da "
            "fonte, com lacunas e eventual repetição (D017)."
        ),
        "fields": [
            campo("ocupacao", "string", CODIGO_OCUPACAO),
            campo("sigla", "string", "Sigla da grande área de competência a que a atividade pertence."),
            campo(
                "numero",
                "integer",
                "Número da atividade como publicado na fonte, não a posição na lista (D017).",
            ),
            campo("descricao", "string", "Descrição da atividade, como publicada."),
        ],
        "foreignKeys": [
            fk("ocupacao", "cbo_ocupacao", "codigo"),
            fk(["ocupacao", "sigla"], "cbo_area", ["ocupacao", "sigla"]),
        ],
    },
    "cbo_ocupacao": {
        "path": "cbo-ocupacoes.csv",
        "title": "Ocupações da CBO",
        "description": "Espinha enumerativa: uma linha por ocupação da CBO 2002.",
        "fields": [
            campo("codigo", "string", CODIGO_OCUPACAO),
            campo("titulo", "string", TITULO),
            campo(
                "familia",
                "string",
                "Código da família (quatro dígitos), prefixo do código da ocupação, como texto (D001).",
            ),
            campo("vigencia", "string", "Status de vigência do registro: vigente ou revogado."),
        ],
        "primaryKey": ["codigo"],
        "foreignKeys": [fk("familia", "cbo_familia", "codigo")],
    },
    "cbo_sinonimo": {
        "path": "cbo-sinonimos.csv",
        "title": "Sinônimos da CBO",
        "description": (
            "Denominações alternativas da ocupação. A relação é 1:N e a fonte "
            "pode repetir um sinônimo; por isso não há chave primária."
        ),
        "fields": [
            campo("ocupacao", "string", CODIGO_OCUPACAO),
            campo("sinonimo", "string", "Denominação alternativa, como publicada na fonte."),
        ],
        "foreignKeys": [fk("ocupacao", "cbo_ocupacao", "codigo")],
    },
    "qbq_ocupacao": {
        "path": "qbq-ocupacoes.csv",
        "title": "Ocupações do QBQ",
        "description": (
            "Ocupações com a qualificação do QBQ. Nível vazio significa que a "
            "ocupação não foi classificada."
        ),
        "fields": [
            campo("codigo", "string", CODIGO_OCUPACAO),
            campo("titulo", "string", TITULO),
            campo("sintese", "string", "Síntese da ocupação no QBQ. Vazia quando a fonte não traz."),
            campo(
                "perfil_ocupacional",
                "string",
                "Perfil ocupacional textual publicado no QBQ. Vazio quando a fonte não traz.",
            ),
            campo(
                "nivel_conhecimento",
                "integer",
                "Nível de qualificação do conhecimento, de 1 a 8. Vazio quando não classificado.",
            ),
            campo(
                "nivel_habilidade",
                "integer",
                "Nível de qualificação da habilidade, de 1 a 8. Vazio quando não classificado.",
            ),
            campo(
                "nivel_atitude",
                "integer",
                "Nível de qualificação da atitude, de 1 a 8. Vazio quando não classificado.",
            ),
            campo(
                "nivel_qualificacao",
                "integer",
                "Nível de qualificação da ocupação, de 1 a 8. Vazio quando não classificado.",
            ),
            campo("vigencia", "string", "Status de vigência do registro: vigente ou revogado."),
        ],
        "primaryKey": ["codigo"],
    },
    "qbq_conhecimento": {
        "path": "qbq-conhecimentos.csv",
        "title": "Conhecimentos exigidos por ocupação",
        "description": (
            "Itens de conhecimento do QBQ. O código do item aponta para o "
            "vocabulário nomeado em taxonomia; não há uma chave estrangeira "
            "única porque o alvo depende dessa coluna e, nos dois vocabulários "
            "de conhecimento, o mesmo código se repete entre níveis."
        ),
        "fields": [
            campo("ocupacao", "string", CODIGO_OCUPACAO),
            campo(
                "taxonomia",
                "string",
                "Vocabulário de conhecimento: conhecimentos-i (níveis 1 a 5) ou conhecimentos-ii (níveis 6 a 8).",
            ),
            campo(
                "item",
                "string",
                "Código do item no vocabulário indicado por taxonomia, preservado como texto.",
            ),
            campo("profundidade", "integer", "Grau de profundidade, de 1 a 5. Vazio quando a fonte não informa."),
            campo("frequencia", "integer", "Grau de frequência, de 1 a 5. Vazio quando a fonte não informa."),
            campo("importancia", "integer", "Grau de importância, de 1 a 5. Vazio quando a fonte não informa."),
            campo(
                "descricao",
                "string",
                "Descrição inline. Nos baldes 'outros' (segmento 90 ou 99) distingue itens de mesmo código (D009).",
            ),
        ],
        "foreignKeys": [fk("ocupacao", "qbq_ocupacao", "codigo")],
    },
    "qbq_habilidade": {
        "path": "qbq-habilidades.csv",
        "title": "Habilidades exigidas por ocupação",
        "description": "Itens de habilidade do QBQ, um por linha, com graus quando a fonte os traz.",
        "fields": [
            campo("ocupacao", "string", CODIGO_OCUPACAO),
            campo("item", "string", "Código da habilidade no vocabulário controlado, preservado como texto."),
            campo("frequencia", "integer", "Grau de frequência, de 1 a 5. Vazio quando a fonte não informa."),
            campo("importancia", "integer", "Grau de importância, de 1 a 5. Vazio quando a fonte não informa."),
            campo(
                "descricao",
                "string",
                "Descrição inline. Nos baldes 'outros' distingue itens de mesmo código (D009).",
            ),
        ],
        "foreignKeys": [
            fk("ocupacao", "qbq_ocupacao", "codigo"),
            fk("item", "qbq_vocabulario_habilidades", "codigo"),
        ],
    },
    "qbq_atitude": {
        "path": "qbq-atitudes.csv",
        "title": "Atitudes exigidas por ocupação",
        "description": "Itens de atitude do QBQ. A atitude no QBQ é escala de autonomia, não catálogo de comportamento.",
        "fields": [
            campo("ocupacao", "string", CODIGO_OCUPACAO),
            campo("item", "string", "Código da atitude no vocabulário controlado, preservado como texto."),
            campo("importancia", "integer", "Grau de importância, de 1 a 5. Vazio quando a fonte não informa."),
            campo(
                "descricao",
                "string",
                "Descrição inline. Nos baldes 'outros' distingue itens de mesmo código (D009).",
            ),
        ],
        "foreignKeys": [
            fk("ocupacao", "qbq_ocupacao", "codigo"),
            fk("item", "qbq_vocabulario_atitudes", "codigo"),
        ],
    },
    "qbq_vocabulario_conhecimentos_i": {
        "path": "qbq-vocabulario-conhecimentos-i.csv",
        "title": "Vocabulário de conhecimentos I",
        "description": (
            "Taxonomia de conhecimentos para ocupações de nível 1 a 5. "
            "O código se repete entre níveis, então a chave é nível mais código "
            "e o pai não vira chave estrangeira."
        ),
        "fields": _campos_vocabulario(),
        "primaryKey": ["nivel", "codigo"],
    },
    "qbq_vocabulario_conhecimentos_ii": {
        "path": "qbq-vocabulario-conhecimentos-ii.csv",
        "title": "Vocabulário de conhecimentos II",
        "description": (
            "Taxonomia de conhecimentos para ocupações de nível 6 a 8, com "
            "elementos no estilo CNPq. O código se repete entre níveis, então "
            "a chave é nível mais código."
        ),
        "fields": _campos_vocabulario(),
        "primaryKey": ["nivel", "codigo"],
    },
    "qbq_vocabulario_habilidades": {
        "path": "qbq-vocabulario-habilidades.csv",
        "title": "Vocabulário de habilidades",
        "description": "Domínios, categorias e habilidades do QBQ. O código é único no arquivo.",
        "fields": _campos_vocabulario(),
        "primaryKey": ["nivel", "codigo"],
        "foreignKeys": [fk("pai", "qbq_vocabulario_habilidades", "codigo")],
    },
    "qbq_vocabulario_atitudes": {
        "path": "qbq-vocabulario-atitudes.csv",
        "title": "Vocabulário de atitudes",
        "description": "Categorias e atitudes do QBQ, escala de autonomia e supervisão. O código é único no arquivo.",
        "fields": _campos_vocabulario(),
        "primaryKey": ["nivel", "codigo"],
        "foreignKeys": [fk("pai", "qbq_vocabulario_atitudes", "codigo")],
    },
    "qbq_conceito": {
        "path": "qbq-conceitos.csv",
        "title": "Conceitos oficiais das habilidades",
        "description": (
            "Definição oficial de cada termo de habilidade, vinda do PDF de "
            "conceitos. Baldes 'outros' não têm conceito (D012)."
        ),
        "fields": [
            campo("vocabulario", "string", "Dimensão a que o conceito pertence. Nesta publicação, habilidades."),
            campo("nivel", "string", "Nível do termo no vocabulário: dominios, categorias ou habilidades."),
            campo("codigo", "string", "Código do termo no vocabulário, preservado como texto."),
            campo("termo", "string", "Rótulo do termo no documento de conceitos."),
            campo("conceito", "string", "Definição oficial do termo."),
        ],
        "primaryKey": ["nivel", "codigo"],
        "foreignKeys": [fk("codigo", "qbq_vocabulario_habilidades", "codigo")],
    },
    "qbq_nao_classificada": {
        "path": "qbq-nao-classificadas.csv",
        "title": "Ocupações sem nível no QBQ",
        "description": "Ocupações que a fonte declara sem classificação de nível, com a justificativa oficial.",
        "fields": [
            campo("codigo", "string", CODIGO_OCUPACAO),
            campo("titulo", "string", TITULO),
            campo("justificativa", "string", "Justificativa oficial para a ausência de nível no QBQ."),
        ],
        "primaryKey": ["codigo"],
        "foreignKeys": [fk("codigo", "qbq_ocupacao", "codigo")],
    },
    "cobertura_qbq_cbo": {
        "path": "cobertura-qbq-cbo.csv",
        "title": "Divergências entre QBQ e CBO",
        "description": (
            "Ocupações em que as duas camadas não coincidem na mesma chave. "
            "Não há chave estrangeira: o código pode existir em só uma delas (D015)."
        ),
        "fields": [
            campo("codigo", "string", CODIGO_OCUPACAO),
            campo(
                "situacao",
                "string",
                "Relação entre as camadas: so_cbo, so_qbq ou titulo_divergente (D015).",
            ),
            campo("titulo_cbo", "string", "Título na CBO. Vazio quando a ocupação não existe nessa camada."),
            campo("titulo_qbq", "string", "Título no QBQ. Vazio quando a ocupação não existe nessa camada."),
        ],
        "primaryKey": ["codigo"],
    },
}
