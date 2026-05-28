"""
app.py
------
Servidor web Flask para apresentação dos dados de
Queimadas × Agronegócio no Maranhão (2019–2024).

Como rodar:
    pip install flask pandas
    python app.py

Acesse: http://localhost:5000
"""

from flask import Flask, render_template, jsonify
from analise_queimadas_co2 import (
    carregar_focos,
    agregar_focos,
    carregar_co2,
    correlacionar,
)
import pandas as pd
import os

app = Flask(__name__)

# Filtro Jinja2 para formatar números no padrão brasileiro
@app.template_filter("format_br")
def format_br(value):
    return f"{int(value):,}".replace(",", ".")

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────
PASTA_FOCOS   = os.path.join("dados", "queimadasMA")
ARQUIVO_GASES = os.path.join("dados", "gases.csv")
ANOS          = range(2019, 2025)


def _carregar_todos_dados() -> dict:
    """Processa todos os dados e retorna um dicionário pronto para o template."""

    focos       = carregar_focos(PASTA_FOCOS, ANOS)
    focos_ano, focos_bioma = agregar_focos(focos)
    co2_df      = carregar_co2(ARQUIVO_GASES, ANOS)
    tabela      = correlacionar(focos_ano, co2_df)

    # ── Agronegócio ──────────────────────────────────────
    gases = pd.read_csv(ARQUIVO_GASES, sep=None, engine="python")
    ma    = gases[gases["Cidade"].str.contains(r"\(MA\)", na=False)]
    anos_cols = [str(a) for a in ANOS]

    def _soma_setor(setor: str) -> list[float]:
        df = ma[(ma["Gás"] == "CO2 (t)") & (ma["Setor de emissão"] == setor)]
        return [(df[c].sum() / 1e6) for c in anos_cols]

    co2_mut  = _soma_setor("Mudança de Uso da Terra e Floresta")
    co2_agro = _soma_setor("Agropecuária")
    co2_outros = [
        round(t - m - a, 2)
        for t, m, a in zip(tabela["co2_Mt"].tolist(), co2_mut, co2_agro)
    ]

    pct_agro = [
        round((m + abs(a)) / t * 100, 1)
        for t, m, a in zip(tabela["co2_Mt"].tolist(), co2_mut, co2_agro)
    ]

    # ── Sazonalidade mensal ───────────────────────────────
    focos_cp = focos.copy()
    focos_cp["mes"] = focos_cp["data_pas"].dt.month
    por_mes = (
        focos_cp.groupby("mes")
        .size()
        .reindex(range(1, 13), fill_value=0)
        .tolist()
    )

    # ── Biomas ───────────────────────────────────────────
    pivot = (
        focos_bioma
        .pivot(index="ano", columns="bioma", values="focos")
        .fillna(0)
        .astype(int)
    )
    biomas_data = {
        col: pivot[col].tolist()
        for col in pivot.columns
    }

    # ── Correlação de Pearson ─────────────────────────────
    r = tabela["total_focos"].corr(tabela["co2_toneladas"])

    # ── Tabela para o template ────────────────────────────
    tabela_rows = []
    max_focos = tabela["total_focos"].max()
    for i, row in tabela.iterrows():
        tabela_rows.append({
            "ano":        int(row["ano"]),
            "focos":      f"{int(row['total_focos']):,}".replace(",", "."),
            "co2_total":  f"{row['co2_Mt']:.1f}",
            "co2_mut":    f"{co2_mut[i - tabela.index[0]]:.1f}",
            "co2_agro":   f"{co2_agro[i - tabela.index[0]]:.1f}",
            "pct_agro":   f"{pct_agro[i - tabela.index[0]]:.1f}",
            "co2_foco":   f"{int(row['co2_por_foco']):,}".replace(",", "."),
            "barra_pct":  int(row["total_focos"] / max_focos * 100),
        })

    return {
        # séries para Chart.js
        "anos":       list(map(int, tabela["ano"].tolist())),
        "focos":      tabela["total_focos"].astype(int).tolist(),
        "co2_total":  [round(v, 1) for v in tabela["co2_Mt"].tolist()],
        "co2_mut":    [round(v, 1) for v in co2_mut],
        "co2_agro":   [round(v, 1) for v in co2_agro],
        "co2_outros": co2_outros,
        "co2_foco":   [int(v) for v in tabela["co2_por_foco"].tolist()],
        "pct_agro":   pct_agro,
        "focos_mes":  por_mes,
        "biomas":     biomas_data,
        "pearson_r":  round(r, 4),
        # cards hero
        "total_focos_fmt": f"{tabela['total_focos'].sum():,}".replace(",", "."),
        "total_co2_fmt":   f"{tabela['co2_Mt'].sum():.0f}",
        "pct_agro_medio":  f"{sum(pct_agro)/len(pct_agro):.0f}",
        # tabela HTML
        "tabela_rows": tabela_rows,
    }


# ─────────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────────
@app.route("/")
def index():
    dados = _carregar_todos_dados()
    return render_template("index.html", **dados)


@app.route("/api/dados")
def api_dados():
    """Endpoint JSON — útil para debug ou integrações futuras."""
    dados = _carregar_todos_dados()
    dados.pop("tabela_rows", None)   # remove lista de dicts para serialização limpa
    return jsonify(dados)


# ─────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
