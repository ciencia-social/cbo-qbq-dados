<!--
Obrigado por contribuir. Este repositório tem uma regra estruturante:
dados/ e derivados/ são GERADOS. Correção de dado acontece no pipeline
(ou na fonte arquivada), nunca por edição manual do JSON ou do CSV.
-->

## O que este PR faz

<!-- Uma ou duas frases. Se resolve uma issue, cite: Resolve #N -->

## Categoria

<!-- Marque uma; é a mesma taxonomia do CHANGELOG.md -->

- [ ] **Normativa** — a fonte oficial mudou (gera nova versão `dados-AAAA.MM`)
- [ ] **Correção** — extração ou derivação divergia da fonte
- [ ] **Schema** — o formato mudou (indique major/minor/patch)
- [ ] **Editorial** — documentação, decisões, textos do repositório

## Fonte oficial

<!--
Toda mudança de dado precisa apontar a fonte: arquivo em fontes/, aba e
linha, ou URL do normativo. Se a fonte oficial é que está inconsistente,
descreva a interpretação adotada — ela vira uma entrada em DECISOES.md.
-->

## Checagens

- [ ] `python3 pipeline/extrair_qbq.py` e `git diff --exit-code dados/` limpo
      (o commitado reproduz da fonte)
- [ ] `python3 pipeline/validar_schema.py` — 0 falhas
- [ ] `python3 pipeline/validar.py` — 0 erros; avisos novos, se houver, estão
      justificados abaixo
- [ ] `python3 pipeline/derivar.py` e derivados regerados no commit
- [ ] Não editei `dados/` nem `derivados/` à mão
- [ ] Se mudou o formato: `docs/modelo-de-dados.md`, os schemas e
      `docs/versionamento.md` acompanham
- [ ] Se mudou uma decisão de interpretação: `DECISOES.md` tem a entrada nova
- [ ] `CHANGELOG.md` atualizado

## Avisos novos do validador

<!--
O baseline atual é 0 erros e 7 avisos (3 ocupações do D010 em duas checagens
cada, e a anomalia de taxonomia da ocupação 254110). Se seu PR muda essa
contagem, explique por quê.
-->
