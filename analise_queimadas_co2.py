"""
Análise de correlação: Focos de queimada x Emissões de CO2 no Maranhão
Período: 2019 a 2024
Fontes: INPE/BDQueimadas (focos) e SEEG (emissões de gases)
"""

import pandas as pd
import glob
import os

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÃO — ajuste os caminhos conforme
#    a estrutura das suas pastas
# ─────────────────────────────────────────────
PASTA_FOCOS  = "queimadasMA"           # pasta com os arquivos focos_br_ma_ref_XXXX.csv
PASTA_GASES  = "MA"           # pasta com o arquivo gases.csv
ARQUIVO_GASES = os.path.join(PASTA_GASES, "gases.csv")
ANOS = range(2019, 2025)


# ─────────────────────────────────────────────
# 2. CARREGA E CONSOLIDA OS FOCOS DE QUEIMADA
# ─────────────────────────────────────────────
def carregar_focos(pasta: str, anos) -> pd.DataFrame:
    """Lê todos os CSVs de focos e retorna um DataFrame unificado."""
    dfs = []
    for ano in anos:
        caminho = os.path.join(pasta, f"focos_br_ma_ref_{ano}.csv")
        if not os.path.exists(caminho):
            print(f"[aviso] Arquivo não encontrado: {caminho}")
            continue
        df = pd.read_csv(caminho)
        df["ano"] = ano
        dfs.append(df)

    if not dfs:
        raise FileNotFoundError("Nenhum arquivo de focos encontrado.")

    focos = pd.concat(dfs, ignore_index=True)
    focos["data_pas"] = pd.to_datetime(focos["data_pas"])
    focos["ano"] = focos["data_pas"].dt.year      # usa o ano da data real
    return focos


# ─────────────────────────────────────────────
# 3. AGREGA FOCOS POR ANO E POR BIOMA
# ─────────────────────────────────────────────
def agregar_focos(focos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna duas tabelas: focos por ano e focos por ano/bioma."""
    por_ano   = focos.groupby("ano").size().reset_index(name="total_focos")
    por_bioma = focos.groupby(["ano", "bioma"]).size().reset_index(name="focos")
    return por_ano, por_bioma


# ─────────────────────────────────────────────
# 4. CARREGA E FILTRA EMISSÕES DE CO2 (MA)
# ─────────────────────────────────────────────
def carregar_co2(caminho: str, anos) -> pd.DataFrame:
    """
    Lê o arquivo de gases, filtra CO2 para municípios do Maranhão
    e retorna as emissões anuais somadas.
    """
    gases = pd.read_csv(caminho, sep=None, engine="python")

    # Filtros: apenas CO2 e apenas cidades do MA
    co2_ma = gases[
        (gases["Gás"] == "CO2 (t)") &
        (gases["Cidade"].str.contains(r"\(MA\)", na=False))
    ]

    anos_cols = [str(a) for a in anos]
    # Mantém apenas colunas de anos que existem no DataFrame
    anos_disponiveis = [c for c in anos_cols if c in co2_ma.columns]

    co2_soma = co2_ma[anos_disponiveis].sum()
    co2_df = co2_soma.reset_index()
    co2_df.columns = ["ano", "co2_toneladas"]
    co2_df["ano"] = co2_df["ano"].astype(int)
    return co2_df


# ─────────────────────────────────────────────
# 5. CORRELACIONA OS DOIS DATASETS
# ─────────────────────────────────────────────
def correlacionar(focos_ano: pd.DataFrame, co2_df: pd.DataFrame) -> pd.DataFrame:
    """
    Faz o merge entre focos e emissões de CO2 por ano.
    Calcula a métrica co2_por_foco (toneladas de CO2 por foco detectado).
    """
    tabela = focos_ano.merge(co2_df, on="ano", how="inner")
    tabela["co2_Mt"] = tabela["co2_toneladas"] / 1_000_000   # Megatoneladas
    tabela["co2_por_foco"] = (
        tabela["co2_toneladas"] / tabela["total_focos"]
    ).round(2)
    return tabela


# ─────────────────────────────────────────────
# 6. EXIBE RESULTADOS
# ─────────────────────────────────────────────
def exibir_resultados(tabela: pd.DataFrame, por_bioma: pd.DataFrame) -> None:
    print("\n" + "=" * 60)
    print("  QUEIMADAS x EMISSÕES DE CO2 — MARANHÃO (2019–2024)")
    print("=" * 60)

    print("\n📊 TABELA DE CORRELAÇÃO ANUAL")
    print("-" * 60)
    for _, row in tabela.iterrows():
        print(
            f"  {int(row['ano'])}  |  "
            f"Focos: {int(row['total_focos']):>6,}  |  "
            f"CO2: {row['co2_Mt']:>6.1f} Mt  |  "
            f"CO2/foco: {row['co2_por_foco']:>8,.0f} t"
        )
    print("-" * 60)
    print(f"  TOTAL  |  Focos: {tabela['total_focos'].sum():>6,}  |  "
          f"CO2: {tabela['co2_Mt'].sum():>6.1f} Mt")

    # Correlação de Pearson entre focos e CO2
    correlacao = tabela["total_focos"].corr(tabela["co2_toneladas"])
    print(f"\n📈 Correlação de Pearson (focos x CO2): {correlacao:.4f}")
    if abs(correlacao) >= 0.7:
        print("   → Correlação forte")
    elif abs(correlacao) >= 0.4:
        print("   → Correlação moderada")
    else:
        print("   → Correlação fraca (outros fatores influenciam as emissões)")

    print("\n🌿 FOCOS POR BIOMA")
    print("-" * 60)
    pivot = por_bioma.pivot(index="ano", columns="bioma", values="focos").fillna(0).astype(int)
    print(pivot.to_string())

    print("\n" + "=" * 60)


# ─────────────────────────────────────────────
# 7. EXPORTA PARA CSV
# ─────────────────────────────────────────────
def exportar(tabela: pd.DataFrame, por_bioma: pd.DataFrame) -> None:
    tabela.to_csv("resultado_correlacao.csv", index=False, encoding="utf-8-sig")
    por_bioma.to_csv("resultado_por_bioma.csv", index=False, encoding="utf-8-sig")
    print("\n✅ Arquivos exportados:")
    print("   • resultado_correlacao.csv")
    print("   • resultado_por_bioma.csv")


# ─────────────────────────────────────────────
# 8. EXECUÇÃO PRINCIPAL
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Carregando dados de focos de queimada...")
    focos = carregar_focos(PASTA_FOCOS, ANOS)

    print("Agregando por ano e bioma...")
    focos_ano, focos_bioma = agregar_focos(focos)

    print("Carregando emissões de CO2 do Maranhão...")
    co2_df = carregar_co2(ARQUIVO_GASES, ANOS)

    print("Correlacionando datasets...")
    tabela_final = correlacionar(focos_ano, co2_df)

    exibir_resultados(tabela_final, focos_bioma)
    exportar(tabela_final, focos_bioma)