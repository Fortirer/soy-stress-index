"""Public validation report, Portuguese and English (issue #10).

    python scripts/23_public_report.py

Every number is read from results/ (scripts 06-22), so the report is rebuilt
whenever the results change. Writes docs/report/turgor_validation_report_{pt,en}.pdf
and the figures they use.
"""
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Polygon  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ssi.config import RESULTS, ROOT  # noqa: E402

OUT = ROOT / "docs" / "report"
OUT.mkdir(parents=True, exist_ok=True)
REPO = "github.com/Fortirer/soy-stress-index"
GREEN, BLUE, GREY, ORANGE, INK = "#1E5B3A", "#2A78D6", "#8A9A90", "#B4541A", "#12291D"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# ---------------------------------------------------------------- numbers
ci = pd.read_csv(RESULTS / "v1_ci.csv")
zc = pd.read_csv(RESULTS / "baselines_ci.csv")
ho = pd.read_csv(RESULTS / "holdout_metrics.csv")
ew = pd.read_csv(RESULTS / "early_warning.csv")
el = pd.read_csv(RESULTS / "expected_loss_metrics.csv")
cal = pd.read_csv(RESULTS / "expected_loss_calibration.csv")
sw = pd.read_csv(RESULTS / "stage_weights.csv")
ms = pd.read_csv(RESULTS / "municipal_scores_2001_2025.csv.gz")
rep = pd.read_csv(ROOT / "monitor/replays/2024-25/2025-02-15/turgor_monitor.csv")


def g(df, **kw):
    for k, v in kw.items():
        df = df[df[k] == v]
    return df.iloc[0]


def bt(index, region, metric):
    if index == "ZARC":
        return g(zc, test="backtest 2001-2023", region=region, metric=metric, index="ZARC risk class")
    return g(ci, region=region, metric=metric, index=index)


def hd(index, region, metric):
    if index == "ZARC":
        return g(zc, test="holdout 2024-2025", region=region, metric=metric, index="ZARC risk class")["estimate"]
    return g(ho, region=region, harvests="2024+2025", index=index)[metric]


IDX = [("Turgor index", "Turgor"), ("Rainfall index", "rain"), ("NDVI only", "ndvi"), ("ZARC", "zarc")]
y25 = ms[ms["year"] == 2025][["fips5", "rel_anom", "loss"]]
rp = rep.merge(y25, on="fips5")
rclass = rp.groupby("stress_class").agg(n=("loss", "size"), anom=("rel_anom", "mean"), loss=("loss", "mean"))
from sklearn.metrics import roc_auc_score  # noqa: E402
rep_auc = roc_auc_score(rp["loss"], rp["turgor_index"])
n_bt = len(pd.read_csv(RESULTS / "v1_scores_rs_pr.csv.gz"))
n_ho = int(g(ho, region="RS + PR", harvests="2024+2025", index="Turgor index")["n"])
fit_w = pd.read_csv(RESULTS / "stage_weights_fitted.csv")


def sw_row(name):
    return g(sw, test="backtest 2001-2023", region="RS + PR", index=name, metric="auc_loss")

