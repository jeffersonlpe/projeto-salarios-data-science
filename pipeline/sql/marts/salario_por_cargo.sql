CREATE OR REPLACE TABLE marts.salario_por_cargo AS
SELECT
    c.id_cargo,
    c.job_title,
    AVG(s.salary_in_usd)::DOUBLE AS salario_medio_usd,
    COUNT(*)::BIGINT AS quantidade_vagas
FROM raw.salarios AS s
INNER JOIN raw.cargos AS c
    ON s.job_title = c.job_title
GROUP BY c.id_cargo, c.job_title;
