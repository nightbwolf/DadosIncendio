"""
main.py
-------
Ponto de entrada do projeto. Orquestra a análise e as visualizações.

Estrutura esperada do projeto:
    DADOSINCENDIO/
    ├  ├── queimadasMA/        ← CSVs de focos (focos_br_ma_ref_XXXX.csv)
    │  └── MA/gases.csv
    ├── analise_queimadas_co2.py
    ├── visualizacoes.py
    └── main.py                 ← você está aqui
"""

from analise_queimadas_co2 import (
    carregar_focos,
    agregar_focos,
    carregar_co2,
    correlacionar,
)
import visualizacoes as viz

# ─────────────────────────────────────────────
# CONFIGURAÇÃO — ajuste os caminhos se precisar
# ─────────────────────────────────────────────
PASTA_FOCOS   = "queimadasMA"
ARQUIVO_GASES = "MA/gases.csv"
ANOS          = range(2019, 2025)

# Controla o comportamento das visualizações
viz.SALVAR  = False   # não salva PNG
viz.MOSTRAR = True    # abre janela interativa


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  ANÁLISE: QUEIMADAS x CO2 — MARANHÃO")
    print("=" * 50)

    # 1. Carrega e processa os dados
    print("\n[1/4] Carregando focos de queimada...")
    focos = carregar_focos(PASTA_FOCOS, ANOS)

    print("[2/4] Agregando por ano e bioma...")
    focos_ano, focos_bioma = agregar_focos(focos)

    print("[3/4] Carregando emissões de CO2...")
    co2_df = carregar_co2(ARQUIVO_GASES, ANOS)

    print("[4/4] Correlacionando datasets...")
    tabela = correlacionar(focos_ano, co2_df)

    # 2. Exibe tabela no terminal
    print("\n── Tabela de resultados ──")
    viz.imprimir_tabela(tabela)

    # 3. Gera visualizações
    print("── Gerando gráficos ──")

    print("  Histograma mensal...")
    viz.plotar_histograma_mensal(focos)

    print("  Linha de CO2...")
    viz.plotar_linha_co2(tabela)

    print("  Barras por bioma...")
    viz.plotar_barras_bioma(focos_bioma)

    print("\nConcluído!")


if __name__ == "__main__":
    main()
