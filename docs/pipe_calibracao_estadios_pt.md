# Calibração fisiológica do índice Turgor: pesos por estádio

*Texto de apoio para a proposta FAPESP PIPE Fase 1 (issue #8). Resultados em `results/stage_weights.csv`, script `scripts/22_stage_weights.py`.*

## Pergunta

O índice Turgor dá peso 0,75 ao estresse no período reprodutivo (florescimento, formação de vagens e enchimento de grãos) e 0,25 ao período vegetativo. Esse peso veio da fisiologia da soja, não de ajuste aos dados. Ele se sustenta quando comparado com a literatura de resposta da produtividade à água e com o que os próprios dados de produtividade indicam?

## Métodos

Mantendo tudo o mais igual ao índice operacional (janelas de estádio típicas de cada município, latência real dos dados, valor de fim de safra), foram comparados cinco esquemas de peso para o estádio reprodutivo:

| Esquema | Peso vegetativo / reprodutivo | Origem |
| --- | --- | --- |
| Prior fisiológico (atual) | 0,25 / 0,75 | Sensibilidade maior da soja ao déficit hídrico e ao calor em R1-R6 |
| FAO Ky | 0,18 / 0,82 | Fatores de resposta da produtividade ao déficit hídrico (Doorenbos & Kassam, 1979, FAO Irrigation and Drainage Paper 33): vegetativo 0,2; florescimento 0,8; formação da produtividade 1,0 |
| Igual | 0,50 / 0,50 | Referência sem fisiologia |
| Só reprodutivo | 0 / 1 | Caso extremo |
| Ajustado aos dados | escolhido por safra | Peso (0 a 1, passo 0,05) com maior AUC nas **outras** safras (validação deixando uma safra de fora), separado por estado |

Avaliação: 17.342 municípios-safra no RS e PR (2001-2023), com intervalos de 95% por reamostragem de safras inteiras, e as safras 2024 e 2025, que não entraram em nenhum ajuste.

## Resultados

| RS + PR | AUC 2001-2023 | Diferença vs. prior (IC 95%) | Risco de base | AUC 2024-2025 | Risco de base 2024-2025 |
| --- | --- | --- | --- | --- | --- |
| **Prior 0,25 / 0,75** | **0,862** | | **0,33** | 0,674 | 0,37 |
| FAO Ky 0,18 / 0,82 | 0,861 | 0,000 (-0,004 a +0,003) | 0,33 | 0,665 | 0,38 |
| Igual 0,50 / 0,50 | 0,854 | -0,008 (-0,020 a +0,003) | 0,34 | 0,700 | 0,34 |
| Só reprodutivo | 0,855 | -0,006 (-0,019 a +0,004) | 0,35 | 0,643 | 0,42 |
| Ajustado aos dados | 0,857 | -0,005 (-0,010 a -0,002) | 0,34 | 0,675 | 0,37 |

- **Três fontes independentes convergem para o mesmo peso.** O peso reprodutivo escolhido pelos dados, safra a safra, ficou entre 0,65 e 0,90 (mediana 0,75 no PR e 0,80 no RS); a literatura da FAO dá 0,82; o prior fisiológico é 0,75.
- **Ajustar o peso aos dados não melhora a previsão.** A versão ajustada é ligeiramente pior que o prior (AUC -0,005, intervalo inteiramente abaixo de zero): com 23 safras, o ajuste adiciona ruído. O prior fisiológico fica como peso operacional.
- Pesos iguais foram um pouco melhores nas duas safras novas (AUC 0,70 contra 0,67), mas piores no período 2001-2023; duas safras não bastam para mudar o peso.

## Por que isso importa para o PIPE

O resultado sustenta a hipótese central do projeto: **conhecimento fisiológico, fixado antes de olhar os dados de produtividade, generaliza tão bem ou melhor que pesos estimados estatisticamente**, o que reduz o risco de sobreajuste quando o índice for aplicado a safras atípicas. Isso diferencia o Turgor de modelos puramente estatísticos.

## Próxima etapa: calibração com os experimentos

Os experimentos de câmaras de topo aberto (aCO2, eCO2, seca, eCO2 + seca; e aCO2, eCO2, aquecimento, eCO2 + aquecimento; cultivar MG/BR-46 Conquista, colheita aos 60 dias) e a meta-análise sobre soja sob eCO2, seca e temperatura permitem calibrar o que os dados de produtividade não informam:

1. **Resposta da fotossíntese (A, gs) e dos carboidratos não estruturais à seca e ao calor**, em magnitude (razão de resposta, lnRR), para pesar os componentes água e calor dentro de cada estádio.
2. **Modificador de CO2**: quanto o eCO2 atenua a resposta à seca (fechamento estomático, economia de água) e ao calor. Isso torna o índice válido para safras futuras com CO2 mais alto, onde modelos ajustados ao passado tendem a superestimar perdas.
3. **Curvas de resposta da meta-análise** por estádio, quando a extração dos dados (média, SD e n de fotossíntese e NSC) estiver completa.

Os experimentos foram colhidos aos 60 dias, então não dão pesos de produtividade por estádio diretamente; dão a magnitude fisiológica das respostas, que entra nos pesos dos componentes e no modificador de CO2. **Antes de usar esses dados no produto, é preciso confirmar a titularidade** com a Agência USP de Inovação e com os coautores (issue #17).
