CREATE OR REPLACE TABLE marts.salario_por_experiencia AS
SELECT
    experience_level,
    AVG(salary_in_usd)::DOUBLE AS salario_medio_usd
FROM refined.salarios
GROUP BY experience_level;
