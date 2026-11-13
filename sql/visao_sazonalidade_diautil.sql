-- Retorna vendas por (filial, dia útil do mês, ano, mês)
WITH DatasBase AS (
    SELECT DISTINCT CONVERT(date, DataEntradaSaida) AS Data
    FROM Movimento
    WHERE DataEntradaSaida >= '2000-01-01'
),
DiasUteis AS (
    SELECT 
        Data,
        YEAR(Data) AS Ano,
        MONTH(Data) AS Mes,
        ROW_NUMBER() OVER (PARTITION BY YEAR(Data), MONTH(Data) ORDER BY Data) AS DiaUtil
    FROM DatasBase
    -- Considera Segunda a Sexta como dias úteis (1 a 5)
    WHERE ((DATEPART(WEEKDAY, Data) + @@DATEFIRST - 2) % 7) + 1 BETWEEN 1 AND 5
)
SELECT 
    m.CodFilial,
    du.DiaUtil,
    YEAR(m.DataEntradaSaida) AS Ano,
    MONTH(m.DataEntradaSaida) AS Mes,
    SUM(ISNULL(m.TotMov, 0) - ISNULL(m.TotCancel, 0)) AS Valor,
    COUNT(DISTINCT CONVERT(date, m.DataEntradaSaida)) AS QtdDias
FROM Movimento m
INNER JOIN DiasUteis du ON CONVERT(date, m.DataEntradaSaida) = du.Data
WHERE m.TipoMov = '2.4'
    AND m.NfeStatus = 'U'
    AND m.DtFinalizacao IS NOT NULL
    AND m.CodFilial IN (1, 2, 3, 4)
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    -- O filtro de hora NÃO é aplicado aqui, para manter a integridade do dia inteiro
    AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
GROUP BY m.CodFilial, du.DiaUtil, YEAR(m.DataEntradaSaida), MONTH(m.DataEntradaSaida)
ORDER BY m.CodFilial, du.DiaUtil, Ano, Mes