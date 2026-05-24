import os
import re
import json
import logging
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import functions_framework
from flask import jsonify
from google import genai
from google.genai import types
import promptia

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Constantes ─────────────────────────────────────────────────────────────────
AWS_API_BASE = "https://8akkoikdg5.execute-api.us-east-2.amazonaws.com/Prod/charge_info/"
MODEL_NAME   = "gemini-flash-latest"

# ESP: 12 chars alfanuméricos com pelo menos 2 dígitos
ESP_PATTERN = re.compile(r'\b(?=[A-Z0-9]*[0-9][A-Z0-9]*[0-9])[A-Z0-9]{12}\b')

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


# ── Helpers ────────────────────────────────────────────────────────────────────

def extrair_valor_linha(lista_linhas, chave_busca):
    if not lista_linhas:
        return None
    chave_lower = chave_busca.lower()
    for linha in lista_linhas:
        if chave_lower in linha.lower():
            try:
                partes = linha.split(":", 1)
                if len(partes) > 1:
                    return float(partes[1].strip())
            except (ValueError, IndexError):
                logger.warning("Nao foi possivel converter valor da linha: %s", linha)
    return None


def consultar_dados_reais_aws(esp_id):
    url_completa = f"{AWS_API_BASE}{esp_id}"
    try:
        requisicao = urllib.request.Request(
            url_completa, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(requisicao, timeout=10) as response:
            resposta_bruta = response.read().decode("utf-8")
            dados_json = json.loads(resposta_bruta)

        mensagem_interna = dados_json.get("message", "")
        if "Nao foi possivel" in mensagem_interna or not mensagem_interna:
            return {"status_conexao": "OFFLINE"}

        linhas_aws = mensagem_interna.split("<br>")
        return {
            "status_conexao":  "ONLINE",
            "voltageInst":     extrair_valor_linha(linhas_aws, "voltageInst"),
            "voltageInst2":    extrair_valor_linha(linhas_aws, "voltageInst2"),
            "voltageInst3":    extrair_valor_linha(linhas_aws, "voltageInst3"),
            "currentInst":     extrair_valor_linha(linhas_aws, "currentInst"),
            "currentInst2":    extrair_valor_linha(linhas_aws, "currentInst2"),
            "currentInst3":    extrair_valor_linha(linhas_aws, "currentInst3"),
            "powerInst":       extrair_valor_linha(linhas_aws, "powerInst"),
            "energyAcc":       extrair_valor_linha(linhas_aws, "energyAcc"),
            "pLow":            extrair_valor_linha(linhas_aws, "plow"),
            "pHigh":           extrair_valor_linha(linhas_aws, "phigh"),
            "pState":          extrair_valor_linha(linhas_aws, "pState"),
            "evState":         extrair_valor_linha(linhas_aws, "evState"),
            "evseState":       extrair_valor_linha(linhas_aws, "evseState"),
            "breakerState":    extrair_valor_linha(linhas_aws, "breakerState"),
            "maxCurrent":      extrair_valor_linha(linhas_aws, "maxCurrent"),
        }
    except urllib.error.URLError as exc:
        logger.error("Erro de rede ao consultar AWS (%s): %s", esp_id, exc)
        return {"status_conexao": "OFFLINE"}
    except Exception as exc:
        logger.error("Erro inesperado ao consultar AWS (%s): %s", esp_id, exc)
        return {"status_conexao": "OFFLINE"}


def enviar_email_via_gmail(conteudo_ticket, assunto_dinamico):
    remetente    = os.getenv("GMAIL_USER")
    senha_app    = os.getenv("GMAIL_APP_PASS")
    destinatario = "suporte@power2go.com.br"

    if not remetente or not senha_app:
        logger.error("Credenciais GMAIL_USER / GMAIL_APP_PASS nao configuradas.")
        return False

    senha_limpa = senha_app.replace(" ", "").strip()

    try:
        msg = MIMEMultipart()
        msg["From"]    = remetente
        msg["To"]      = destinatario
        msg["Subject"] = assunto_dinamico
        msg.attach(MIMEText(conteudo_ticket, "plain", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(remetente, senha_limpa)
            server.sendmail(remetente, destinatario, msg.as_string())

        logger.info("E-mail enviado com sucesso para %s", destinatario)
        return True

    except smtplib.SMTPAuthenticationError as exc:
        logger.error("Falha de autenticacao SMTP: %s", exc)
    except smtplib.SMTPException as exc:
        logger.error("Erro SMTP ao enviar e-mail: %s", exc)
    except Exception as exc:
        logger.error("Erro inesperado ao enviar e-mail: %s", exc)

    return False


def extrair_assunto_ticket(ticket_texto, esp_id, eh_funcionario):
    for l_ticket in ticket_texto.split("\n"):
        if "NOME DO LOCAL" in l_ticket.upper():
            partes = l_ticket.split(":", 1)
            if len(partes) > 1:
                valor = partes[1].strip()
                if valor and "[" not in valor:
                    return valor
    if eh_funcionario and esp_id:
        return f"[CHAMADO TECNICO] ESP {esp_id}"
    return "[CHAMADO CLIENTE] Suporte Power2Go"


def montar_historico_gemini(historico_bruto):
    historico = []
    for msg in historico_bruto:
        role_correta = "model" if msg.get("role") in ["bot", "model", "assistant"] else "user"
        historico.append(
            types.Content(
                role=role_correta,
                parts=[types.Part.from_text(text=msg.get("content", ""))]
            )
        )
    return historico


def disparar_email(resposta_texto, esp_detectado, eh_funcionario):
    """Extrai assunto e envia o e-mail. Retorna (resposta_limpa, enviado)."""
    resposta_limpa = resposta_texto.replace("[DISPARAR_EMAIL]", "").strip()
    assunto_final  = extrair_assunto_ticket(resposta_limpa, esp_detectado, eh_funcionario)
    enviado        = enviar_email_via_gmail(resposta_limpa, assunto_final)
    return resposta_limpa, enviado


# ── Entry-point ────────────────────────────────────────────────────────────────

@functions_framework.http
def chat_ochamado(request):
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        return ("", 204, headers)

    headers = {"Access-Control-Allow-Origin": "*"}

    try:
        dados = request.get_json(silent=True)
        if not dados or "historico" not in dados:
            return (jsonify({"erro": "Historico ausente"}), 400, headers)

        historico_bruto = dados.get("historico", [])
        if not historico_bruto:
            return (jsonify({"erro": "Historico vazio"}), 400, headers)

        ultima_msg          = historico_bruto[-1].get("content", "")
        texto_usuario_upper = ultima_msg.upper()
        conversa_upper      = " ".join(m.get("content", "").upper() for m in historico_bruto)

        eh_funcionario = "FUNCIONÁRIO" in conversa_upper or "FUNCIONARIO" in conversa_upper

        # ── Gatilho certo: pedido explícito (Python decide) ────────────────────
        pediu_chamado = any(t in texto_usuario_upper for t in [
            "ABRIR", "CHAMADO", "TICKET", "ABRE", "SUPORTE", "ENVIAR"
        ])

        # ── Detecção do ESP ────────────────────────────────────────────────────
        esp_detectado = None
        match = ESP_PATTERN.search(conversa_upper)
        if match:
            esp_detectado = match.group(0)

        # ── Telemetria AWS (só funcionários) ───────────────────────────────────
        dados_reais_aws = ""
        if esp_detectado and eh_funcionario:
            telemetria = consultar_dados_reais_aws(esp_detectado)
            dados_reais_aws = (
                f"\n\n[DADOS REAIS DA AWS PARA O ESP {esp_detectado}]:\n"
                f"{json.dumps(telemetria, indent=2, ensure_ascii=False)}\n"
            )

        # ── Gatilho certo: pedido explícito → Python força o ticket ───────────
        if pediu_chamado:
            logger.info("Gatilho Python ativado: pedido explicito de chamado.")

            if eh_funcionario:
                instrucao_ticket = (
                    f"{dados_reais_aws}\n[COMANDO CRITICO]: Abertura de chamado autorizada. "
                    "Preencha o '[MODELO TICKET: FUNCIONARIO]' com os dados tecnicos da AWS. "
                    "Nao use negrito. Retorne APENAS o bloco do ticket."
                )
            else:
                instrucao_ticket = (
                    "[COMANDO CRITICO]: Abertura de chamado autorizada. "
                    "Preencha o '[MODELO TICKET: CLIENTE]' com o Nome, Local/Condominio e LEDs informados. "
                    "Nao use negrito. Retorne APENAS o bloco do ticket."
                )

            historico_para_ticket = montar_historico_gemini(historico_bruto[:-1])
            historico_para_ticket.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=instrucao_ticket)]
                )
            )

            config_ticket = types.GenerateContentConfig(
                system_instruction=promptia.INSTRUCAO_SISTEMA,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
            )
            completion_ticket = client.models.generate_content(
                model=MODEL_NAME,
                contents=historico_para_ticket,
                config=config_ticket,
            )
            ticket_preenchido = completion_ticket.text
            assunto_final     = extrair_assunto_ticket(ticket_preenchido, esp_detectado, eh_funcionario)
            email_enviado     = enviar_email_via_gmail(ticket_preenchido, assunto_final)

            if email_enviado:
                if eh_funcionario:
                    resposta = (
                        f"Chamado tecnico para o ESP {esp_detectado} enviado com sucesso.\n\n"
                        f"Assunto: {assunto_final}\n\n{ticket_preenchido}"
                    )
                else:
                    resposta = (
                        "Entendido! Acabei de gerar e enviar o seu chamado de suporte "
                        "para a nossa equipe tecnica.\n\n"
                        f"Assunto: {assunto_final}\n\n"
                        f"Um especialista foi acionado. Aqui esta a copia:\n\n{ticket_preenchido}"
                    )
            else:
                resposta = (
                    "Chamado gerado, mas houve uma falha no envio (SMTP). "
                    f"Segue o texto para registro manual:\n\n{ticket_preenchido}"
                )

            return (jsonify({"resposta": resposta}), 200, headers)

        # ── Gatilho ambíguo: Gemini decide via [DISPARAR_EMAIL] ───────────────
        historico_gemini = montar_historico_gemini(historico_bruto)

        instrucao_com_gatilho = (
            promptia.INSTRUCAO_SISTEMA + dados_reais_aws +
            "\n\n[INSTRUCAO CRITICA DO SISTEMA]: Se o usuario relatar que o procedimento "
            "nao funcionou ou que o problema persiste (mesmo sem usar essas palavras exatas), "
            "e voce ja tiver coletado Nome, Local/Condominio e estado dos LEDs, "
            "gere o modelo de ticket padrao e inclua EXATAMENTE o termo [DISPARAR_EMAIL] "
            "sem negrito, sem espacos extras, no final da sua resposta. "
            "Se for um Funcionario pedindo abertura, faca o mesmo."
        )

        config_conversa = types.GenerateContentConfig(
            system_instruction=instrucao_com_gatilho,
            temperature=0.4,
            thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
        )
        completion = client.models.generate_content(
            model=MODEL_NAME,
            contents=historico_gemini,
            config=config_conversa,
        )
        resposta_final = completion.text

        # ── Intercepta tag do Gemini ───────────────────────────────────────────
        if "[DISPARAR_EMAIL]" in resposta_final:
            logger.info("Gatilho Gemini reconhecido: [DISPARAR_EMAIL] detectado.")
            resposta_limpa, email_enviado = disparar_email(
                resposta_final, esp_detectado, eh_funcionario
            )
            if email_enviado:
                logger.info("E-mail disparado com sucesso via gatilho Gemini.")
                return (jsonify({"resposta": resposta_limpa}), 200, headers)
            else:
                logger.error("Gatilho Gemini ativado mas SMTP falhou.")
                resposta_com_aviso = (
                    resposta_limpa +
                    "\n\n*(Nota: O chamado foi gerado mas houve uma instabilidade no servidor de e-mail.)*"
                )
                return (jsonify({"resposta": resposta_com_aviso}), 200, headers)

        # Conversa normal
        return (jsonify({"resposta": resposta_final}), 200, headers)

    except Exception as exc:
        logger.exception("Erro interno nao tratado")
        return (jsonify({"erro": f"Erro interno: {str(exc)}"}), 500, headers)