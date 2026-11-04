SELECT 
    mr.IdFormaPag,
    fp.Denominacao,
    DATEPART(hour, mr.DataOperacao) AS Hora,
    SUM(ISNULL(mr.ValorRecebimento, 0) - ISNULL(mr.ValorTroco, 0)) AS Valor
FROM MovimentoRecebimento mr
INNER JOIN Movimento m ON mr.IdMovimento = m.IdMov
LEFT JOIN FormaPag fp ON mr.IdFormaPag = fp.IdFormaPag
WHERE m.TipoMov = '2.4'
    AND m.NfeStatus = 'U'
    AND mr.DataOperacao >= CONVERT(date, :data_inicio, 23)
    AND mr.DataOperacao < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    AND DATEPART(hour, mr.DataOperacao) >= :hora_inicio
    AND DATEPART(hour, mr.DataOperacao) <= :hora_fim
    AND mr.IdFormaPag <> 5
    /* FILTRO_FILIAL */
GROUP BY mr.IdFormaPag, fp.Denominacao, DATEPART(hour, mr.DataOperacao)