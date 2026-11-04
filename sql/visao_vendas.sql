SELECT
    m.CodFilial,
    DATEPART(hour, m.DataEntradaSaida) AS Hora,
    SUM(ISNULL(m.TotMov, 0) - ISNULL(m.TotCancel, 0)) AS ValorVenda,
    COUNT(DISTINCT m.IdMov) AS QtdVendas,
    SUM(ISNULL(itens.QtdItens, 0)) AS QtdItens
FROM Movimento m
OUTER APPLY (
    SELECT SUM(ISNULL((im.Qtd - ISNULL(im.QtdCancel, 0)) / NULLIF(im.FatorConvUnid, 0), 0)) AS QtdItens
    FROM ItensMov im
    WHERE im.IdMov = m.IdMov
) itens
WHERE m.TipoMov = '2.4'
    AND m.NfeStatus = 'U'
    AND m.DtFinalizacao IS NOT NULL
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND DATEPART(hour, m.DataEntradaSaida) >= :hora_inicio
    AND DATEPART(hour, m.DataEntradaSaida) <= :hora_fim
    AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
    /* FILTRO_FILIAL */
GROUP BY m.CodFilial, DATEPART(hour, m.DataEntradaSaida)
ORDER BY m.CodFilial, Hora