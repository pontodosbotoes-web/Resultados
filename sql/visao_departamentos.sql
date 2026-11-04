SELECT 
    LEFT(g.CodGrupo, 2) AS Depto,
    DATEPART(hour, m.DataEntradaSaida) AS Hora,
    SUM(((im.Qtd - ISNULL(im.QtdCancel, 0)) / im.FatorConvUnid) * p.PrecoVenda1) AS ValorVenda
FROM Movimento m
INNER JOIN ItensMov im ON m.IdMov = im.IdMov
INNER JOIN Produtos p ON im.IdProduto = p.IdProduto
INNER JOIN Grupos g ON p.IdGrupo = g.IdGrupo
WHERE m.TipoMov = '2.4'
    AND m.NfeStatus = 'U'
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND DATEPART(hour, m.DataEntradaSaida) >= :hora_inicio
    AND DATEPART(hour, m.DataEntradaSaida) <= :hora_fim
    /* FILTRO_FILIAL */
GROUP BY LEFT(g.CodGrupo, 2), DATEPART(hour, m.DataEntradaSaida)