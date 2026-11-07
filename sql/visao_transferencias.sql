WITH MapeamentoFiliais AS (
    SELECT 1 AS CodFilial, 'C08327' AS CodCliFor UNION ALL SELECT 1, 'F00074' UNION ALL
    SELECT 2, 'C08328' UNION ALL SELECT 2, 'F10077' UNION ALL
    SELECT 3, 'C22206' UNION ALL SELECT 3, 'F15703' UNION ALL
    SELECT 4, 'C16205' UNION ALL SELECT 4, 'F14688' UNION ALL
    SELECT 5, 'C30965' UNION ALL SELECT 5, 'F16834'
)

-- PARTE 1: Transferências 2.9 (padrão entre filiais - exclui destino=SRB p/ evitar duplicidade)
SELECT 
    YEAR(m.DataEntradaSaida) AS Ano,
    MONTH(m.DataEntradaSaida) AS Mes,
    m.CodFilial AS FilialOrigem,
    dest.CodFilial AS FilialDestino,
    'transf_2.9' AS TipoDado,
    SUM(((i.Qtd - ISNULL(i.QtdCancel, 0)) / NULLIF(i.FatorConvUnid, 0)) * ISNULL(p.CustoCompra2, 0)) AS Valor
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
    AND dest.CodFilial <> 4
    AND self.CodCliFor IS NULL
    AND p.IndisponivelVenda = 'N'
    /* FILTRO_FILIAL */
GROUP BY YEAR(m.DataEntradaSaida), MONTH(m.DataEntradaSaida), m.CodFilial, dest.CodFilial

UNION ALL

-- PARTE 2: ENTRADAS na SRB (TipoMov 1.1 e 1.2 registrados na própria filial 4)
SELECT
    YEAR(m.DataEntradaSaida) AS Ano,
    MONTH(m.DataEntradaSaida) AS Mes,
    origem.CodFilial AS FilialOrigem,
    m.CodFilial AS FilialDestino,
    'srb_entrada' AS TipoDado,
    SUM(((i.Qtd - ISNULL(i.QtdCancel, 0)) / NULLIF(i.FatorConvUnid, 0)) * ISNULL(p.CustoCompra2, 0)) AS Valor
FROM Produtos p
INNER JOIN ItensMov i ON p.IdProduto = i.IdProduto
INNER JOIN Movimento m ON i.IdMov = m.IdMov
INNER JOIN MapeamentoFiliais origem ON origem.CodCliFor = m.CodCliFor
LEFT JOIN MapeamentoFiliais self ON self.CodFilial = m.CodFilial AND self.CodCliFor = m.CodCliFor
WHERE m.CodFilial = 4
    AND m.TipoMov IN ('1.1', '1.2')
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND origem.CodFilial <> 4
    AND self.CodCliFor IS NULL
    AND p.IndisponivelVenda = 'N'
    /* FILTRO_FILIAL */
GROUP BY YEAR(m.DataEntradaSaida), MONTH(m.DataEntradaSaida), origem.CodFilial, m.CodFilial

UNION ALL

-- PARTE 3: SAÍDAS das filiais para a SRB (TipoMov 2.2 e 2.4 nas filiais 1,2,3,5 com destino SRB)
SELECT
    YEAR(m.DataEntradaSaida) AS Ano,
    MONTH(m.DataEntradaSaida) AS Mes,
    m.CodFilial AS FilialOrigem,
    dest.CodFilial AS FilialDestino,
    'srb_saida_filiais' AS TipoDado,
    SUM(((i.Qtd - ISNULL(i.QtdCancel, 0)) / NULLIF(i.FatorConvUnid, 0)) * ISNULL(p.CustoCompra2, 0)) AS Valor
FROM Produtos p
INNER JOIN ItensMov i ON p.IdProduto = i.IdProduto
INNER JOIN Movimento m ON i.IdMov = m.IdMov
INNER JOIN MapeamentoFiliais dest ON dest.CodCliFor = m.CodCliFor
LEFT JOIN MapeamentoFiliais self ON self.CodFilial = m.CodFilial AND self.CodCliFor = m.CodCliFor
WHERE m.TipoMov IN ('2.2', '2.4')
    AND m.NfeStatus = 'U'
    AND m.CodFilial <> 4
    AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
    AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND dest.CodFilial = 4
    AND self.CodCliFor IS NULL
    AND p.IndisponivelVenda = 'N'
    /* FILTRO_FILIAL */
GROUP BY YEAR(m.DataEntradaSaida), MONTH(m.DataEntradaSaida), m.CodFilial, dest.CodFilial