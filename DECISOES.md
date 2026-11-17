# Registro de decisões

Toda decisão de modelagem que não decorre trivialmente da fonte oficial fica
registrada aqui, numerada, com contexto e alternativas consideradas. Formato
inspirado no `bncc-dados`.

---

## D001 — Código CBO normalizado para 6 dígitos com zero à esquerda

**Contexto.** A aba `Layout` do XLSX oficial define `CodCBO` como `<999999>`
com amplitude `010105 a 992225`. Porém, células das abas de dados ora vêm como
texto (`"312105"`), ora como número (`10105`, sem o zero à esquerda).

**Decisão.** Normalizar todo código para *string* de 6 dígitos com
`zfill(6)`, conforme o próprio Layout. Sem hífen: a forma de exibição oficial
`XXXX-XX` é derivável deterministicamente e será tratada na camada de
apresentação/pacotes.

## D002 — Aparar espaços nas pontas; conteúdo interno intocado

**Contexto.** A fonte traz códigos e descrições com espaços espúrios
(`"02  "`, `" COMUNICAÇÃO"`).

**Decisão.** Aplicar apenas `strip()` nas pontas (e normalizar `\r\n`).
Nenhuma outra alteração — sem mudança de caixa, sem colapso de espaços
internos — para manter fidelidade ao texto oficial.

## D003 — `codArea` de Conhecimento II sem ponto terminal

**Contexto.** A aba `Conhecimento II` traz `codArea` como `"1."`, mas o
Layout define o código como `<9>` com amplitude `1 a 9`.

**Decisão.** Remover a pontuação terminal, seguindo a especificação do
próprio Layout. Registrado como normalização de código, não de conteúdo.

## D004 — Duas taxonomias de conhecimento, mantidas separadas

**Contexto.** O QBQ usa taxonomias diferentes por faixa de nível:
`Conhecimento I` (domínio → área → campo → conhecimento) para ocupações de
nível 1–5 e `Conhecimento II` (área → campo → conhecimento → elemento, nos
moldes da tabela CNPq) para níveis 6–8. Os códigos se sobrepõem entre elas
com significados distintos.

**Decisão.** Honestidade estrutural: dois vocabulários separados
(`conhecimentos-i.json`, `conhecimentos-ii.json`), e cada ocupação declara em
`taxonomia_conhecimento` qual usa. Nenhuma tentativa de unificação — um
crosswalk entre as duas seria trabalho interpretativo, não extração.

## D005 — Descrição canônica por frequência; divergências registradas

**Contexto.** As descrições das taxonomias se repetem a cada linha da
planilha e podem divergir entre ocorrências (grafia, espaços).

**Decisão.** O vocabulário adota a variante mais frequente como descrição
canônica; toda divergência fica registrada em
`dados/qbq/verificacao.json` (`divergencias_vocabulario`), sem apagar a
informação de que a fonte é inconsistente.

## D006 — Graus fora da escala viram `null` com aviso

**Contexto.** O Layout define escalas fechadas (níveis 1–8; graus 1–5).

**Decisão.** Valor fora da escala ou não numérico é gravado como `null` e
registrado em `verificacao.json` (`avisos`), preservando o rastro em vez de
propagar valor inválido ou inventar correção.

## D007 — Nome do arquivo-fonte com data de modificação do documento

**Contexto.** O download oficial chama-se `download.xlsx`, sem versão. Os
metadados internos do documento registram criação em 2022-09-21 e última
modificação em 2025-03-18.

**Decisão.** Arquivar como `fontes/qbq/qbq-2025-03.xlsx` (data de modificação
do documento), com checksum SHA-256 e data de captura registrados em
`fontes/README.md`.

## D008 — Não-classificadas permanecem também em `ocupacoes/`

**Contexto.** As 52 ocupações da aba `Ocupações não classificada` **também**
constam da aba `Ocupação` — com título, mas com síntese, perfil e todos os
níveis vazios, e sem nenhum item CHA. Verificado na extração de 2026-08-28.

