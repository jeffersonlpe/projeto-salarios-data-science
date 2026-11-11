CREATE OR REPLACE TABLE marts.salario_por_cargo AS
SELECT
    job_title,
    AVG(salary_in_usd)::DOUBLE AS salario_medio_usd,
    COUNT(*)::BIGINT AS quantidade_vagas
FROM refined.salarios
GROUP BY job_title;
