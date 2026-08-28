# Versionamento

Dois eixos independentes, como no bncc-dados:

- **Versão de conteúdo** — `dados-AAAA.MM` (ex.: `dados-2026.08`): identifica
  a publicação do dataset. Muda quando a fonte oficial muda ou uma correção
  de extração é aplicada.
- **Versão de schema** — `schema-vX.Y.Z` (semver): muda quando o *formato*
  muda. Major = quebra de compatibilidade; minor = campo novo opcional;
  patch = correção de descrição.

Versão atual: `dados-2026.08` · `schema-v0.1.0` (pré-1.0: o formato ainda
pode mudar sem major).

## Vigência

Registros **nunca são deletados**. Quando uma ocupação sai da fonte oficial,
seu registro recebe `vigencia.status = "revogado"` e `vigencia.ate` com a
versão em que deixou de valer. Códigos nunca são reutilizados. Isso habilita
consultas point-in-time quando o histórico de alterações da CBO entrar
(fase 4).

## Releases

Cada versão de conteúdo vira uma tag `dados-AAAA.MM` e um release no GitHub.
`CHANGELOG.md` resume o que mudou.

Empurrar a tag dispara `.github/workflows/release.yml`, que reconstrói tudo a
partir da fonte arquivada, revalida e anexa ao release `qbq.sql.gz`,
`qbq.sqlite.gz` e `MANIFEST.sha256`. Esses dois derivados monolíticos não são
versionados no git — o motivo e a forma de conferir os checksums estão em
[`derivados/README.md`](../derivados/README.md).