**Decisão.** Fidelidade à fonte: os registros permanecem em `ocupacoes/`
(com níveis `null`) e em `nao-classificadas.json` (com a justificativa). O
contrato passa a ser de **coerência**, verificado no CI: quem está em
`nao-classificadas` precisa ter todos os níveis nulos e zero competências; e
toda ocupação sem nenhum nível precisa estar em `nao-classificadas`.

## D009 — Códigos com segmento `90` ou `99` são baldes de "outros"

**Contexto.** A nota da aba `Layout` diz que códigos `90` representam
"outros". Na prática o padrão é mais amplo: códigos com **algum segmento
`90` ou `99`** (ex.: `06.01.02.90`, `06.01.99.01`, `02.90.01`) se repetem
para a mesma ocupação com descrições distintas — o conteúdo real do item está
na **descrição da linha**, não no código (ex.: "OUTROS ELEMENTOS (DIREITO
PÚBLICO) DIREITO AMBIENTAL"). A maioria das divergências de descrição nos
vocabulários vem desses códigos.

**Decisão.** Itens de balde carregam o campo `descricao` inline
(obrigatório, verificado no CI); para eles o código não é chave única e a
duplicidade é permitida. Nos demais itens, `descricao` aparece apenas quando
a grafia da linha diverge da canônica do vocabulário (nenhuma variante é
descartada). Nos vocabulários, a entrada do balde mantém a variante mais
frequente como rótulo, com as variantes preservadas em `verificacao.json`.

## D010 — Três lideranças comunitárias sem nível e sem justificativa

**Contexto.** `113005` (Cacique), `113010` (Líder de comunidade caiçara) e
`113015` (Membro de liderança quilombola) constam da aba `Ocupação` sem
nenhum nível e sem itens CHA, mas **não** aparecem na aba de não
classificadas — diferentemente das 52 ocupações com justificativa oficial.

**Decisão.** Lacuna da fonte, não do dataset: os registros ficam em
`ocupacoes/` com níveis `null`, e o validador emite **aviso** (não erro).
Não inventamos justificativa nem as movemos para `nao-classificadas.json`,
que contém exatamente o que a fonte declara.

## D011 — Conceitos em camada própria, chaveada pelo vocabulário

**Contexto.** O QBQ publica as definições de cada habilidade em documento
separado da planilha (o PDF de conceitos e terminologia, também disponível na
página de Conceitos do portal de consulta). São duas fontes distintas sobre os
mesmos termos: a planilha dá a taxonomia e as atribuições por ocupação; o PDF
dá o significado de cada termo.

**Decisão.** Os conceitos ficam em `dados/qbq/conceitos/<dimensao>.json`, uma
camada à parte dos vocabulários, chaveada pelos mesmos códigos. Não são
mesclados no vocabulário porque vêm de outra fonte, com outra data e outro
checksum — juntá-los apagaria a rastreabilidade de qual documento afirma o
quê. Cada registro guarda `codigo` (do vocabulário), `termo` (o rótulo como
grafado no documento de conceitos) e `conceito` (a definição transcrita). O CI
exige cobertura total: todo termo do vocabulário que não seja balde "outros"
tem de ter conceito, e todo conceito tem de apontar para termo existente.

Hoje só a dimensão `habilidades` tem documento de conceitos publicado. Quando
houver equivalente para conhecimentos e atitudes, entram como novos arquivos
na mesma pasta, sem mudança de schema.

## D012 — Baldes "outros" não têm conceito oficial

**Contexto.** Os baldes de segmento `90` (D009) existem para o preenchimento
livre da fonte e não aparecem no documento de conceitos.

**Decisão.** Ficam fora de `conceitos/`, e o validador trata como **erro** a
presença de conceito para um balde — sinal de erro de parsing. A ausência de
definição é fato da fonte, não lacuna a preencher.

## D013 — Grafias divergentes entre planilha e PDF: as duas são preservadas

