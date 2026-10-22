# Tamanho de mercado, de baixo para cima (issue #16)

Slide pronto: [`docs/figures/market_size_slide.png`](../figures/market_size_slide.png). O script `scripts/25_market_size.py` gera o slide e a tabela `results/market_size.csv`. As premissas estão no topo do script; para atualizar, troque os números lá e rode de novo.

## Fórmula

**Receita = clientes × hectares por cliente × preço por hectare por safra**, somada por segmento. Para as seguradoras, a conta é: área segurada com gatilho Turgor × prêmio por ha × participação da licença.

## Números

| Nível | Conta | Hectares | R$ por ano |
| --- | --- | --- | --- |
| TAM | Toda a soja do Brasil, 48,7 M ha × R$ 3/ha | 48,7 M | R$ 146 M |
| SAM | Soja do RS + PR, 12,5 M ha × R$ 3/ha (onde o índice está validado) | 12,5 M | R$ 37 M |
| SOM, cooperativas | 15 clientes × 50 mil ha × R$ 3 | 750 mil | R$ 2,3 M |
| SOM, revendas e tradings | 10 × 30 mil ha × R$ 3 | 300 mil | R$ 0,9 M |
| SOM, bancos e cooperativas de crédito | 5 × 100 mil ha × R$ 3 | 500 mil | R$ 1,5 M |
| SOM, seguradoras (licença) | 5% da soja do RS+PR × R$ 202/ha de prêmio × 2% | 620 mil | R$ 2,5 M |
| **SOM em 5 anos** | soma | 2,2 M | **R$ 7,2 M** |

## De onde vêm os números

- **Área de soja na safra 2025/26:** Brasil 48,72 M ha, RS 6,73 M ha, PR 5,74 M ha, MT 13,01 M ha (Conab, levantamento de maio de 2026, publicado pela [Embrapa Soja](https://www.embrapa.br/en/web/soja/cultivos/soja1/dados-economicos)).
- **Prêmio de seguro:** a soja do PR em 2020 teve cerca de 2 M ha segurados e R$ 404 M de prêmio, com taxa média de 5,84% ([Revista Cultivar](https://revistacultivar.com.br/noticias/contratacao-de-seguro-rural-cresce-no-pais-puxada-pelo-parana)). Isso dá cerca de R$ 200/ha. É um valor de 2020 e deve ser maior hoje.
- **Cooperativas:** são 1.254 cooperativas agropecuárias no Brasil, 88 delas no RS, segundo o Anuário do Cooperativismo 2026 do Sistema OCB ([AgFeed](https://agfeed.com.br/negocios/cooperativas-do-agro-crescem-dois-digitos-em-2025-e-faturam-quase-meio-trilhao)). Nem todas trabalham com soja. As 15 do SOM saem das maiores de grãos do RS e do PR; a lista de alvos está no rastreador privado.
- **Preço:** R$ 3/ha é o meio da hipótese do score de risco. Ainda precisa ser confirmado por 3 compradores (issue #12). Com R$ 2/ha o SOM cai para cerca de R$ 5,6 M; com R$ 6/ha sobe para cerca de R$ 11,8 M (a licença de seguro não muda com o preço por hectare).

## Leitura

- Vender só por hectare monitorado é um negócio de nicho: R$ 37 M por ano mesmo com 100% da soja do RS e do PR. Para virar uma empresa grande, o Turgor precisa de pelo menos uma de três coisas: outros estados (MT tem mais soja que RS e PR juntos), outras culturas (milho safrinha) ou a licença de gatilho para seguro, que cobra sobre o prêmio e não sobre o hectare.
- No começo, o cliente que paga a conta é quem tem mais hectares por contrato: bancos e cooperativas de crédito (carteira de custeio) e grandes cooperativas.
- Falta um número: o crédito de custeio de soja por estado (SICOR, Banco Central). A API de dados abertos do Banco Central (olinda.bcb.gov.br) está bloqueada nesta sessão. Para incluir esse dado, baixe a tabela "Custeio por região, UF e produto" na Matriz de Dados do Crédito Rural do BCB, ou libere o domínio.

## Para expandir depois

| Expansão | Área | Conta rápida a R$ 3/ha |
| --- | --- | --- |
| Mato Grosso, soja | 13,0 M ha | R$ 39 M |
| Brasil, milho safrinha | conferir no Conab | — |
| Argentina e Paraguai, soja | conferir | — |

Antes de vender em MT, o índice precisa ser validado lá: o clima, o calendário e as perdas são diferentes. Roda o mesmo backtest com a lista de municípios de MT.
