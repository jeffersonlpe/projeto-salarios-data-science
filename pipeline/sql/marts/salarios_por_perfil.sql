CREATE OR REPLACE TABLE marts.salarios_por_perfil AS
SELECT
    c.id_cargo,
    c.job_title,
    s.experience_level,
    s.company_size,
    AVG(s.salary_in_usd)::DOUBLE AS salario_medio_usd,
    MAX(s.salary_in_usd)::BIGINT AS maior_salario_usd,
    COUNT(*)::BIGINT AS quantidade_vagas
FROM refined.salarios AS s
INNER JOIN raw.cargos AS c
    ON s.job_title = c.job_title
GROUP BY
    c.id_cargo,
    c.job_title,
    s.experience_level,
    s.company_size;
