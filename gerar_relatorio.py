import pandas as pd

def gerar_csv_relatorio(resumo, caminho_saida="relatorio.csv"):
	df = pd.DataFrame(resumo)

	if df.empty:
		df.to_csv(caminho_saida, index=False, encoding="utf-8")
		return

	# retira o markdown da coluna PDF
	if "PDF" in df.columns:
		df["PDF"] = df["PDF"].astype(str).str.extract(r'\((.*?)\)', expand=False).fillna(df["PDF"])

	# cria colunas auxiliares para score
	if "Match" in df.columns:
		df["_qtd"] = pd.to_numeric(df["Match"].astype(str).str.split("/").str[0], errors="coerce").fillna(0)

	if "Match Negativas" in df.columns:
		df["_qtdn"] = pd.to_numeric(df["Match Negativas"].astype(str).str.split("/").str[0], errors="coerce").fillna(0)

	df["_score"] = (
		df["_qtd"] * 2.0     # positivo pesa mais
		- df["_qtdn"] * 2.5  # negativo pesa mais ainda
	)

	# filtra por score positivo (maior chance de representacao)
	filtro = pd.to_numeric(df["_score"], errors="coerce").fillna(0) > 0

	# gera o arquivo csv 
	df[filtro].to_csv(caminho_saida, columns=["Documento", "PDF"], index=False, encoding="utf-8")