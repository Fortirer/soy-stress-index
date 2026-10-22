# Kit do piloto com cooperativa (issue #9)

Tudo o que é preciso para conseguir os dados de uma cooperativa e devolver o resultado em duas semanas. Junto com este kit vão o pedido de dados ([`pilot_data_request_pt.md`](pilot_data_request_pt.md)) e uma demonstração do relatório ([`results/field_validation_demo/relatorio_cooperativa.md`](../results/field_validation_demo/relatorio_cooperativa.md), com produtividades sintéticas).

## 1. Mensagem de contato (e-mail ou WhatsApp)

> **Assunto:** Teste gratuito: ver as perdas de soja por seca antes da colheita, talhão a talhão
>
> Olá, [nome]. Sou Janaina Fortirer, ecofisiologista vegetal (doutoranda na USP, pesquisadora visitante na Universidade de Illinois). Desenvolvi um índice de estresse da soja por seca e calor que usa só satélite e clima, sem sensor na fazenda. Testado nos municípios do RS e do PR desde 2001, ele separa as safras com perda das normais com AUC de 0,86. Em 15 de fevereiro de 2025, dois meses antes da colheita, os municípios que ele marcou como "estresse severo" terminaram a safra 30% abaixo da tendência.
>
> Quero testar agora no nível de talhão, com dados reais de uma cooperativa. A proposta é simples: vocês enviam o contorno de 50 a 300 talhões e a produtividade de soja de pelo menos três safras (sem nome nem CPF de produtor), e em duas semanas eu devolvo um relatório mostrando quais talhões o índice teria apontado, em que data, e quantas perdas ele encontrou em comparação com um índice de chuva. Sem custo; os dados são usados só para este teste, sob termo de confidencialidade.
>
> Podemos conversar 20 minutos esta semana?

## 2. Termo de confidencialidade e uso de dados (rascunho)

*Rascunho para conversa. Antes de assinar, revisar com a Agência USP de Inovação ou com um advogado (ver issue #17, titularidade e papel de fundadora).*

1. **Partes:** [Cooperativa], CNPJ [ ], doravante "Cooperativa"; Janaina Fortirer, CPF [ ], doravante "Pesquisadora".
2. **Objeto:** avaliação, sem custo, de um índice de estresse hídrico e térmico da soja a partir de dados de satélite e clima, comparado com a produtividade de talhões fornecida pela Cooperativa.
3. **Dados fornecidos:** contorno dos talhões, produtividade de soja por talhão e safra e, opcionalmente, município, data de semeadura, cultivar e sinistros. Não serão fornecidos nome, CPF ou dados financeiros de cooperados.
4. **Finalidade única:** os dados serão usados somente para o teste descrito no item 2. Não serão vendidos, cedidos a terceiros, publicados nem usados para treinar produtos comerciais sem nova autorização por escrito.
5. **Resultados:** a Cooperativa recebe o relatório completo. Resultados agregados e anonimizados (sem identificar a Cooperativa, talhões ou produtores) poderão ser citados pela Pesquisadora em propostas de fomento e publicações científicas, salvo oposição por escrito da Cooperativa.
6. **Segurança:** os dados ficam em ambiente com acesso restrito à Pesquisadora e não são incluídos em repositórios públicos.
7. **Prazo e exclusão:** os dados serão apagados em até 30 dias após a entrega do relatório, ou antes, a pedido da Cooperativa.
8. **LGPD:** as partes cumprem a Lei 13.709/2018. Não há tratamento de dados pessoais sensíveis.
9. **Vigência:** 6 meses a partir da assinatura.

## 3. Passo a passo e prazos

| Dia | O quê |
| --- | --- |
| 0 | Termo assinado; dados recebidos (Shapefile, KML ou GeoJSON + planilha) |
| 1 | Conferência automática dos arquivos: `python scripts/13_field_validation.py --check-only --fields ... --yields ...`; pedir correções, se houver |
| 2-7 | Processamento: curva Sentinel-2 de cada talhão, clima no talhão, índice Turgor por data |
| 8-10 | Leitura dos resultados, revisão do relatório |
| 14 | Reunião de devolução; pedido de carta de intenção para um piloto pago na safra seguinte |

## 4. Como rodar

```bash
python scripts/13_field_validation.py --fields talhoes.shp --yields produtividade.xlsx \
    --name "Cooperativa X" --out results/field_validation/coop_x
```

Aceita GeoJSON, Shapefile (.shp ou .zip), KML/KMZ e GeoPackage em qualquer sistema de coordenadas, e planilhas CSV ou Excel com colunas em português (`id_talhao`, `safra` como 2022 ou "2021/22", `produtividade_kg_ha` ou `produtividade_sc_ha`, `municipio_ibge` opcional). Os resultados de cada cooperativa ficam fora do repositório público (pasta `results/field_validation/` no `.gitignore`).
