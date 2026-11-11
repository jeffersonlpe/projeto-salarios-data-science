CREATE OR REPLACE TABLE marts.salario_por_pais AS
SELECT
    company_location,
    AVG(salary_in_usd)::DOUBLE AS salario_medio_usd
FROM refined.salarios
GROUP BY company_location;
