# Versionamento

Dois eixos independentes, como no bncc-dados:

- **Versão de conteúdo** — `dados-AAAA.MM` (ex.: `dados-2026.08`): identifica a publicação do dataset. Muda quando a fonte oficial muda ou uma correção de extração é aplicada. Duas publicações no mesmo mês recebem sufixo sequencial — `dados-2026.11.1` é a segunda de novembro (D018).
- **Versão de schema** — `schema-vX.Y.Z` (semver): muda quando o *formato* muda. Major = quebra de compatibilidade; minor = campo novo opcional; patch = correção de descrição.

Versão atual: `dados-2026.11.2` · `schema-v0.3.0` (pré-1.0: o formato ainda pode mudar sem major).

O campo `versao_dados` **dentro de cada arquivo** indica a publicação em que aquela camada foi gerada pela última vez, e não a publicação corrente: os arquivos do perfil trazem `dados-2026.11.1`, os da espinha da CBO `dados-2026.11` e os do QBQ seguem em `dados-2026.08`, porque a fonte do QBQ não mudou e regerá-los reescreveria `vigencia.desde` dos registros (D016). A versão do conjunto é a tag do release.

## Identificadores

Três identificadores nomeiam a mesma publicação, cada um com um papel. A tag git fixa o commit. O DOI de versão fixa o conteúdo depositado daquela tag no Zenodo e não se move. O DOI de conceito identifica o dataset como obra contínua e resolve sempre para a versão mais recente; é o identificador do selo do README (D019). O selo entra quando esse número existir.

As tags `dados-2026.08`, `dados-2026.11` e `dados-2026.11.1` foram publicadas antes da integração com o Zenodo e não têm DOI. A primeira versão com identificador persistente é `dados-2026.11.2`. O número em si entra nos metadados quando for reservado; até lá `VERSAO.json` grava os dois campos vazios.

## Vigência

Registros **nunca são deletados**. Quando uma ocupação sai da fonte oficial, seu registro recebe `vigencia.status = "revogado"` e `vigencia.ate` com a versão em que deixou de valer. Códigos nunca são reutilizados. Isso habilita consultas point-in-time quando o histórico de alterações da CBO entrar (fase 4).

## Releases

Cada versão de conteúdo vira uma tag `dados-AAAA.MM` e um release no GitHub. `CHANGELOG.md` resume o que mudou.

Empurrar a tag dispara `.github/workflows/release.yml`, que reconstrói tudo a partir da fonte arquivada, revalida e anexa ao release `qbq.sql.gz`, `qbq.sqlite.gz` e `MANIFEST.sha256`. Esses dois derivados monolíticos não são versionados no git — o motivo e a forma de conferir os checksums estão em [`derivados/README.md`](../derivados/README.md).
