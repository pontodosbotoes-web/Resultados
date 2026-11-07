WITH MapeamentoFiliais AS (
    SELECT 1 AS CodFilial, 'C08327' AS CodCliFor UNION ALL SELECT 1, 'F00074' UNION ALL
    SELECT 2, 'C08328' UNION ALL SELECT 2, 'F10077' UNION ALL
    SELECT 3, 'C22206' UNION ALL SELECT 3, 'F15703' UNION ALL
    SELECT 4, 'C16205' UNION ALL SELECT 4, 'F14688' UNION ALL
    SELECT 5, 'C30965' UNION ALL SELECT 5, 'F16834'
)
SELECT 
    YEAR(m.DataEntradaSaida) AS Ano,
    MONTH(m.DataEntradaSaida) AS Mes,
    m.CodFilial AS FilialOrigem,
    dest.CodFilial AS FilialDestino,
    SUM(
        ((i.Qtd - ISNULL(i.QtdCancel, 0)) / NULLIF(i.FatorConvUnid, 0)) 
        * ISNULL(p.CustoCompra2, 0)
    ) AS Valor
FROM Produtos p
INNER JOIN ItensMov i ON p.IdProduto = i.IdProduto
INNER JOIN Movimento m ON i.IdMov = m.IdMov
LEFT JOIN MapeamentoFiliais dest ON dest.CodCliFor = m.CodCliFor
LEFT JOIN MapeamentoFiliais self ON self.CodFilial = m.CodFilial AND self.CodCliFor = m.CodCliFor
WHERE m.TipoMov = '2.9'
    AND m.NfeStatus = 'U'
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND dest.CodCliFor IS NOT NULL
    AND self.CodCliFor IS NULL
    AND p.IndisponivelVenda = 'N'
    /* FILTRO_FILIAL */
GROUP BY 
    YEAR(m.DataEntradaSaida), 
    MONTH(m.DataEntradaSaida), 
    m.CodFilial, 
    dest.CodFilial
ORDER BY 
    [Ano] ASC,
    [Mes] ASC,
    [FilialOrigem] ASC,
    [FilialDestino] ASC;