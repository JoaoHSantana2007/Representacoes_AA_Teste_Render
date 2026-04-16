from __future__ import annotations

import os
import base64
from datetime import date
from pathlib import Path

import pandas as pd
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


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

    nomes = [
        str(nome).strip()
        for nome in df["Documento"].dropna().tolist()
        if str(nome).strip()
    ]
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


def _arquivo_para_anexo(arquivo: Path) -> dict:
    conteudo_base64 = base64.b64encode(arquivo.read_bytes()).decode("utf-8")
    return {
        "filename": arquivo.name,
        "content": conteudo_base64,
    }


def _montar_anexos(
    caminho_csv: str,
    pasta_pdfs: str,
    tem_representacoes: bool,
) -> list[dict]:
    anexos: list[dict] = []

    if not tem_representacoes:
        return anexos

    csv_path = Path(caminho_csv)
    if csv_path.exists():
        anexos.append(_arquivo_para_anexo(csv_path))

    pasta = Path(pasta_pdfs)
    if pasta.exists():
        for pdf in sorted(pasta.glob("*.pdf")):
            anexos.append(_arquivo_para_anexo(pdf))

    return anexos


def enviar_email_representacoes(
    caminho_csv: str = "relatorio.csv",
    pasta_pdfs: str = "downloads_pdfs",
) -> dict:
    api_key = os.getenv("RESEND_API_KEY")
    email_remetente = os.getenv("EMAIL_FROM")
    destinatarios = _listar_destinatarios()

    if not api_key:
        return {"ok": False, "mensagem": "RESEND_API_KEY nao configurada."}

    if not email_remetente:
        return {"ok": False, "mensagem": "EMAIL_FROM nao configurado."}

    if not destinatarios:
        return {"ok": False, "mensagem": "EMAIL_TO nao configurado."}

    tem_representacoes, nomes_representacoes = _carregar_representacoes(caminho_csv)

    assunto = f"Representacoes {date.today().strftime('%d/%m/%Y')}"
    corpo = _montar_corpo_email(tem_representacoes, nomes_representacoes)
    anexos = _montar_anexos(caminho_csv, pasta_pdfs, tem_representacoes)

    try:
        params = {
            "from": email_remetente,
            "to": destinatarios,
            "subject": assunto,
            "text": corpo,
        }

        if anexos:
            params["attachments"] = anexos

        retorno = resend.Emails.send(params)

        return {
            "ok": True,
            "mensagem": "E-mail enviado com sucesso.",
            "retorno": retorno,
        }

    except Exception as e:
        return {
            "ok": False,
            "mensagem": f"Erro ao enviar e-mail: {type(e).__name__}: {e}",
        }

if __name__ == "__main__":
	resultado = enviar_email_representacoes()
	print(resultado)