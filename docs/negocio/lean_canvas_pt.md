# Lean Canvas — versão 0 (issue #19)

**Situação:** canvas preenchido em 22/10/2026, **antes** das entrevistas. Cada caixa traz o que já tem **evidência** (✔), o que ainda é **hipótese** (?) e a issue que testa. Atualize depois das 10 entrevistas de problema (#11) e das demos.

| Caixa | Conteúdo |
| --- | --- |
| **1. Problema** | ? Quem financia ou segura a soja só descobre o tamanho da quebra na colheita, por vistoria. ? Gatilhos de seguro por chuva deixam de pagar perdas reais (risco de base). ? O ZARC diz onde e quando plantar, mas não como a safra está indo. ✔ O ZARC quase não separa safras com perda (AUC 0,57); um índice de chuva deixa passar 44% das perdas (backtest). |
| **2. Segmentos de clientes** | ? Primeiros compradores: cooperativas de grãos do RS e do PR (crédito de insumos, recebimento), revendas com barter e CPR, crédito rural (cooperativas de crédito e bancos), seguradoras e insurtechs paramétricas. **Early adopters prováveis:** insurtechs (Guarda) e cooperativas de crédito com carteira concentrada em soja. Testes: #11, #13. |
| **3. Proposta de valor única** | ✔ Ver a quebra de 8 a 12 semanas antes da colheita: em 15/01 o índice já sabe o que um índice de chuva só sabe no fim da safra. ✔ Errar menos que a chuva: risco de base 0,33 contra 0,44 no backtest e 0,36 contra 0,51 em 2024/25. ✔ Sem sensor no campo; tudo por satélite e clima. |
| **4. Solução** | ✔ Índice Turgor semanal por município (monitor automático a partir de 2/12/2026). ✔ Perda esperada em R$/ha. ✔ Leitura por talhão via Sentinel-2 (pronta, falta validar com dados reais, #9). ? Gatilho paramétrico licenciado. |
| **5. Canais** | ? Indicações de pesquisadores e de agrônomos de cooperativas; eventos (Show Rural, Expodireto, hackathon); relatório público de validação; parcerias com plataformas (Traive, SciCrop, Trag). Teste: #11, #14. |
| **6. Receita** | ? R$ 2–6/ha/safra pelo score de risco; R$ 1–3/ha pelos alertas; 1–3% do prêmio pela licença de gatilho; R$ 30–100 mil por estudo de backtest. Âncora: R$ 3/ha = 0,2–0,4% da quebra média anual. Teste: #12. |
| **7. Estrutura de custos** | Pessoas (cofundador de dados, vendas); nuvem e dados (hoje quase zero: dados públicos, GitHub Actions); validação de campo; viagens a cooperativas; jurídico (contrato social, propriedade intelectual). Financiamento previsto: PIPE Fase 1 (até R$ 500 mil), Centelha (até R$ 128 mil). #20. |
| **8. Métricas-chave** | Hectares monitorados pagos; número de cartas de intenção e pilotos (meta: 3 até janeiro); risco de base medido em cada safra nova (registro público semanal); renovação depois da 1ª safra. |
| **9. Vantagem injusta** | ✔ Fisiologia da soja sob seca, calor e CO2 (doutorado, SoyFACE): pesos por estádio que não vêm de ajuste estatístico. ✔ Backtest público, com intervalos de confiança e registro semanal com data, feito antes da colheita: difícil de copiar sem anos de histórico. ? Dados de campo de parceiros (quando vierem). |

## Riscos principais (para testar primeiro)

1. **Alguém paga?** Maior risco. Ver #11, #12 e #13.
2. **O ganho no RS** sobre a chuva não está provado por município. Venda no RS o alerta antecipado e a visão da carteira; o maior ganho por município está no PR.
3. **Papel da fundadora** com a Embrapa (#17): pode atrasar a criação da empresa.
4. **Concorrência:** a Trag e a Guarda já têm clientes e captaram R$ 4,5 M cada. A diferenciação precisa ser a validação.
