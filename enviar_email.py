from __future__ import annotations

import os
import smtplib
import socket
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from time import perf_counter, sleep

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


def _enviar_smtp(msg: EmailMessage, host: str, port: int, usuario: str, senha: str, timeout: int) -> None:
	if port == 465:
		with smtplib.SMTP_SSL(host, port, timeout=timeout) as servidor:
			servidor.login(usuario, senha)
			servidor.send_message(msg)
		return

	with smtplib.SMTP(host, port, timeout=timeout) as servidor:
		servidor.ehlo()
		servidor.starttls()
		servidor.ehlo()
		servidor.login(usuario, senha)
		servidor.send_message(msg)


def enviar_email_representacoes(
	caminho_csv: str = "relatorio.csv",
	pasta_pdfs: str = "downloads_pdfs",
) -> dict:
	inicio = perf_counter()
	smtp_host = os.getenv("SMTP_HOST")
	smtp_port = int(os.getenv("SMTP_PORT", "465"))
	smtp_usuario = os.getenv("SMTP_USER")
	smtp_senha = os.getenv("SMTP_PASSWORD")
	email_remetente = os.getenv("EMAIL_FROM", smtp_usuario)
	destinatarios = _listar_destinatarios()
	smtp_timeout = int(os.getenv("SMTP_TIMEOUT", "30"))
	smtp_max_retries = int(os.getenv("SMTP_MAX_RETRIES", "3"))

	if not smtp_host or not smtp_usuario or not smtp_senha:
		return {
			"ok": False,
			"mensagem": "Variaveis SMTP obrigatorias nao configuradas.",
			"duracao_segundos": round(perf_counter() - inicio, 2),
		}

	if not destinatarios:
		return {
			"ok": False,
			"mensagem": "Nenhum destinatario encontrado em EMAIL_TO.",
			"duracao_segundos": round(perf_counter() - inicio, 2),
		}

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

	ultimo_erro = None
	for tentativa in range(1, smtp_max_retries + 1):
		try:
			_enviar_smtp(msg, smtp_host, smtp_port, smtp_usuario, smtp_senha, smtp_timeout)
			return {
				"ok": True,
				"mensagem": f"Email enviado com sucesso na tentativa {tentativa}.",
				"duracao_segundos": round(perf_counter() - inicio, 2),
			}
		except (smtplib.SMTPException, OSError, TimeoutError, socket.gaierror) as erro:
			ultimo_erro = erro
			print(f"[SMTP] Tentativa {tentativa}/{smtp_max_retries} falhou: {type(erro).__name__}: {erro}")
			if tentativa < smtp_max_retries:
				sleep(tentativa)

	return {
		"ok": False,
		"mensagem": f"Falha ao enviar email via SMTP apos {smtp_max_retries} tentativas.",
		"erro": f"{type(ultimo_erro).__name__}: {ultimo_erro}" if ultimo_erro else "Erro nao identificado.",
		"duracao_segundos": round(perf_counter() - inicio, 2),
	}