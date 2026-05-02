"""
visualizacoes.py
----------------
Responsabilidade única: gerar gráficos e tabelas a partir dos
DataFrames já processados por analise_queimadas_co2.py.

Não faz leitura de arquivos nem processamento de dados.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import os

# ─────────────────────────────────────────────
# CONFIGURAÇÃO GLOBAL DE ESTILO
# ─────────────────────────────────────────────
PASTA_SAIDA = "graficos"          # pasta onde os PNGs serão salvos
SALVAR      = True              # True → salva PNG
MOSTRAR     = True                # True → abre janela interativa

CORES_BIOMA = {
    "Amazônia": "#1D9E75",
    "Cerrado":  "#D85A30",
    "Caatinga": "#BA7517",
}

def _configurar_estilo():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor":   "white",
        "axes.grid":        True,
        "grid.alpha":       0.3,
        "axes.spines.top":  False,
        "axes.spines.right":False,
        "font.size":        11,
    })

def _salvar_ou_mostrar(fig: plt.Figure, nome_arquivo: str) -> None:
    """Salva e/ou exibe a figura conforme as flags globais."""
    if SALVAR:
        os.makedirs(PASTA_SAIDA, exist_ok=True)
        caminho = os.path.join(PASTA_SAIDA, nome_arquivo)
        fig.savefig(caminho, dpi=150, bbox_inches="tight")
        print(f"  → Salvo em: {caminho}")
    if MOSTRAR:
        plt.show()
    plt.close(fig)


# ─────────────────────────────────────────────
# 1. HISTOGRAMA — focos por mês
# ─────────────────────────────────────────────
def plotar_histograma_mensal(focos: pd.DataFrame) -> None:
    """
    Histograma de quantidade de focos agrupados por mês do ano
    (todos os anos somados), para identificar sazonalidade.

    Parâmetro
    ---------
    focos : DataFrame com coluna 'data_pas' (datetime) e 'ano'.
    """
    _configurar_estilo()

    df = focos.copy()
    df["mes"] = df["data_pas"].dt.month
    por_mes = df.groupby("mes").size().reindex(range(1, 13), fill_value=0)

    meses_label = ["Jan","Fev","Mar","Abr","Mai","Jun",
                   "Jul","Ago","Set","Out","Nov","Dez"]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(range(1, 13), por_mes.values, color="#D85A30", alpha=0.85, width=0.7)

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(meses_label)
    ax.set_xlabel("Mês")
    ax.set_ylabel("Total de focos")
    ax.set_title("Distribuição mensal de focos de queimada — MA (2019–2024)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",",".")))

    # Rótulo em cima de cada barra
    for bar in bars:
        altura = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, altura + 100,
                f"{int(altura):,}".replace(",", "."),
                ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    _salvar_ou_mostrar(fig, "01_histograma_mensal.png")


# ─────────────────────────────────────────────
# 2. LINHA — CO2 ao longo dos anos
# ─────────────────────────────────────────────
def plotar_linha_co2(tabela: pd.DataFrame) -> None:
    """
    Gráfico de linha com as emissões de CO2 anuais em megatoneladas.

    Parâmetro
    ---------
    tabela : DataFrame com colunas 'ano' e 'co2_Mt'.
    """
    _configurar_estilo()

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(tabela["ano"], tabela["co2_Mt"],
            marker="o", linewidth=2.5, color="#185FA5",
            markersize=7, markerfacecolor="white", markeredgewidth=2)

    for _, row in tabela.iterrows():
        ax.annotate(f"{row['co2_Mt']:.1f} Mt",
                    xy=(row["ano"], row["co2_Mt"]),
                    xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=9, color="#185FA5")

    ax.set_xticks(tabela["ano"])
    ax.set_xlabel("Ano")
    ax.set_ylabel("CO2 emitido (Mt)")
    ax.set_title("Emissões de CO2 no Maranhão — 2019 a 2024")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f} Mt"))

    fig.tight_layout()
    _salvar_ou_mostrar(fig, "02_linha_co2.png")


# ─────────────────────────────────────────────
# 3. BARRAS EMPILHADAS — focos por bioma
# ─────────────────────────────────────────────
def plotar_barras_bioma(focos_bioma: pd.DataFrame) -> None:
    """
    Barras empilhadas com a quantidade de focos por bioma em cada ano.

    Parâmetro
    ---------
    focos_bioma : DataFrame com colunas 'ano', 'bioma', 'focos'.
    """
    _configurar_estilo()

    pivot = (focos_bioma
             .pivot(index="ano", columns="bioma", values="focos")
             .fillna(0))

    anos = pivot.index.tolist()
    biomas = pivot.columns.tolist()
    bottom = [0] * len(anos)

    fig, ax = plt.subplots(figsize=(10, 6))

    for bioma in biomas:
        valores = pivot[bioma].tolist()
        cor = CORES_BIOMA.get(bioma, "#888780")
        ax.bar(anos, valores, bottom=bottom, label=bioma,
               color=cor, alpha=0.88, width=0.6)
        bottom = [b + v for b, v in zip(bottom, valores)]

    ax.set_xticks(anos)
    ax.set_xlabel("Ano")
    ax.set_ylabel("Focos de queimada")
    ax.set_title("Focos por bioma — Maranhão (2019–2024)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",",".")))
    ax.legend(title="Bioma", loc="upper left")

    fig.tight_layout()
    _salvar_ou_mostrar(fig, "03_barras_bioma.png")


# ─────────────────────────────────────────────
# 4. TABELA FORMATADA NO TERMINAL
# ─────────────────────────────────────────────
def imprimir_tabela(tabela: pd.DataFrame) -> None:
    """
    Exibe uma tabela formatada com os principais indicadores anuais.

    Parâmetro
    ---------
    tabela : DataFrame com colunas 'ano', 'total_focos',
             'co2_Mt', 'co2_por_foco'.
    """
    sep = "─" * 62
    print(f"\n{sep}")
    print(f"  {'ANO':<6} {'FOCOS':>10} {'CO2 (Mt)':>10} {'CO2/FOCO (t)':>14}")
    print(sep)
    for _, row in tabela.iterrows():
        print(
            f"  {int(row['ano']):<6} "
            f"{int(row['total_focos']):>10,} "
            f"{row['co2_Mt']:>10.1f} "
            f"{row['co2_por_foco']:>14,.0f}"
        )
    print(sep)
    print(f"  {'TOTAL':<6} {int(tabela['total_focos'].sum()):>10,} "
          f"{tabela['co2_Mt'].sum():>10.1f}")
    print(sep)

    r = tabela["total_focos"].corr(tabela["co2_toneladas"])
    print(f"\n  Correlação de Pearson (focos x CO2): {r:.4f}")
    forca = "forte" if abs(r) >= 0.7 else "moderada" if abs(r) >= 0.4 else "fraca"
    print(f"  → Correlação {forca}\n")
