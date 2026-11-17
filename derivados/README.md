# Derivados

Gerados por `pipeline/derivar.py` a partir de `dados/` — **nunca editar à mão**. Todos expõem as mesmas tabelas: `qbq_ocupacao`, `qbq_conhecimento`, `qbq_habilidade`, `qbq_atitude`, `qbq_vocabulario_*`, `qbq_conceito`, `qbq_nao_classificada`, mais a camada CBO (`cbo_grande_grupo`, `cbo_subgrupo_principal`, `cbo_subgrupo`, `cbo_familia`, `cbo_ocupacao`, `cbo_sinonimo`, `cbo_area`, `cbo_atividade`) e `cobertura_qbq_cbo`, que lista as divergências entre as duas camadas na mesma chave (D015).

## O que está no git e o que não está

| Formato | No git? | Como obter |
|---|---|---|
| CSVs (`csv/`, 28 MB) | Sim | Clone ou raw link |
| `MANIFEST.sha256` | Sim | Clone |
| `qbq.sqlite` (29 MB) | **Não** | Anexo do release, ou `python3 pipeline/derivar.py` |
| `qbq.sql` (38 MB) | **Não** | Anexo do release, ou `python3 pipeline/derivar.py` |

Os dois arquivos monolíticos ficam fora do histórico do git de propósito: são conteúdo gerado, e cada nova versão `dados-AAAA.MM` acrescentaria ao histórico uma cópia inteira dos dois — o clone cresceria dezenas de MB por publicação sem ganho de informação, já que `dados/` (a fonte da verdade) e os CSVs já estão versionados. Eles são anexados a cada release pelo workflow `.github/workflows/release.yml`.

## Conferindo o que você baixou

`MANIFEST.sha256` é versionado e regenerado pelo pipeline:

```sh
gunzip qbq.sqlite.gz qbq.sql.gz
sha256sum -c MANIFEST.sha256    # shasum -a 256 -c no macOS
```

Uma ressalva honesta sobre as duas linhas do manifesto: `qbq.sql` é texto escrito por Python puro e regenera byte a byte idêntico — o CI confere essa linha em cada push. Já `qbq.sqlite` é um binário cuja serialização depende da versão da `libsqlite` que o gerou; o conteúdo é o mesmo, mas os bytes podem diferir entre máquinas. Por isso o CI não trava nessa linha, e o manifesto autoritativo para um release é o que vai anexado a ele.
