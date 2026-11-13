-- Retorna vendas por (filial, dia da semana, ano, mês) para o cálculo do índice de sazonalidade
-- DiaSemana: 1=Segunda, 2=Terça, 3=Quarta, 4=Quinta, 5=Sexta, 6=Sábado (domingo excluído)
SELECT 
    m.CodFilial,
    ((DATEPART(WEEKDAY, m.DataEntradaSaida) + @@DATEFIRST - 2) % 7) + 1 AS DiaSemana,
    YEAR(m.DataEntradaSaida) AS Ano,
    MONTH(m.DataEntradaSaida) AS Mes,
    SUM(ISNULL(m.TotMov, 0) - ISNULL(m.TotCancel, 0)) AS Valor,
    COUNT(DISTINCT CONVERT(date, m.DataEntradaSaida)) AS QtdDias
FROM Movimento m
WHERE m.TipoMov = '2.4'
    AND m.NfeStatus = 'U'
    AND m.DtFinalizacao IS NOT NULL
    AND m.CodFilial IN (1, 2, 3, 4)  /* Só as 4 lojas */
    AND ((DATEPART(WEEKDAY, m.DataEntradaSaida) + @@DATEFIRST - 2) % 7) + 1 BETWEEN 1 AND 6  /* seg-sáb */
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
GROUP BY 
    m.CodFilial,
    ((DATEPART(WEEKDAY, m.DataEntradaSaida) + @@DATEFIRST - 2) % 7) + 1,
    YEAR(m.DataEntradaSaida),
    MONTH(m.DataEntradaSaida)
ORDER BY m.CodFilial, DiaSemana, Ano, Mes