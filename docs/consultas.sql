-- Consultas de exemplo para derivados/qbq.sqlite (qbq-dados)
-- Gerar o banco: python3 pipeline/derivar.py
-- Rodar:        sqlite3 -box derivados/qbq.sqlite < docs/consultas.sql
--
-- Tabelas: camada CBO  -> cbo_grande_grupo, cbo_subgrupo_principal, cbo_subgrupo,
--                         cbo_familia, cbo_ocupacao, cbo_sinonimo
--          camada QBQ  -> qbq_ocupacao, qbq_conhecimento, qbq_habilidade,
--                         qbq_atitude, qbq_vocabulario_*, qbq_conceito,
--                         qbq_nao_classificada
--          cruzamento  -> cobertura_qbq_cbo
-- A chave entre as camadas é o código CBO de 6 dígitos.


-- 1. Caminho completo da hierarquia, de grande grupo a ocupação.
--    Os níveis são prefixos do código, então o JOIN é por substr().
SELECT o.codigo,
       g.titulo  AS grande_grupo,
       sp.titulo AS subgrupo_principal,
       s.titulo  AS subgrupo,
       f.titulo  AS familia,
       o.titulo  AS ocupacao
FROM cbo_ocupacao o
JOIN cbo_familia f             ON f.codigo  = o.familia
JOIN cbo_subgrupo s            ON s.codigo  = substr(o.codigo, 1, 3)
JOIN cbo_subgrupo_principal sp ON sp.codigo = substr(o.codigo, 1, 2)
JOIN cbo_grande_grupo g        ON g.codigo  = substr(o.codigo, 1, 1)
WHERE o.codigo = '212405';


-- 2. Do nome de mercado ao código oficial: busca por sinônimo.
--    Útil para casar títulos de vaga com a classificação.
SELECT s.sinonimo, o.codigo, o.titulo, q.nivel_qualificacao
FROM cbo_sinonimo s
JOIN cbo_ocupacao o      ON o.codigo = s.ocupacao
LEFT JOIN qbq_ocupacao q ON q.codigo = o.codigo
WHERE s.sinonimo LIKE '%programador%'
ORDER BY s.sinonimo;


-- 3. Perfil de habilidades de uma ocupação, com a definição oficial do termo.
--    qbq_conceito traz a definição publicada no PDF de conceitos do QBQ.
SELECT c.termo, h.importancia, h.frequencia, c.conceito
FROM qbq_habilidade h
JOIN qbq_conceito c ON c.codigo = h.item AND c.nivel = 'habilidades'
WHERE h.ocupacao = '212405'
ORDER BY h.importancia DESC, h.frequencia DESC, c.termo
LIMIT 10;


-- 4. Consulta transversal: quem exige um conhecimento específico em grau alto.
--    Conhecimento II é a taxonomia das ocupações de nível 6-8; para níveis
--    1-5 use qbq_vocabulario_conhecimentos_i e nivel = 'conhecimentos'.
SELECT o.codigo, o.titulo, k.profundidade, k.importancia
FROM qbq_conhecimento k
JOIN qbq_ocupacao o ON o.codigo = k.ocupacao
JOIN qbq_vocabulario_conhecimentos_ii v
     ON v.codigo = k.item AND v.nivel = 'elementos'
WHERE v.descricao LIKE 'ESTAT%' AND k.profundidade >= 4
ORDER BY k.profundidade DESC, o.titulo;


-- 5. Agregado por grande grupo: nível de qualificação médio.
--    Usa a espinha da CBO para agrupar e o QBQ para medir.
SELECT g.codigo,
       g.titulo AS grande_grupo,
       count(q.codigo)                  AS ocupacoes,
       round(avg(q.nivel_qualificacao), 2) AS nivel_medio,
       max(q.nivel_qualificacao)        AS maximo
FROM cbo_grande_grupo g
JOIN cbo_ocupacao o ON substr(o.codigo, 1, 1) = g.codigo
JOIN qbq_ocupacao q ON q.codigo = o.codigo AND q.nivel_qualificacao IS NOT NULL
GROUP BY g.codigo
ORDER BY nivel_medio DESC;


-- 6. Onde as duas camadas divergem (D015): contagem por situação.
--    so_cbo = existe na CBO e não no QBQ; so_qbq = o inverso;
--    titulo_divergente = mesmo código, títulos diferentes.
SELECT situacao, count(*) AS n
FROM cobertura_qbq_cbo
GROUP BY situacao;

-- 6b. As divergências em si, para inspeção.
SELECT codigo, situacao, titulo_cbo, titulo_qbq
FROM cobertura_qbq_cbo
WHERE situacao <> 'titulo_divergente'
ORDER BY situacao, codigo;


-- 7. O que distingue uma família: importância média na família contra a
--    média do dataset inteiro. Família 2124 = analistas de TI.
WITH familia AS (
  SELECT h.item, avg(h.importancia) AS imp_fam
  FROM qbq_habilidade h
  JOIN cbo_ocupacao o ON o.codigo = h.ocupacao
  WHERE o.familia = '2124'
  GROUP BY h.item),
geral AS (
  SELECT item, avg(importancia) AS imp_geral
  FROM qbq_habilidade GROUP BY item)
SELECT c.termo,
       round(f.imp_fam, 2)              AS familia_2124,
       round(g.imp_geral, 2)            AS media_geral,
       round(f.imp_fam - g.imp_geral, 2) AS diferenca
FROM familia f
JOIN geral g USING (item)
JOIN qbq_conceito c ON c.codigo = f.item AND c.nivel = 'habilidades'
ORDER BY diferenca DESC
LIMIT 10;


-- 8. Ocupações com perfil de habilidades parecido, normalizado por Jaccard.
--    Contar só as habilidades em comum premiaria ocupações com muitos itens;
--    dividir pela união corrige isso.
WITH alta AS (
  SELECT ocupacao, item FROM qbq_habilidade WHERE importancia >= 4),
alvo AS (
  SELECT item FROM alta WHERE ocupacao = '212405')
SELECT o.codigo, o.titulo,
       count(*) AS em_comum,
       round(100.0 * count(*) /
             ((SELECT count(*) FROM alvo)
              + (SELECT count(*) FROM alta a2 WHERE a2.ocupacao = a.ocupacao)
              - count(*)), 1) AS jaccard_pct
FROM alta a
JOIN qbq_ocupacao o ON o.codigo = a.ocupacao
WHERE a.item IN (SELECT item FROM alvo) AND a.ocupacao <> '212405'
GROUP BY a.ocupacao
ORDER BY jaccard_pct DESC, em_comum DESC
LIMIT 10;


-- 9. Ocupação sem classificação do QBQ, com a justificativa oficial quando há.
SELECT o.codigo, o.titulo,
       CASE WHEN n.codigo IS NOT NULL THEN n.justificativa
            WHEN q.codigo IS NULL     THEN '(ausente da camada QBQ — ver cobertura_qbq_cbo)'
            ELSE '(classificada)' END AS situacao
FROM cbo_ocupacao o
LEFT JOIN qbq_ocupacao q        ON q.codigo = o.codigo
LEFT JOIN qbq_nao_classificada n ON n.codigo = o.codigo
WHERE q.nivel_qualificacao IS NULL
ORDER BY o.codigo
LIMIT 15;
