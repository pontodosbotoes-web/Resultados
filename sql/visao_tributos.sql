WITH MapeamentoFiliais AS (
    SELECT 1 AS CodFilial, 'C08327' AS CodCliFor UNION ALL SELECT 1, 'F00074' UNION ALL
    SELECT 2, 'C08328' UNION ALL SELECT 2, 'F10077' UNION ALL
    SELECT 3, 'C22206' UNION ALL SELECT 3, 'F15703' UNION ALL
    SELECT 4, 'C16205' UNION ALL SELECT 4, 'F14688' UNION ALL
    SELECT 5, 'C30965' UNION ALL SELECT 5, 'F16834'
),
AliquotaFiliais AS (
    SELECT 1 AS CodFilial, CAST(0.20 AS DECIMAL(18,4)) AS Aliquota, CAST(0.0 AS DECIMAL(18,4)) AS Adicional, CAST(0.20 AS DECIMAL(18,4)) AS AliquotaTransf, 0 AS UsarLimite, CAST(0 AS DECIMAL(18,2)) AS LimiteVendas, 1 AS TributarTransfEnviadas, 1 AS TributarTransfRecebidas, 1 AS TributarCompras UNION ALL
    SELECT 2, 0.20, 0.0, 0.20, 0, 0, 1, 1, 1 UNION ALL
    SELECT 3, 0.20, 0.0, 0.20, 0, 0, 1, 1, 1 UNION ALL
    SELECT 4, 0.143, 0.0, 0.143, 0, 0, 1, 1, 1 UNION ALL
    SELECT 5, 0.20, 0.0, 0.20, 0, 0, 1, 1, 1
),
MovContaAgregado AS (
    SELECT CodFilial, SUM(ValorLan * -1) AS TotalAntecipado
    FROM MovConta
    WHERE IdPlanoConta = 490 AND Compensado = 'S'
        AND DataOperacao >= CONVERT(date, :data_inicio, 23)
        AND DataOperacao < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
    GROUP BY CodFilial
),
Base AS (
    SELECT
        f.CodFilial,
        f.NomeFilial,
        af.Aliquota,
        af.Adicional,
        af.AliquotaTransf,
        af.UsarLimite,
        af.LimiteVendas,
        af.TributarCompras,
        af.TributarTransfEnviadas,
        af.TributarTransfRecebidas,
        ISNULL(mc.TotalAntecipado, 0) AS TributosAntecipados,
        
        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.4' AND m.NfeStatus = 'U'
                AND m.DtFinalizacao >= CONVERT(date, :data_inicio, 23)
                AND m.DtFinalizacao < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND (dest.CodCliFor IS NULL OR (m.CodFilial = 5 AND m.CodCliFor IN ('C16205','F14688')))
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS VendasBruto,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.4' AND m.NfeStatus = 'U'
                AND m.DtFinalizacao >= CONVERT(date, :data_inicio, 23)
                AND m.DtFinalizacao < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND (dest.CodCliFor IS NULL OR (m.CodFilial = 5 AND m.CodCliFor IN ('C16205','F14688')))
            THEN ISNULL(m.TotMov,0) * (1 - ISNULL(m.PercDesconto,0)/100.0)
            ELSE 0
        END), 0) AS VendasLiquidoDesconto,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.4' AND m.NfeStatus = 'U'
                AND m.DtFinalizacao >= CONVERT(date, :data_inicio, 23)
                AND m.DtFinalizacao < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND (dest.CodCliFor IS NULL OR (m.CodFilial = 5 AND m.CodCliFor IN ('C16205','F14688')))
            THEN ISNULL(m.ValorICMS, 0)
            ELSE 0
        END), 0) AS ICMS_Vendas,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.8'
                AND m.DtFinalizacao >= CONVERT(date, :data_inicio, 23)
                AND m.DtFinalizacao < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS DevolucaoVendas,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.9' AND m.NfeStatus = 'U'
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND dest.CodCliFor IS NOT NULL AND self.CodCliFor IS NULL
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS TransfEnvTotal,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.9' AND m.NfeStatus = 'U'
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND dest.CodCliFor IS NOT NULL AND self.CodCliFor IS NULL
                AND ISNULL(af.TributarTransfEnviadas, 0) = 1
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS TransfEnvTrib,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.9' AND m.NfeStatus = 'U'
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND dest.CodCliFor IS NOT NULL AND self.CodCliFor IS NULL
                AND ISNULL(af.TributarTransfEnviadas, 0) = 0
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS TransfEnvNaoTrib,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '2.9' AND m.NfeStatus = 'U'
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND dest.CodCliFor IS NOT NULL AND self.CodCliFor IS NULL
                AND ISNULL(af.TributarTransfEnviadas, 0) = 1
            THEN ISNULL(m.ValorICMS, 0)
            ELSE 0
        END), 0) AS ICMS_TransfEnv,

        ISNULL(SUM(CASE
            WHEN m.TipoMov IN ('1.1','1.0')
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
            THEN ISNULL(m.TotMov,0) + ISNULL(m.ValorIPI,0) + ISNULL(m.ValorFrete,0)
                 + ISNULL(m.OutrasDespesas,0) + ISNULL(m.ValorSubICMS,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS ComprasTotal,

        ISNULL(SUM(CASE
            WHEN m.TipoMov IN ('1.1','1.0')
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND ISNULL(af.TributarCompras, 0) = 1
            THEN ISNULL(m.TotMov,0) + ISNULL(m.ValorIPI,0) + ISNULL(m.ValorFrete,0)
                 + ISNULL(m.OutrasDespesas,0) + ISNULL(m.ValorSubICMS,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS ComprasTrib,

        ISNULL(SUM(CASE
            WHEN m.TipoMov IN ('1.1','1.0')
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND ISNULL(af.TributarCompras, 0) = 0
            THEN ISNULL(m.TotMov,0) + ISNULL(m.ValorIPI,0) + ISNULL(m.ValorFrete,0)
                 + ISNULL(m.OutrasDespesas,0) + ISNULL(m.ValorSubICMS,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS ComprasNaoTrib,

        ISNULL(SUM(CASE
            WHEN m.TipoMov IN ('1.1','1.0')
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND ISNULL(af.TributarCompras, 0) = 1
            THEN ISNULL(m.ValorICMS, 0)
            ELSE 0
        END), 0) AS ICMS_Compras,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '1.2' AND m.StatusSeparacao = 'F' AND m.ChaveNFe IS NOT NULL
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS TransfRecTotal,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '1.2' AND m.StatusSeparacao = 'F' AND m.ChaveNFe IS NOT NULL
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND ISNULL(af.TributarTransfRecebidas, 0) = 1
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS TransfRecTrib,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '1.2' AND m.StatusSeparacao = 'F' AND m.ChaveNFe IS NOT NULL
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND ISNULL(af.TributarTransfRecebidas, 0) = 0
            THEN ISNULL(m.TotMov,0) - ISNULL(m.TotCancel,0)
            ELSE 0
        END), 0) AS TransfRecNaoTrib,

        ISNULL(SUM(CASE
            WHEN m.TipoMov = '1.2' AND m.StatusSeparacao = 'F' AND m.ChaveNFe IS NOT NULL
                AND m.DataEntradaSaida >= CONVERT(date, :data_inicio, 23)
                AND m.DataEntradaSaida < DATEADD(day, 1, CONVERT(date, :data_fim, 23))
                AND ISNULL(af.TributarTransfRecebidas, 0) = 1
            THEN ISNULL(m.ValorICMS, 0)
            ELSE 0
        END), 0) AS ICMS_TransfRec
    FROM Filiais f
    LEFT JOIN AliquotaFiliais af ON af.CodFilial = f.CodFilial
    LEFT JOIN Movimento m ON f.CodFilial = m.CodFilial
        AND ISNULL(m.IdNaturezaOperacao, 0) NOT IN (19, 32, 86, 38)
    LEFT JOIN MapeamentoFiliais dest ON dest.CodCliFor = m.CodCliFor
    LEFT JOIN MapeamentoFiliais self ON self.CodFilial = m.CodFilial AND self.CodCliFor = m.CodCliFor
    LEFT JOIN MovContaAgregado mc ON mc.CodFilial = f.CodFilial
    GROUP BY f.CodFilial, f.NomeFilial, af.Aliquota, af.Adicional, af.AliquotaTransf,
             af.UsarLimite, af.LimiteVendas, af.TributarCompras, af.TributarTransfEnviadas,
             af.TributarTransfRecebidas, mc.TotalAntecipado
)
SELECT * FROM Base ORDER BY NomeFilial;