# Teste de preço: R$ por hectare por safra (issue #12)

O objetivo é descobrir o preço com os compradores. Os números abaixo não são preços: servem para você saber se o valor que alguém disser faz sentido. A issue fecha quando **3 compradores diferentes** citarem uma faixa de preço. Os preços são registrados na aba **Preços** do rastreador privado de entrevistas, e não neste repositório público.

## 1. Hipóteses do Business Overview

| Oferta | Cliente | Hipótese |
| --- | --- | --- |
| Score de risco | Cooperativas, revendas, crédito | R$ 2–6 / ha / safra |
| Alertas de estresse | Cooperativas, agrônomos | R$ 1–3 / ha / safra |
| Licença de gatilho paramétrico | Seguradoras | 1–3% do prêmio |
| Estudo de backtest | Bancos, seguradoras | R$ 30–100 mil por estudo |

## 2. Âncoras: as hipóteses fazem sentido?

**Valor da perda** (`scripts/24_pricing_anchors.py`, safras 2016–2025, soja a R$ 153,49/saca, CEPEA/ESALQ PR em 28/09/2026). A tabela mostra a quebra média abaixo da tendência, municípios com soja, em R$ por hectare:

| UF | Receita na tendência | Quebra média por ano | Quebra num ano ruim (10% piores) | Safras com perda > 10% |
| --- | --- | --- | --- | --- |
| PR | R$ 8.461/ha | R$ 693/ha | R$ 1.306/ha | 24% |
| RS | R$ 7.477/ha | R$ 1.227/ha | R$ 2.645/ha | 39% |

R$ 3/ha equivale a 0,4% da quebra média anual no PR e a 0,2% no RS. Mesmo R$ 6/ha fica abaixo de 1%. Do lado do valor, a hipótese não é cara. O risco está em o comprador não ver a ligação entre o índice e uma decisão que economize dinheiro. Por isso é preciso perguntar o que ele decidiria diferente.

**Prêmio de seguro.** Em 2020, a soja no Paraná teve cerca de 2 milhões de ha segurados, R$ 404 milhões de prêmio e taxa média de 5,84% sem subvenção ([Revista Cultivar, dez/2020](https://revistacultivar.com.br/noticias/contratacao-de-seguro-rural-cresce-no-pais-puxada-pelo-parana)). Isso dá cerca de R$ 200 de prêmio por ha. 1–3% do prêmio ≈ R$ 2–6/ha, a mesma faixa do score de risco. Com a soja mais cara hoje, o prêmio por ha provavelmente subiu; confirme nas entrevistas com seguradoras.

**Preço de referência de satélite.** A Agronow lançou em 2017 um plano anual de mapas (NDVI, umidade, produtividade) a R$ 1/ha/ano para áreas acima de 500 ha ([Revista Cultivar, out/2017](https://revistacultivar.com.br/noticias/agronow-lanca-plano-anual-a-partir-de-r-1-por-hectare)). Imagem sem validação contra perda tende a esse preço. O que sustenta R$ 2–6/ha é a validação (AUC 0,86, risco de base 0,33 contra 0,44 do índice de chuva). Plataformas internacionais como a EOSDA cobram de cooperativas por proposta (plano Enterprise), sem preço público.

## 3. Teste de estresse

Receita anual por cliente (`results/pricing_stress_test.csv`):

| Hectares | R$ 1/ha | R$ 2/ha | R$ 3/ha | R$ 6/ha |
| --- | --- | --- | --- | --- |
| 20.000 | R$ 20 mil | R$ 40 mil | R$ 60 mil | R$ 120 mil |
| 50.000 | R$ 50 mil | R$ 100 mil | R$ 150 mil | R$ 300 mil |
| 200.000 | R$ 200 mil | R$ 400 mil | R$ 600 mil | R$ 1,2 milhão |
| 500.000 | R$ 500 mil | R$ 1 milhão | R$ 1,5 milhão | R$ 3 milhões |

O exemplo da issue (200.000 ha × R$ 3 = R$ 600 mil/ano) só é realista se a cooperativa comprar para **toda** a área dos cooperados. É mais provável que o primeiro contrato cubra a carteira de crédito de insumos, ou uma regional com 20–50 mil ha. A faixa provável do primeiro contrato é de R$ 40–150 mil/ano. Pergunte nas entrevistas qual área entraria no primeiro ano.

## 4. Como perguntar (5 minutos, só na demo)

Não diga um preço antes deles. Se perguntarem, responda: "Estamos definindo com os primeiros clientes. Que faixa faria sentido para vocês?"

1. Quanto vocês gastam hoje com vistorias, dados de clima e regulação de sinistro, por safra?
2. Quem aprova esse gasto, e em que mês fecha o orçamento?
3. A partir de que preço por hectare você desconfiaria da qualidade? *(barato demais)*
4. Que preço seria um bom negócio? *(barato)*
5. Que preço já é caro, mas você ainda levaria para a diretoria? *(caro)*
6. A partir de que preço você não compraria? *(caro demais)*
7. Se o teste com os seus talhões der certo, você assinaria uma carta de intenção para a próxima safra nessa faixa?

As perguntas 3–6 seguem o método de Van Westendorp. A faixa aceitável vai do "barato" ao "caro". Com seguradoras, pergunte em % do prêmio ou em R$ por apólice. Com bancos, pergunte o preço de um estudo de backtest da carteira.

## 5. Registro e critério de conclusão

- Registre cada resposta no formulário de entrevista do rastreador privado. Ele tem campos para a oferta discutida, o gasto atual, os quatro preços de Van Westendorp, outra unidade de preço, quem assina e o mês do orçamento.
- A aba **Preços** mostra a mediana da faixa barato–caro por oferta e quantos compradores já citaram um número.
- **Concluído quando** 3 compradores diferentes tiverem citado uma faixa. Depois, atualize a tabela da seção 1 com a faixa observada e use-a no pitch deck (#23) e na proposta PIPE.
