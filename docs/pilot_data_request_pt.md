# Piloto Turgor: dados que pedimos à cooperativa

**Objetivo:** testar, com talhões reais, se o índice de estresse Turgor (satélite + clima, sem sensores na fazenda) identifica quais talhões perderam produtividade de soja e quão cedo na safra. A cooperativa recebe um relatório com o resultado em cerca de duas semanas.

## O que precisamos

| Dado | Formato | Obrigatório? |
| --- | --- | --- |
| Contorno dos talhões | Shapefile, KML ou GeoJSON (pode ser o polígono do CAR ou o do sistema da cooperativa). Um identificador por talhão. | Sim |
| Produtividade de soja por talhão e safra | Planilha: `id_talhao`, `safra` (ano da colheita, ex.: 2022), `produtividade_kg_ha` | Sim |
| Safras | Pelo menos 3 safras entre 2017/18 e 2024/25, idealmente incluindo 2021/22 ou 2024/25 (secas no RS) | Sim |
| Número de talhões | 50 a 300 talhões; quanto mais municípios, melhor | Recomendado |
| Município do talhão | Código IBGE ou nome | Opcional |
| Data de semeadura e cultivar | Por talhão e safra | Opcional (melhora a leitura dos estádios) |
| Sinistros de seguro ou Proagro | Talhão, safra, causa, perda declarada | Opcional |

Não precisamos de nome, CPF ou dados financeiros dos produtores. Um código de talhão basta.

## Como os dados são usados

- Apenas para este teste. Não são compartilhados com terceiros nem usados para outros fins.
- Ficam guardados com acesso restrito e são apagados quando a cooperativa pedir.
- Assinamos um termo simples de confidencialidade e uso de dados antes do envio (LGPD).

## O que a cooperativa recebe

1. Para cada safra: quais talhões o índice teria apontado como em risco e em que data (1º de janeiro, 15 de janeiro, 1º de fevereiro ...).
2. Quantas perdas reais o índice encontrou e quantas deixou passar, comparado com um índice de chuva e com o índice municipal.
3. Mapas dos talhões com o estresse de cada safra.

Contato: Janaina Fortirer · Turgor