**Contexto.** Os dois documentos oficiais têm erros de digitação em rótulos, em
direções opostas: a planilha traz `RACIOCÍONIO CIENTÍFICO` (01.03.06, o PDF
grafa "Raciocínio científico") e o PDF traz "Habilidades Sensorias" (categoria
03.03, a planilha grafa `HABILIDADES SENSORIAIS`). O casamento exato de
rótulos falharia nesses dois casos.

**Decisão.** O extrator casa o rótulo por texto exato e, só quando isso falha,
pela janela de palavras mais à esquerda com similaridade ≥ 0,90. Nenhuma das
duas grafias é corrigida: o vocabulário mantém a da planilha, o conceito
mantém a do PDF em `termo`, e toda diferença encontrada é listada em
`divergencias`, no próprio arquivo de conceitos, com aviso no validador. Assim
a divergência fica auditável em vez de escondida no código do extrator.

## D014 — Fonte sem data interna mantém o nome original

**Contexto.** O D007 manda nomear o arquivo-fonte com a data de modificação do
documento. Os CSVs da CBO não permitem isso: as respostas HTTP do gov.br não
trazem `Last-Modified` e o CSV não tem metadado interno de versão. A única
"versão" declarada é a da própria classificação (CBO 2002), já presente no
nome original.

**Decisão.** Quando a fonte não expõe data própria, o arquivo entra em
`fontes/` com o nome original (`cbo2002-ocupacao.csv`), e a rastreabilidade
fica na data de captura e no checksum registrados em `fontes/README.md`. A
página de downloads vigente na captura é arquivada ao lado, como evidência das
URLs de origem — URLs do gov.br mudam com reorganizações administrativas.
Fonte substituída por versão nova = novo checksum e nova versão de dados, com
a diferença visível no diff.

## D015 — Divergências entre QBQ e CBO são dado, não defeito

**Contexto.** As duas camadas usam a mesma chave (código CBO de 6 dígitos) e
vêm de capturas diferentes da mesma classificação: a espinha da CBO é de
2026-11-17, a planilha do QBQ é de 2025-03-18. Resultado do confronto: 25
ocupações existem na CBO e não no QBQ (vinte delas em sete famílias inteiras do
grande grupo 2), 4 existem no QBQ e não na CBO, e 35 têm título diferente sob o
mesmo código.

**Decisão.** Nenhuma das camadas é ajustada para caber na outra: não criamos
registro faltante, não removemos o que sobra e não escolhemos um título
"correto". As diferenças viram **aviso** no validador e tabela em
`derivados/csv/cobertura-qbq-cbo.csv`, com a leitura narrativa em
[`docs/cobertura-qbq-cbo.md`](docs/cobertura-qbq-cbo.md). Três das quatro
ocupações só do QBQ têm aparência de substituídas por códigos novos na CBO, mas
confirmar substituição exige o histórico de alterações (fase 4) — até lá a
hipótese fica registrada como hipótese.

## D016 — `versao_dados` é a publicação em que a camada foi gerada

**Contexto.** A fase 1 publica `dados-2026.11` acrescentando a camada CBO, sem
tocar na camada QBQ, cuja fonte não mudou. Reescrever `versao_dados` nos
arquivos do QBQ exigiria regerá-los, e a regeração reescreveria também
`vigencia.desde` de cada ocupação — que é histórico e tem de continuar
apontando para a publicação em que o registro apareceu.

**Decisão.** O campo `versao_dados` de cada arquivo registra a publicação em
que **aquela camada** foi gerada pela última vez: os arquivos da CBO trazem
`dados-2026.11`, os do QBQ seguem com `dados-2026.08`. A versão do conjunto é a
tag do release e o `CHANGELOG.md`. Quando a camada QBQ for regerada em uma
publicação futura, preservar `vigencia.desde` dos registros existentes é
requisito — mecanismo previsto para a fase 4, junto com o histórico de
alterações.