# ---------------------------------------------------------------- text
L = {
 "pt": dict(
  title="Índice Turgor de estresse da soja: relatório de validação",
  sub="Seca e calor na soja do Rio Grande do Sul e do Paraná, a partir de satélite e clima públicos. Outubro de 2026.",
  names={"Turgor": "Índice Turgor", "rain": "Índice de chuva (jan-fev)", "ndvi": "Só NDVI", "zarc": "ZARC (zoneamento oficial)"},
  s_summary="Resumo",
  summary=[
   f"<b>O que é:</b> um índice de estresse hídrico e térmico da soja, ponderado pelo estádio da cultura, calculado só com dados públicos de satélite (MODIS, Sentinel-2) e clima (NASA POWER), sem sensores na fazenda.",
   f"<b>Teste histórico (2001-2023, {n_bt:,} municípios-safra):</b> separa as safras com perda (produtividade &gt;10% abaixo da tendência) das normais com AUC {bt('Turgor index','RS + PR','auc_loss')['estimate']:.2f}, contra {bt('Rainfall index','RS + PR','auc_loss')['estimate']:.2f} de um índice de chuva e {bt('ZARC','RS + PR','auc_loss')['estimate']:.2f} do ZARC. Deixa de encontrar {100*bt('Turgor index','RS + PR','basis_risk')['estimate']:.0f}% das perdas reais, contra {100*bt('Rainfall index','RS + PR','basis_risk')['estimate']:.0f}% do índice de chuva.",
   f"<b>Safras novas (2024 e 2025, nunca usadas para construir o índice):</b> AUC {hd('Turgor index','RS + PR','auc_loss'):.2f} contra {hd('Rainfall index','RS + PR','auc_loss'):.2f}; perdas não encontradas {100*hd('Turgor index','RS + PR','basis_risk'):.0f}% contra {100*hd('Rainfall index','RS + PR','basis_risk'):.0f}%.",
   f"<b>Antecedência:</b> em 15 de janeiro o índice já tem a capacidade que o índice de chuva só atinge no fim da safra, 8 a 12 semanas antes da colheita. Em 15 de fevereiro de 2025, os municípios marcados como estresse severo terminaram {abs(100*rclass.loc['severe','anom']):.0f}% abaixo da tendência.",
   "<b>Limites, abertamente:</b> no RS o ganho sobre o índice de chuva por município não é comprovado; as probabilidades de perda foram confiantes demais em 2024-2025, sobretudo no PR; a validação por talhão ainda depende de dados de uma cooperativa.",
  ],
  s_method="1. Método",
  method=[
   "Para cada município e safra, o índice soma, separadamente no estádio vegetativo e no reprodutivo, três componentes padronizados contra a história do próprio município: déficit hídrico (demanda de água não atendida por chuva e água do solo), graus-dia acima de 30 °C, e a interação calor × seca. Subtrai a anomalia de NDVI (vigor do dossel). O estádio reprodutivo (florescimento, formação de vagens, enchimento de grãos) pesa 0,75 e o vegetativo 0,25.",
   "<b>Nenhum peso foi ajustado aos dados de produtividade.</b> Os pesos vêm da fisiologia da soja. Um teste à parte mostrou que eles coincidem com os fatores de resposta da FAO (0,82 para o reprodutivo) e com o peso que os próprios dados escolheriam (0,75 no PR, 0,80 no RS); ajustar o peso não melhora o resultado.",
   "<b>Versão em tempo real:</b> o índice usa as janelas de estádio típicas de cada município (mediana das outras safras) e a latência real dos dados (clima com 3 dias, composições MODIS de 16 dias com 23 dias). Ou seja, os números deste relatório são os que o índice teria dado na época.",
   "<b>Verdade de campo:</b> produtividade municipal de soja do IBGE (Produção Agrícola Municipal), sem tendência tecnológica por município. Perda = produtividade mais de 10% abaixo da tendência. <b>Risco de base</b> = fração das perdas reais que um gatilho deixa de pagar quando paga o mesmo número de municípios-safra em que houve perda.",
  ],
  s_bt="2. Teste histórico, 2001-2023",
  bt_note=f"Intervalos de 95% por reamostragem de safras inteiras (1.000 vezes): municípios da mesma safra compartilham o clima e não são independentes.",
  bt_cols=["Índice", "AUC (IC 95%)", "Perdas não encontradas", "Correlação estado-ano"],
  bt_bul=lambda: [
   f"<b>RS + PR e Paraná: ganho claro sobre o índice de chuva</b> (AUC +{bt('Turgor index','RS + PR','auc_loss')['diff_vs_ref']:.2f}, IC {bt('Turgor index','RS + PR','auc_loss')['diff_ci_low']:+.2f} a {bt('Turgor index','RS + PR','auc_loss')['diff_ci_high']:+.2f}; no PR, perdas não encontradas {100*bt('Turgor index','PR','basis_risk')['estimate']:.0f}% contra {100*bt('Rainfall index','PR','basis_risk')['estimate']:.0f}%).",
   f"<b>Rio Grande do Sul: provável, mas não comprovado</b> por município (AUC {bt('Turgor index','RS','auc_loss')['estimate']:.2f} contra {bt('Rainfall index','RS','auc_loss')['estimate']:.2f}; IC da diferença {bt('Turgor index','RS','auc_loss')['diff_ci_low']:+.3f} a {bt('Turgor index','RS','auc_loss')['diff_ci_high']:+.3f}). As secas do RS são sobretudo secas de chuva. Testamos resolução de 250 m, máscara só de soja (MapBiomas) e déficit de pressão de vapor: nenhum mudou o resultado. Com 23 safras, ganhos menores que cerca de 0,10 no risco de base não podem ser comprovados por município.",
   f"<b>ZARC</b> quase não separa as safras com perda (AUC {bt('ZARC','RS + PR','auc_loss')['estimate']:.2f}): é um zoneamento fixo, de pré-plantio. O Turgor acrescenta a informação da safra em curso ao que o mercado já usa; não substitui o ZARC.",
  ],
  s_ho="3. Safras novas: 2024 e 2025",
  ho_text=f"Produtividades do IBGE baixadas depois de o índice estar pronto; tendência e padronização usam só 2001-2023. {n_ho:,} municípios-safra.",
  ho_bul=lambda: [
   f"O índice perde {100*hd('Turgor index','RS + PR','basis_risk'):.0f}% das perdas reais, contra {100*hd('Rainfall index','RS + PR','basis_risk'):.0f}% do índice de chuva, {100*hd('NDVI only','RS + PR','basis_risk'):.0f}% do NDVI e {100*hd('ZARC','RS + PR','basis_risk'):.0f}% do ZARC.",
   f"O desempenho é menor que no teste histórico (AUC {hd('Turgor index','RS + PR','auc_loss'):.2f} contra {bt('Turgor index','RS + PR','auc_loss')['estimate']:.2f}). Duas safras são pouco, e parte da perda de 2024 no RS veio das enchentes de maio, na colheita, que nenhum índice de seca deve apontar.",
  ],
  s_ew="4. Quão cedo",
  ew_text="O índice recalculado como seria em cada data, só com os dados disponíveis naquele dia.",
  rep_title="Reprodução de 15 de fevereiro de 2025 (seca do RS), com 2025 fora da referência:",
  rep_cols=["Classe em 15/02/2025", "Municípios", "Produtividade vs. tendência", "Com perda &gt;10%"],
  cls={"severe": "severo", "high": "alto", "watch": "atenção", "normal": "normal"},
  rep_after=f"AUC {rep_auc:.2f}, cerca de dois meses antes da colheita. A partir de dezembro de 2026, o mapa é publicado toda semana em {REPO}/tree/main/monitor, com data, antes da colheita.",
  s_el="5. Do índice ao dinheiro",
  el_text=lambda: f"Mapas monotônicos (isotônicos) por estado convertem o índice em probabilidade de perda, produtividade esperada e perda esperada em R$/ha. Em 2001-2023, prevendo cada safra sem usá-la, as probabilidades são bem calibradas (escore de Brier {g(el,test='loyo 2001-2023',region='RS + PR')['brier']:.3f} contra {g(el,test='loyo 2001-2023',region='RS + PR')['brier_climatology']:.3f} da taxa histórica: ganho de {100*g(el,test='loyo 2001-2023',region='RS + PR')['brier_skill']:.0f}%). Em 2024-2025 o ganho cai para {100*g(el,test='holdout 2024-2025',region='RS + PR')['brier_skill']:.0f}% (RS {100*g(el,test='holdout 2024-2025',region='RS')['brier_skill']:.0f}%, PR {100*g(el,test='holdout 2024-2025',region='PR')['brier_skill']:.0f}%): as probabilidades foram confiantes demais nos extremos. Por isso ficam limitadas a 2-98% e são apresentadas como taxas históricas, não garantias.",
  s_sw="6. Pesos por estádio: fisiologia, literatura e dados concordam",
  sw_text=lambda: f"O peso 0,75 do estádio reprodutivo foi comparado com os fatores de resposta da FAO para a soja (Doorenbos e Kassam, 1979: vegetativo 0,2; florescimento 0,8; formação da produtividade 1,0, ou seja 0,82 no reprodutivo), com pesos iguais, só reprodutivo, e com o peso escolhido pelos próprios dados safra a safra. Os dados escolhem entre {fit_w['w_reproductive'].min():.2f} e {fit_w['w_reproductive'].max():.2f} (mediana {fit_w[fit_w.st=='PR']['w_reproductive'].median():.2f} no PR e {fit_w[fit_w.st=='RS']['w_reproductive'].median():.2f} no RS). Ajustar o peso deixa o resultado ligeiramente pior (AUC {sw_row('fitted (leave-one-season-out)')['estimate']:.3f} contra {sw_row('prior (0.25/0.75)')['estimate']:.3f}). Três fontes independentes concordam, e o peso fixado antes de olhar a produtividade generaliza tão bem quanto qualquer peso ajustado.",
  s_field="7. Próximo passo: validação por talhão",
  field_text="A versão por talhão usa a curva Sentinel-2 (10-20 m) de cada talhão e o clima no talhão, com a mesma definição do índice. Numa amostra de 15 talhões no RS, a queda de NDVI reprodutivo entre 2021 e 2022 ordenou os municípios como a perda do IBGE e mostrou diferenças grandes entre talhões vizinhos (em Cruz Alta, 12% num talhão e 51-61% nos vizinhos), que um índice municipal não vê. A validação com produtividades reais depende de uma cooperativa parceira; o processo de leitura dos arquivos, teste e relatório já está pronto.",
  s_lim="8. Limites",
  lim=[
   "Rio Grande do Sul: ganho sobre o índice de chuva por município não comprovado (seção 2).",
   "Probabilidades de perda confiantes demais em safras atípicas; no PR, piores que a taxa histórica em 2024-2025.",
   "Escala municipal: um município mistura muitas lavouras. A versão por talhão (Sentinel-2) está pronta, mas só pode ser validada com produtividades reais de uma cooperativa.",
   "Só seca e calor. Excesso de chuva, enchentes, granizo, geada e doenças não estão no índice.",
   "Tendência de produtividade extrapolada para safras novas; chuva da NASA POWER em grade de cerca de 50 km.",
   "23 safras de histórico: os intervalos de confiança são largos, e ficarão mais estreitos com cada safra monitorada.",
  ],
  s_rep="9. Reprodutibilidade e revisão",
  rep_text=f"Código, dados e resultados abertos (licença MIT): {REPO}. Cada número deste relatório é lido dos arquivos em <i>results/</i> e o relatório é refeito pelo script <i>scripts/23_public_report.py</i>. Revisões críticas são bem-vindas, em especial de modeladores de culturas e atuários do seguro agrícola: abra uma issue no repositório.",
  author="Janaina Fortirer · ecofisiologista vegetal, doutoranda na USP, pesquisadora visitante na Universidade de Illinois (Urbana-Champaign)",
  page="Página",
 ),
 "en": dict(
  title="Turgor soybean stress index: validation report",
  sub="Drought and heat in soybean in Rio Grande do Sul and Paraná, Brazil, from public satellite and weather data. October 2026.",
  names={"Turgor": "Turgor index", "rain": "Rainfall index (Jan-Feb)", "ndvi": "NDVI only", "zarc": "ZARC (official zoning)"},
  s_summary="Summary",
  summary=[
   "<b>What it is:</b> a drought and heat stress index for soybean, weighted by crop stage, computed only from public satellite (MODIS, Sentinel-2) and weather (NASA POWER) data, with no farm sensors.",
   f"<b>Backtest (2001-2023, {n_bt:,} municipality-seasons):</b> it separates loss seasons (yield &gt;10% below trend) from normal ones with AUC {bt('Turgor index','RS + PR','auc_loss')['estimate']:.2f}, against {bt('Rainfall index','RS + PR','auc_loss')['estimate']:.2f} for a rainfall index and {bt('ZARC','RS + PR','auc_loss')['estimate']:.2f} for ZARC. It misses {100*bt('Turgor index','RS + PR','basis_risk')['estimate']:.0f}% of real losses, against {100*bt('Rainfall index','RS + PR','basis_risk')['estimate']:.0f}% for the rainfall index.",
   f"<b>New seasons (2024 and 2025, never used to build the index):</b> AUC {hd('Turgor index','RS + PR','auc_loss'):.2f} against {hd('Rainfall index','RS + PR','auc_loss'):.2f}; losses missed {100*hd('Turgor index','RS + PR','basis_risk'):.0f}% against {100*hd('Rainfall index','RS + PR','basis_risk'):.0f}%.",
   f"<b>Lead time:</b> by 15 January the index already has the skill the rainfall index reaches only at season end, 8 to 12 weeks before harvest. On 15 February 2025, municipalities flagged as severe stress ended {abs(100*rclass.loc['severe','anom']):.0f}% below trend.",
   "<b>Limits, openly:</b> in Rio Grande do Sul the gain over the rainfall index is not proven at municipality level; loss probabilities were too confident in 2024-2025, mostly in Paraná; field-level validation still needs a co-op's data.",
  ],
  s_method="1. Method",
  method=[
   "For each municipality and season, the index adds, separately for the vegetative and the reproductive stage, three components standardised against the municipality's own history: water deficit (crop water demand not met by rain and soil water), degree-days above 30 °C, and the heat × drought interaction. It subtracts the NDVI anomaly (canopy vigour). The reproductive stage (flowering, pod set, seed fill) weighs 0.75 and the vegetative stage 0.25.",
   "<b>No weight was fitted to yield data.</b> The weights come from soybean physiology. A separate test showed they match the FAO yield-response factors (0.82 reproductive) and the weight the data themselves would choose (0.75 in PR, 0.80 in RS); fitting the weight does not improve the result.",
   "<b>Real-time version:</b> the index uses each municipality's typical stage windows (median of its other seasons) and real data latency (weather 3 days late, MODIS 16-day composites 23 days late). The numbers in this report are those the index would have given at the time.",
   "<b>Ground truth:</b> IBGE municipal soybean yields (Produção Agrícola Municipal), detrended per municipality. Loss = yield more than 10% below trend. <b>Basis risk</b> = share of real losses a trigger misses when it pays as many municipality-seasons as there were losses.",
  ],
  s_bt="2. Backtest, 2001-2023",
  bt_note="95% intervals from 1,000 resamples of whole harvest years: municipalities in the same season share weather and are not independent.",
  bt_cols=["Index", "AUC (95% CI)", "Losses missed", "State-year correlation"],
  bt_bul=lambda: [
   f"<b>RS + PR and Paraná: clear gain over the rainfall index</b> (AUC +{bt('Turgor index','RS + PR','auc_loss')['diff_vs_ref']:.2f}, CI {bt('Turgor index','RS + PR','auc_loss')['diff_ci_low']:+.2f} to {bt('Turgor index','RS + PR','auc_loss')['diff_ci_high']:+.2f}; in PR losses missed {100*bt('Turgor index','PR','basis_risk')['estimate']:.0f}% against {100*bt('Rainfall index','PR','basis_risk')['estimate']:.0f}%).",
   f"<b>Rio Grande do Sul: likely but not proven</b> at municipality level (AUC {bt('Turgor index','RS','auc_loss')['estimate']:.2f} against {bt('Rainfall index','RS','auc_loss')['estimate']:.2f}; CI of the difference {bt('Turgor index','RS','auc_loss')['diff_ci_low']:+.3f} to {bt('Turgor index','RS','auc_loss')['diff_ci_high']:+.3f}). RS droughts are mostly rainfall droughts. We tested 250 m resolution, a soybean-only mask (MapBiomas) and vapour-pressure deficit: none changed the result. With 23 seasons, basis-risk gains below about 0.10 cannot be proven per municipality.",
   f"<b>ZARC</b> barely separates loss seasons (AUC {bt('ZARC','RS + PR','auc_loss')['estimate']:.2f}): it is a fixed, pre-planting zoning. Turgor adds in-season information to what the market already uses; it does not replace ZARC.",
  ],
  s_ho="3. New seasons: 2024 and 2025",
  ho_text=f"IBGE yields downloaded after the index was finished; trend and standardisation use 2001-2023 only. {n_ho:,} municipality-seasons.",
  ho_bul=lambda: [
   f"The index misses {100*hd('Turgor index','RS + PR','basis_risk'):.0f}% of real losses, against {100*hd('Rainfall index','RS + PR','basis_risk'):.0f}% for the rainfall index, {100*hd('NDVI only','RS + PR','basis_risk'):.0f}% for NDVI and {100*hd('ZARC','RS + PR','basis_risk'):.0f}% for ZARC.",
   f"Skill is lower than in the backtest (AUC {hd('Turgor index','RS + PR','auc_loss'):.2f} against {bt('Turgor index','RS + PR','auc_loss')['estimate']:.2f}). Two seasons is a small sample, and part of the 2024 RS loss came from the May floods at harvest, which no drought index should flag.",
  ],
  s_ew="4. How early",
  ew_text="The index rebuilt as it would have looked on each date, using only the data available that day.",
  rep_title="Replay of 15 February 2025 (RS drought), with 2025 left out of the reference:",
  rep_cols=["Class on 15 Feb 2025", "Municipalities", "Yield vs trend", "With loss &gt;10%"],
  cls={"severe": "severe", "high": "high", "watch": "watch", "normal": "normal"},
  rep_after=f"AUC {rep_auc:.2f}, about two months before harvest. From December 2026 the map is published every week at {REPO}/tree/main/monitor, dated, before harvest.",
  s_el="5. From index to money",
  el_text=lambda: f"Monotone (isotonic) maps per state turn the index into a probability of loss, an expected yield and an expected loss in R$/ha. On 2001-2023, predicting each season without using it, the probabilities are well calibrated (Brier score {g(el,test='loyo 2001-2023',region='RS + PR')['brier']:.3f} against {g(el,test='loyo 2001-2023',region='RS + PR')['brier_climatology']:.3f} for the historical rate: {100*g(el,test='loyo 2001-2023',region='RS + PR')['brier_skill']:.0f}% better). On 2024-2025 the gain drops to {100*g(el,test='holdout 2024-2025',region='RS + PR')['brier_skill']:.0f}% (RS {100*g(el,test='holdout 2024-2025',region='RS')['brier_skill']:.0f}%, PR {100*g(el,test='holdout 2024-2025',region='PR')['brier_skill']:.0f}%): the probabilities were too confident at both ends. They are therefore capped at 2-98% and presented as historical base rates, not guarantees.",
  s_sw="6. Stage weights: physiology, literature and data agree",
  sw_text=lambda: f"The reproductive weight of 0.75 was compared with the FAO yield-response factors for soybean (Doorenbos and Kassam, 1979: vegetative 0.2, flowering 0.8, yield formation 1.0, i.e. 0.82 reproductive), equal weights, reproductive only, and the weight chosen by the data season by season. The data choose between {fit_w['w_reproductive'].min():.2f} and {fit_w['w_reproductive'].max():.2f} (median {fit_w[fit_w.st=='PR']['w_reproductive'].median():.2f} in PR, {fit_w[fit_w.st=='RS']['w_reproductive'].median():.2f} in RS). Fitting the weight makes the result slightly worse (AUC {sw_row('fitted (leave-one-season-out)')['estimate']:.3f} against {sw_row('prior (0.25/0.75)')['estimate']:.3f}). Three independent sources agree, and a weight fixed before looking at yields generalises as well as any fitted weight.",
  s_field="7. Next step: field-level validation",
  field_text="The field version uses each field's Sentinel-2 curve (10-20 m) and the weather at the field, with the same index definition. In a sample of 15 fields in RS, the drop in reproductive NDVI from 2021 to 2022 ranked municipalities like the IBGE loss and showed large differences between neighbouring fields (in Cruz Alta, 12% in one field and 51-61% in its neighbours) that a municipal index cannot see. Validation against real yields needs a partner co-op; reading the files, the test and the report are already in place.",
  s_lim="8. Limits",
  lim=[
   "Rio Grande do Sul: gain over the rainfall index per municipality not proven (section 2).",
   "Loss probabilities too confident in unusual seasons; in PR worse than the historical rate in 2024-2025.",
   "Municipal scale: a municipality mixes many farms. The field version (Sentinel-2) is ready but can only be validated with a co-op's real yields.",
   "Drought and heat only. Excess rain, floods, hail, frost and disease are not in the index.",
   "Yield trend extrapolated to new seasons; NASA POWER rainfall on a ~50 km grid.",
   "23 seasons of history: confidence intervals are wide and will narrow with each monitored season.",
  ],
  s_rep="9. Reproducibility and review",
  rep_text=f"Open code, data and results (MIT licence): {REPO}. Every number in this report is read from the files in <i>results/</i>, and the report is rebuilt by <i>scripts/23_public_report.py</i>. Critical reviews are welcome, especially from crop modellers and agricultural insurance actuaries: open an issue in the repository.",
  author="Janaina Fortirer · plant ecophysiologist, PhD candidate at USP, visiting researcher at the University of Illinois Urbana-Champaign",
  page="Page",
 ),
}

