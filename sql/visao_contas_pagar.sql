SELECT
    c.IdCPR,
    c.CodFilial,
    c.NUMDOC,
    c.CodCliFor,
    cf.NomeCliFor AS Fornecedor,
    c.DTEMISSAO,
    c.DTVENCIMENTO,
    c.NumeroParcela,
    c.HISTORICO,
    c.ValorTitulo,
    c.DTBAIXA,
    td.TipoDoc
FROM CPR c
INNER JOIN TipoDoc td ON c.CodTipoDoc = td.CodTipoDoc
LEFT JOIN Cli_For cf ON c.CodCliFor = cf.CodCliFor
WHERE td.TipoLancamento = 'P'
  AND c.CodTipoDoc IN ('01', '05', '09', '14', '57')
  AND c.DTVENCIMENTO >= CONVERT(date, :data_inicio, 23)
  AND c.DTVENCIMENTO < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
  /* FILTRO_FILIAL */
ORDER BY c.DTVENCIMENTO ASC