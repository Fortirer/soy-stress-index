# PIPE FAPESP Fase 1: rascunho (issue #20)

## 1. Qual chamada

| Chamada | Prazo | Valor Fase 1 | Situação |
| --- | --- | --- | --- |
| PIPE Jornada Tecnológica **Agro** 2026 (FAPESP 11/2026) | Pré-proposta até 22/04/2026 | até R$ 500 mil, 12 meses | **Encerrada.** Se repetir o calendário, a de 2027 abre em março e a pré-proposta vence em abril de 2027 |
| PIPE Jornada Tecnológica, 1ª rodada 2026 (todas as áreas) | Pré-proposta até 29/07/2026 | até R$ 500 mil | Encerrada; a próxima rodada deve sair em 2027 |
| PIPE Jornada Tecnológica, Tecnologias Educacionais (53/2026) | 12/11/2026 | — | Aberta, mas não serve para o Turgor |
| Centelha SP 3 (FAPESP/Finep) | Ideias até 21/05/2026 | até R$ 128 mil + bolsas | Encerrada; a próxima edição deve sair em 2027. Aceita pessoa física sem empresa na 1ª fase |

**Alvo:** pré-proposta da **PIPE Jornada Tecnológica Agro 2027** (março/abril de 2027), ou da 1ª rodada de 2027, a que abrir primeiro. Isso coincide com a decisão de janeiro (#24): se o resultado for "seguir", este rascunho vira a proposta.

Fontes: [chamada Agro 2026](https://fapesp.br/pipe/2026-agro); [chamadas FAPESP 2026](https://fapesp.br/2185/chamadas-de-propostas-2026); [1ª rodada 2026](https://agencia.fapesp.br/fapesp-destina-r-50-milhoes-para-projetos-de-inovacao-em-pequenas-empresas/58585); [Centelha SP 3](https://agencia.fapesp.br/programa-centelha-sp-destina-r-6-milhoes-para-inovacao/57791).

## 2. Requisitos que travam (resolver antes)

| Requisito (chamada Agro 2026) | Situação do Turgor | O que fazer |
| --- | --- | --- |
| Empresa com fins lucrativos, sede ou unidade de P&D **física** no estado de SP (endereço virtual não vale); MEI não vale; Inova Simples vale | Empresa não existe | Abrir a empresa (pode ser Inova Simples) com endereço em SP, por exemplo na incubadora (#21) |
| Pesquisador responsável **sócio** da empresa, **morando em SP** durante o projeto, com ≥24 h/semana | Você estará na Embrapa (onde?) e é doutoranda | Depende da #17. Se não puder ser você, o pesquisador responsável será o cofundador de dados (#18) |
| Pesquisadores principais não podem ser mestrandos ou doutorandos | Você é doutoranda | Defender o doutorado antes, ou não constar como pesquisadora principal |
| Equipe morando em SP e ligada à empresa | — | Contratar no estado de SP |

## 3. Pré-proposta (campos do SAGe)

### Título
**Turgor: índice fisiológico de estresse hídrico e térmico da soja, por satélite e clima, para crédito rural e seguro paramétrico**

### Resumo executivo (até ~1.500 caracteres)
Cooperativas, revendas, bancos e seguradoras financiam e seguram a soja, mas só conhecem o tamanho da quebra na colheita, por vistoria. Os gatilhos de seguro paramétrico baseados em chuva deixam de pagar perdas reais (risco de base), e o zoneamento ZARC informa o risco antes do plantio, mas não como a safra está indo. A Turgor desenvolve um índice de estresse da soja que combina déficit hídrico, calor extremo e sua interação, ponderados pela sensibilidade fisiológica de cada estádio (enchimento de grãos > vegetativo), com fenologia e vigor do dossel obtidos por satélite. Em backtest público com 780 municípios do RS e do PR (2001–2023), o índice separou safras com perda > 10% das normais com AUC de 0,86, contra 0,78 de um índice de chuva e 0,57 do ZARC. Em safras não usadas no ajuste (2024 e 2025), deixou de detectar 28% menos perdas que um gatilho de chuva, e em 15 de janeiro já igualava o desempenho de fim de safra do índice de chuva, 8 a 12 semanas antes da colheita. O projeto de Fase 1 vai demonstrar a viabilidade técnica em nível de talhão, com dados de produtividade de cooperativas parceiras, calibrar a resposta por estádio com experimentos controlados e operar o índice em tempo real na safra 2027/28, com perda esperada em R$/ha para carteiras de crédito e seguro.

### Desafio tecnológico
Converter um índice validado em nível municipal em um produto **por talhão e em tempo real**, com erro conhecido. Isso exige resolver quatro problemas que a literatura e o mercado ainda não resolveram juntos:

1. estimar estádios fenológicos de cada talhão durante a safra, quando o pico de NDVI ainda não ocorreu;
2. ponderar o estresse por estádio com base fisiológica, e não só por ajuste estatístico, para manter o desempenho em safras atípicas;
3. reduzir o risco de base em regiões onde a seca é sobretudo de chuva (RS), em que o ganho municipal sobre a chuva ainda não é significativo;
4. traduzir o índice em probabilidade de perda e perda esperada calibradas (escore de Brier), comparáveis entre regiões.

### Pergunta científica
Um índice de estresse ponderado por estádio, derivado de satélite e clima, prevê a quebra de produtividade da soja **no talhão** melhor do que anomalias de NDVI, índices de chuva e classes de risco do ZARC, e com quantas semanas de antecedência?

### Metodologia (resumo)
- **Dados:** Sentinel-2 (10 m) e MODIS (250 m); NASA POWER e ERA5-Land (chuva, temperatura, radiação, ETo); MapBiomas (máscara de soja); IBGE PAM (municipal); ZARC (MAPA); contornos e produtividade de talhões de 2 a 3 cooperativas parceiras (≥3 safras, sob termo de confidencialidade).
- **Índice:** balanço hídrico com componentes de déficit, graus-dia acima de 30 °C e interação calor × seca, em escore z local, ponderados 0,25 (vegetativo) / 0,75 (reprodutivo). Os pesos serão recalibrados com experimentos de eCO2 × seca × temperatura e com meta-análise (resposta da fotossíntese e dos carboidratos não estruturais por estádio).
- **Validação:** AUC para perda > 10% abaixo da tendência, risco de base, correlação de carteira e escore de Brier; reamostragem por safra (1.000 bootstrap) para intervalos de confiança; teste em safras e cooperativas não usadas no ajuste; comparação com NDVI, chuva e ZARC.
- **Tempo real:** monitor semanal (dez–abr) com registro público datado antes da colheita; perda esperada em R$/ha por mapas isotônicos por estado e data.

### Resultados preliminares
Repositório aberto: github.com/Fortirer/soy-stress-index (relatório de validação em PT e EN).

| Teste | Turgor | Chuva | NDVI | ZARC |
| --- | --- | --- | --- | --- |
| Backtest 2001–2023, AUC (RS+PR) | **0,862** (IC 0,81–0,90) | 0,784 | 0,773 | 0,573 |
| Backtest, risco de base | **0,33** | 0,44 | 0,44 | 0,64 |
| Safras novas 2024–25, AUC | **0,674** | 0,563 | 0,606 | 0,571 |
| Safras novas, risco de base | **0,36** | 0,51 | 0,42 | 0,46 |

- Antecedência: em 15/01 o índice já tem o desempenho que o índice de chuva só atinge no fim da safra.
- Reconstituição de 15/02/2025: municípios classificados como "severo" fecharam 30% abaixo da tendência; 83% tiveram perda > 10%.
- Perda esperada: escore de Brier 38% melhor que a climatologia na validação cruzada; 16% melhor nas safras novas.
- Limite conhecido: no RS, o ganho municipal sobre a chuva não é significativo (IC inclui zero). Este é um dos alvos do projeto.

### Oportunidade de mercado
- Soja na safra 2025/26: 48,7 M ha no Brasil; 12,5 M ha no RS + PR (Conab).
- Mercado endereçável (RS + PR) a R$ 3/ha/safra: R$ 37 M/ano; Brasil: R$ 146 M/ano. Mercado alcançável em 5 anos: cerca de R$ 7 M/ano (15 cooperativas, 10 revendas, 5 instituições de crédito e licença de gatilho), conforme `docs/negocio/mercado_pt.md`.
- Clientes: cooperativas (crédito de insumos, recebimento), revendas (barter, CPR), crédito rural, seguradoras e insurtechs paramétricas.
- Concorrentes: Trag, Guarda, Visiona/Agrotools. Diferencial: base fisiológica por estádio e validação pública com intervalos de confiança (`docs/negocio/concorrentes_pt.md`).
- **Evidência de demanda:** [preencher com o resultado das entrevistas (#11) e as cartas de intenção (#13)]. **Esta é a parte que mais pesa na avaliação e ainda está vazia.**

### Equipe
- **Janaina Fortirer:** ecofisiologista vegetal (doutorado USP; pesquisadora visitante na Universidade de Illinois, SoyFACE). Criou o índice e a validação. [Papel formal: depende da #17.]
- **[Cofundador de dados / sensoriamento remoto]:** pesquisador responsável ou principal se a fundadora não puder; ≥24 h/semana; morando em SP.
- **[Cofundador de negócios]:** administrador; relação com cooperativas e crédito.
- **Colaboradores:** [orientador ou pesquisador de modelagem de culturas]; [atuário de seguro agrícola].

### Capacidade da empresa
Pipeline de dados público em produção (GitHub Actions, monitor semanal desde 2/12/2026); infraestrutura em nuvem de baixo custo; [endereço em SP — incubadora].

## 4. Plano de trabalho (12 meses)

| Meta | Atividades | Meses | Indicador de sucesso |
| --- | --- | --- | --- |
| M1. Validação por talhão | Termos com 2–3 cooperativas; processamento Sentinel-2 por talhão; backtest das safras 2021–2026 | 1–5 | AUC por talhão ≥ 0,75 e risco de base ≤ 0,8 × o da chuva, com IC |
| M2. Calibração fisiológica | Integrar experimentos eCO2 × seca × temperatura e meta-análise; pesos por estádio com incerteza | 2–6 | Pesos com IC; ganho ≥ 0 sobre o prior em safras novas |
| M3. Chuva melhor no RS | ERA5-Land e estações; balanço hídrico com solo (AD) | 3–7 | Diferença de risco de base no RS com IC acima de zero, ou conclusão negativa documentada |
| M4. Operação em tempo real | Monitor por talhão para os parceiros na safra 2027/28; perda esperada em R$/ha | 6–12 | Relatórios semanais entregues; escore de Brier > climatologia ao fim da safra |
| M5. Viabilidade comercial | 3 pilotos pagos ou cartas de intenção; preço por hectare validado | 1–12 | ≥3 contratos ou cartas; faixa de preço citada por ≥3 compradores |

## 5. Orçamento (estrutura; preencher com a tabela de bolsas FAPESP vigente)

Teto da Fase 1: R$ 500 mil, incluindo as bolsas. Consultorias somam no máximo R$ 50 mil.

| Item | Uso | Peso indicativo |
| --- | --- | --- |
| Bolsas de Pesquisa em Pequenas Empresas (PE) | Cofundador de dados e analista de sensoriamento remoto | ~55% |
| Bolsa de Treinamento Técnico (TT) | Apoio em processamento e controle de qualidade de dados | ~10% |
| Serviços de terceiros | Atuário de seguro agrícola (consultoria ≤ R$ 50 mil); jurídico de dados (LGPD) | ~10% |
| Material de consumo e software | Nuvem (processamento Sentinel-2), armazenamento, licenças | ~10% |
| Viagens | Visitas às cooperativas parceiras (RS e PR) e eventos (Show Rural, Expodireto) | ~10% |
| Equipamento | Estação de trabalho para processamento | ~5% |

## 6. Antes de enviar (checklist)

- [ ] #17 respondida e estrutura societária definida
- [ ] Empresa aberta, com endereço físico em SP e cadastro na FAPESP pelo menos 2 dias úteis antes do prazo
- [ ] Pesquisador responsável definido, sócio, morando em SP, com ≥24 h/semana
- [ ] Evidência de demanda: entrevistas e cartas de intenção
- [ ] Pelo menos uma cooperativa disposta a ceder dados (carta de apoio)
- [ ] Súmulas curriculares
- [ ] Revisão por alguém que já ganhou um PIPE (peça indicação à ESALQTec, ao Cietec ou à AUSPIN)