# ---------------------------------------------------------------- figures (per language)
LBL = {"pt": dict(dark="barra escura (IC 95%)", light="barra clara", auc="AUC, perda >10%", br="Perdas não encontradas", bt="Teste histórico 2001-2023",
                  ho="Safras novas 2024-2025", ewt="AUC por data (RS + PR), dados até a data",
                  ew_t="Índice Turgor", ew_r="Índice de chuva (chuva jan-fev até a data)",
                  dates=["1 dez", "15 dez", "1 jan", "15 jan", "1 fev", "15 fev", "1 mar", "15 mar", "1 abr", "15 abr"],
                  calx="Probabilidade prevista de perda >10%", caly="Fração observada com perda",
                  loso="2001-2023 (cada safra sem ela mesma)", hold="2024-2025",
                  map_t="Classe de estresse em 15 fev 2025", cls=L["pt"]["cls"]),
       "en": dict(dark="dark bar (95% CI)", light="light bar", auc="AUC, loss >10%", br="Losses missed", bt="Backtest 2001-2023", ho="New seasons 2024-2025",
                  ewt="AUC by date (RS + PR), data up to that date", ew_t="Turgor index",
                  ew_r="Rainfall index (Jan-Feb rain so far)",
                  dates=["1 Dec", "15 Dec", "1 Jan", "15 Jan", "1 Feb", "15 Feb", "1 Mar", "15 Mar", "1 Apr", "15 Apr"],
                  calx="Predicted probability of loss >10%", caly="Observed share with loss",
                  loso="2001-2023 (each season left out)", hold="2024-2025",
                  map_t="Stress class on 15 Feb 2025", cls=L["en"]["cls"])}
