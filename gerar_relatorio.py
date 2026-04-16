import pandas as pd

def gerar_csv_relatorio(resumo, caminho_saida="relatorio.csv"):
	df = pd.DataFrame(resumo)

	if df.empty:
		df.to_csv(caminho_saida, index=False, encoding="utf-8")
		return

	# retira o markdown da coluna PDF
	if "PDF" in df.columns:
		df["PDF"] = df["PDF"].astype(str).str.extract(r'\((.*?)\)', expand=False).fillna(df["PDF"])

	# filtra por score positivo (maior chance de representacao)
	filtro = pd.to_numeric(df["Score"], errors="coerce").fillna(0) > 0

	# gera o arquivo csv 
	df[filtro].to_csv(caminho_saida, columns=["Documento", "PDF"], index=False, encoding="utf-8")