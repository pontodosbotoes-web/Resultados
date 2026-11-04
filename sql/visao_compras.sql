SELECT 
    YEAR(m.DtFinalizacao) AS Ano,
    MONTH(m.DtFinalizacao) AS Mes,
    m.CodFilial AS Loja,
    ISNULL(depto.NOMEGRUPO, 'SEM DEPARTAMENTO') AS Departamento,
    cf.NomeCliFor AS Fornecedor,
    SUM((i.Qtd - ISNULL(i.QtdCancel, 0)) / NULLIF(i.FatorConvUnid, 0)) AS Quantidade,
    SUM(((i.Qtd - ISNULL(i.QtdCancel, 0)) / NULLIF(i.FatorConvUnid, 0)) * ISNULL(p.CustoCompra2, 0)) AS Valor
FROM Produtos p
INNER JOIN ItensMov i ON p.IdProduto = i.IdProduto
INNER JOIN Movimento m ON i.IdMov = m.IdMov
INNER JOIN Cli_For cf ON m.CodCliFor = cf.CodCliFor
LEFT JOIN Grupos g ON p.IdGrupo = g.IdGrupo
LEFT JOIN Grupos depto ON LEFT(g.CodGrupo, 2) = LEFT(depto.CodGrupo, 2) AND (LEN(REPLACE(depto.CodGrupo, '.', '')) = 2 OR LEN(depto.CodGrupo) = 2)
WHERE m.TipoMov = '1.1'
    AND m.CodLocal = '01'
    AND m.DtFinalizacao >= CONVERT(date, :data_inicio, 23)
    AND m.DtFinalizacao < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND m.CodCliFor NOT IN ('C08327','F00074','C08328','F10077','C22206','F15703','C16205','F14688','C30965','F16834')
    /* FILTRO_FILIAL */
GROUP BY YEAR(m.DtFinalizacao), MONTH(m.DtFinalizacao), m.CodFilial, depto.NOMEGRUPO, cf.NomeCliFor