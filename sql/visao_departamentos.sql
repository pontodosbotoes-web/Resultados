SELECT 
    LEFT(g.CodGrupo, 2) AS Depto,
    dg.NomeGrupo AS NomeDepto,
    DATEPART(hour, m.DataEntradaSaida) AS Hora,
    SUM(((im.Qtd - ISNULL(im.QtdCancel, 0)) / NULLIF(im.FatorConvUnid, 1)) * p.PrecoVenda1) AS ValorVenda
FROM Movimento m
INNER JOIN ItensMov im ON m.IdMov = im.IdMov
INNER JOIN Produtos p ON im.IdProduto = p.IdProduto
INNER JOIN Grupos g ON p.IdGrupo = g.IdGrupo
LEFT JOIN Grupos dg ON LEFT(g.CodGrupo, 2) = dg.CodGrupo AND LEN(dg.CodGrupo) = 2
WHERE m.TipoMov = '2.4'
    AND m.NfeStatus = 'U'
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND DATEPART(hour, m.DataEntradaSaida) >= :hora_inicio
    AND DATEPART(hour, m.DataEntradaSaida) <= :hora_fim
    AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
    AND p.IndisponivelVenda = 'N'
    /* FILTRO_FILIAL */
GROUP BY LEFT(g.CodGrupo, 2), dg.NomeGrupo, DATEPART(hour, m.DataEntradaSaida)