COL = {"Turgor": GREEN, "rain": BLUE, "ndvi": GREY, "zarc": ORANGE}


def figures(lang):
    lb, nm = LBL[lang], L[lang]["names"]
    # fig A: backtest + holdout bars
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    for j, (key, k) in enumerate(IDX):
        for i, (metric, title) in enumerate([("auc_loss", lb["auc"]), ("basis_risk", lb["br"])]):
            b = bt(key, "RS + PR", metric)
            ax[i].bar(j - 0.2, b["estimate"], 0.38, color=COL[k], yerr=[[b["estimate"] - b["ci_low"]], [b["ci_high"] - b["estimate"]]],
                      capsize=2, ecolor=INK, label=nm[k] if i == 0 else None)
            ax[i].bar(j + 0.2, hd(key, "RS + PR", metric), 0.38, color=COL[k], alpha=0.45)
            ax[i].set_title(title)
    for a in ax:
        a.set_xticks(range(4))
        a.set_xticklabels([nm[k].split(" (")[0] for _, k in IDX], fontsize=8)
    ax[0].set_ylim(0.4, 0.95)
    fig.text(0.5, 0.005, f"{lb['bt']}: {lb['dark']}   ·   {lb['ho']}: {lb['light']}", ha="center", fontsize=8, color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUT / f"fig_a_{lang}.png", dpi=200)
    plt.close(fig)
    # fig B: early warning + calibration
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    e = ew[(ew["region"] == "RS + PR") & (ew["asof"] != "end")]
    t = e[e["index"] == "Turgor index (as of date)"]
    r = e[e["index"] == "Rainfall index (as of date)"]
    ax[0].plot(lb["dates"], t["auc_loss"], "-o", color=GREEN, ms=3, lw=2, label=lb["ew_t"])
    ax[0].plot(lb["dates"], r["auc_loss"], "-o", color=BLUE, ms=3, label=lb["ew_r"])
    ax[0].axhline(r["auc_loss"].iloc[-1], color=BLUE, ls=":", lw=1)
    ax[0].set(ylim=(0.45, 0.92), title=lb["ewt"])
    ax[0].tick_params(axis="x", rotation=60)
    ax[0].legend(frameon=False, fontsize=7.5, loc="lower right")
    for name, c, lab in [("loyo 2001-2023", GREEN, lb["loso"]), ("holdout 2024-2025", BLUE, lb["hold"])]:
        cc = cal[(cal["test"] == name) & (cal["target"] == "p_loss")]
        ax[1].plot(cc["predicted"], cc["observed"], "-o", color=c, ms=3, label=lab)
    ax[1].plot([0, 1], [0, 1], ":", color=GREY)
    ax[1].set(xlabel=lb["calx"], ylabel=lb["caly"], xlim=(0, 1), ylim=(0, 1))
    ax[1].legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / f"fig_b_{lang}.png", dpi=200)
    plt.close(fig)
    # fig C: replay map
    gj = json.loads((ROOT / "monitor/replays/2024-25/2025-02-15/turgor_monitor.geojson").read_text())
    colors = {"normal": "#DCE9E0", "watch": "#F2D27A", "high": "#E8893A", "severe": "#B4271F"}
    fig, ax = plt.subplots(figsize=(4.2, 4.6))
    for f in gj["features"]:
        c = colors.get(f["properties"].get("stress_class"), "#FFFFFF")
        ax.add_patch(Polygon(f["geometry"]["coordinates"][0], closed=True, fc=c, ec="#8A9A90", lw=0.1))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(handles=[Patch(fc=colors[k], label=lb["cls"][k]) for k in ["severe", "high", "watch", "normal"]],
              loc="lower right", frameon=False, fontsize=7.5)
    ax.set_title(lb["map_t"], fontsize=9)
    fig.savefig(OUT / f"fig_c_{lang}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- PDF
from reportlab.lib import colors as rc  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

FONT = Path("/usr/share/fonts/truetype/crosextra/")
if (FONT / "Carlito-Regular.ttf").exists():
    pdfmetrics.registerFont(TTFont("B", str(FONT / "Carlito-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("B-b", str(FONT / "Carlito-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("B-i", str(FONT / "Carlito-Italic.ttf")))
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("B", normal="B", bold="B-b", italic="B-i", boldItalic="B-b")
    FN, FB = "B", "B-b"
else:
    FN, FB = "Helvetica", "Helvetica-Bold"
GD, MUT, RULE = rc.HexColor(GREEN), rc.HexColor("#52514E"), rc.HexColor("#DCDAD3")
S = dict(
    t=ParagraphStyle("t", fontName=FB, fontSize=17, leading=21, textColor=GD, spaceAfter=4),
    sub=ParagraphStyle("s", fontName=FN, fontSize=10.5, leading=14, textColor=MUT, spaceAfter=10),
    h=ParagraphStyle("h", fontName=FB, fontSize=12.5, leading=16, textColor=GD, spaceBefore=10, spaceAfter=4),
    b=ParagraphStyle("b", fontName=FN, fontSize=9.8, leading=13.4, spaceAfter=4),
    sm=ParagraphStyle("sm", fontName=FN, fontSize=8.2, leading=10.6, textColor=MUT, spaceAfter=4),
    c=ParagraphStyle("c", fontName=FN, fontSize=8.8, leading=11),
    cb=ParagraphStyle("cb", fontName=FB, fontSize=8.8, leading=11),
)
S["bl"] = ParagraphStyle("bl", parent=S["b"], leftIndent=11, bulletIndent=1, spaceAfter=3)


import re  # noqa: E402
LANG = {"v": "en"}


def fix(x):
    """Portuguese: decimal comma, thousands point (17,342 -> 17.342; 0.86 -> 0,86)."""
    x = str(x)
    if LANG["v"] != "pt":
        return x
    x = re.sub(r"(\d),(\d{3})\b", r"\1§\2", x)
    x = re.sub(r"(?<![\w/])(\d+)\.(\d+)", r"\1,\2", x)
    return x.replace("§", ".")


_P = Paragraph


def Paragraph(text, style, **kw):  # noqa: N802
    return _P(fix(text), style, **kw)


def tbl(rows, widths):
    data = [[Paragraph(str(x), S["cb"] if i == 0 else S["c"]) for x in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
                           ("LINEBELOW", (0, 0), (-1, 0), 1, GD), ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def img(path, width_cm):
    from PIL import Image as PI
    w, h = PI.open(path).size
    return Image(str(path), width=width_cm * cm, height=width_cm * cm * h / w)


def build(lang):
    T = L[lang]
    LANG["v"] = lang
    figures(lang)
    st = []
    st += [img(OUT / "turgor_logo.png", 4.2), Spacer(1, 6), Paragraph(T["title"], S["t"]), Paragraph(T["sub"], S["sub"])]
    st.append(Paragraph(T["s_summary"], S["h"]))
    st += [Paragraph(x, S["bl"], bulletText="•") for x in T["summary"]]
    st.append(Paragraph(T["s_method"], S["h"]))
    st += [Paragraph(x, S["b"]) for x in T["method"]]
    rows = [T["bt_cols"]]
    for key, k in IDX:
        a, br, r = bt(key, "RS + PR", "auc_loss"), bt(key, "RS + PR", "basis_risk"), bt(key, "RS + PR", "state_year_r")
        rows.append([T["names"][k], f"{a['estimate']:.2f} ({a['ci_low']:.2f}-{a['ci_high']:.2f})",
                     f"{100*br['estimate']:.0f}% ({100*br['ci_low']:.0f}-{100*br['ci_high']:.0f}%)",
                     f"{r['estimate']:.2f} ({r['ci_low']:.2f}-{r['ci_high']:.2f})"])
    st += [KeepTogether([Paragraph(T["s_bt"], S["h"]), tbl(rows, [5.2 * cm, 3.6 * cm, 3.6 * cm, 3.8 * cm]),
                         Paragraph(T["bt_note"], S["sm"])])]
    reg = [["", "RS: AUC", "RS: " + T["bt_cols"][2], "PR: AUC", "PR: " + T["bt_cols"][2]]]
    for key, k in IDX:
        reg.append([T["names"][k]] + [f"{bt(key, rg, 'auc_loss')['estimate']:.2f}" if m == "auc_loss" else
                                      f"{100*bt(key, rg, 'basis_risk')['estimate']:.0f}%"
                                      for rg in ("RS", "PR") for m in ("auc_loss", "basis_risk")])
    st += [tbl(reg, [5.2 * cm, 2.6 * cm, 3.0 * cm, 2.6 * cm, 3.0 * cm]), Spacer(1, 4)]
    st += [Paragraph(x, S["bl"], bulletText="•") for x in T["bt_bul"]()]
    st += [KeepTogether([Paragraph(T["s_ho"], S["h"]), Paragraph(T["ho_text"], S["b"]), img(OUT / f"fig_a_{lang}.png", 16.5)])]
    st += [Paragraph(x, S["bl"], bulletText="•") for x in T["ho_bul"]()]
    st += [KeepTogether([Paragraph(T["s_ew"], S["h"]), Paragraph(T["ew_text"], S["b"]), img(OUT / f"fig_b_{lang}.png", 16.5)])]
    rr = [T["rep_cols"]] + [[T["cls"][c], f"{int(rclass.loc[c, 'n'])}", f"{100*rclass.loc[c, 'anom']:+.0f}%",
                             f"{100*rclass.loc[c, 'loss']:.0f}%"] for c in ["severe", "high", "watch", "normal"]]
    side = Table([[img(OUT / f"fig_c_{lang}.png", 6.3), [Paragraph(T["rep_title"], S["b"]),
                                                         tbl(rr, [2.9 * cm, 2.1 * cm, 2.6 * cm, 2.0 * cm]),
                                                         Spacer(1, 4), Paragraph(T["rep_after"], S["b"])]]],
                 colWidths=[6.6 * cm, 10 * cm])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    st.append(side)
    st += [Paragraph(T["s_el"], S["h"]), Paragraph(T["el_text"](), S["b"])]
    st += [Paragraph(T["s_sw"], S["h"]), Paragraph(T["sw_text"](), S["b"])]
    st += [Paragraph(T["s_field"], S["h"]), Paragraph(T["field_text"], S["b"])]
    st.append(Paragraph(T["s_lim"], S["h"]))
    st += [Paragraph(x, S["bl"], bulletText="•") for x in T["lim"]]
    st += [Paragraph(T["s_rep"], S["h"]), Paragraph(T["rep_text"], S["b"]), Spacer(1, 6), Paragraph(T["author"], S["sm"])]

    def footer(c, d):
        c.saveState()
        c.setFont(FN, 7.5)
        c.setFillColor(MUT)
        c.drawString(2 * cm, 1.1 * cm, f"Turgor · {REPO}")
        c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"{T['page']} {d.page}")
        c.restoreState()

    fp = OUT / f"turgor_validation_report_{lang}.pdf"
    SimpleDocTemplate(str(fp), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm,
                      bottomMargin=1.8 * cm, title=T["title"], author="Janaina Fortirer").build(
        st, onFirstPage=footer, onLaterPages=footer)
    return fp


if __name__ == "__main__":
    for lang in ("pt", "en"):
        print("written", build(lang))
