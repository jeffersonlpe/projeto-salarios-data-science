CREATE OR REPLACE TABLE refined.salarios AS
SELECT
    CAST(work_year AS INTEGER) AS work_year,
    TRIM(CAST(experience_level AS VARCHAR)) AS experience_level,
    TRIM(CAST(employment_type AS VARCHAR)) AS employment_type,
    TRIM(CAST(job_title AS VARCHAR)) AS job_title,
    CAST(salary AS BIGINT) AS salary,
    TRIM(CAST(salary_currency AS VARCHAR)) AS salary_currency,
    CAST(salary_in_usd AS BIGINT) AS salary_in_usd,
    TRIM(CAST(employee_residence AS VARCHAR)) AS employee_residence,
    CAST(remote_ratio AS SMALLINT) AS remote_ratio,
    TRIM(CAST(company_location AS VARCHAR)) AS company_location,
    TRIM(CAST(company_size AS VARCHAR)) AS company_size
FROM raw.salarios;
