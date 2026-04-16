from __future__ import annotations

import os
import smtplib
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from time import perf_counter

import pandas as pd

from dotenv import load_dotenv
load_dotenv()

def _listar_destinatarios() -> list[str]:
	raw = os.getenv("EMAIL_TO", "")
	if not raw:
		return []

	valores = raw.replace(";", ",").split(",")
	return [v.strip() for v in valores if v.strip()]

def _carregar_representacoes(caminho_csv: str) -> tuple[bool, list[str]]:
	caminho = Path(caminho_csv)
	if not caminho.exists():
		return False, []

	df = pd.read_csv(caminho)
	if df.empty or "Documento" not in df.columns:
		return False, []

	nomes = [str(nome).strip() for nome in df["Documento"].dropna().tolist() if str(nome).strip()]
	return len(nomes) > 0, nomes


def _montar_corpo_email(tem_representacoes: bool, nomes_representacoes: list[str]) -> str:
	if not tem_representacoes:
		return (
			"Prezados,\n\n"
			"Informamos que, na consulta realizada hoje, nao foram identificadas representacoes.\n\n"
			"Atenciosamente,\n"
			"Equipe de Monitoramento"
		)

	lista_nomes = "\n".join(f"- {nome}" for nome in nomes_representacoes)
	return (
		"Prezados,\n\n"
		"Informamos que foram identificadas representacoes na consulta realizada hoje.\n"
		"Seguem abaixo os documentos localizados:\n\n"
		f"{lista_nomes}\n\n"
		"Encaminhamos em anexo o relatorio CSV e os arquivos PDF correspondentes.\n\n"
		"Atenciosamente,\n"
		"Equipe de Monitoramento"
	)


def _adicionar_anexo(msg: EmailMessage, arquivo: Path) -> None:
	conteudo = arquivo.read_bytes()
	if arquivo.suffix.lower() == ".pdf":
		maintype, subtype = "application", "pdf"
	elif arquivo.suffix.lower() == ".csv":
		maintype, subtype = "text", "csv"
	else:
		maintype, subtype = "application", "octet-stream"

	msg.add_attachment(conteudo, maintype=maintype, subtype=subtype, filename=arquivo.name)


def enviar_email_representacoes(
	caminho_csv: str = "relatorio.csv",
	pasta_pdfs: str = "downloads_pdfs",
) -> dict:
	smtp_host = os.getenv("SMTP_HOST")
	smtp_port = int(os.getenv("SMTP_PORT"))
	smtp_usuario = os.getenv("SMTP_USER")
	smtp_senha = os.getenv("SMTP_PASSWORD")
	email_remetente = os.getenv("EMAIL_FROM", smtp_usuario)
	destinatarios = _listar_destinatarios()

	tem_representacoes, nomes_representacoes = _carregar_representacoes(caminho_csv)

	msg = EmailMessage()
	msg["From"] = email_remetente
	msg["To"] = ", ".join(destinatarios)
	msg["Subject"] = f"Representacoes {date.today().strftime('%d/%m/%Y')}"
	msg.set_content(_montar_corpo_email(tem_representacoes, nomes_representacoes))

	if tem_representacoes:
		csv_path = Path(caminho_csv)
		if csv_path.exists():
			_adicionar_anexo(msg, csv_path)

		pasta = Path(pasta_pdfs)
		if pasta.exists():
			for pdf in sorted(pasta.glob("*.pdf")):
				_adicionar_anexo(msg, pdf)

	if smtp_port == 465:
		with smtplib.SMTP_SSL(smtp_host, smtp_port) as servidor:
			servidor.login(smtp_usuario, smtp_senha)
			servidor.send_message(msg)
	else:
		with smtplib.SMTP(smtp_host, smtp_port) as servidor:
			servidor.ehlo()
			servidor.starttls()
			servidor.ehlo()
			servidor.login(smtp_usuario, smtp_senha)
			servidor.send_message(msg)