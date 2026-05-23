import os
import json
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import functions_framework
from flask import jsonify
from groq import Groq
import promptia

AWS_API_BASE = "https://8akkoikdg5.execute-api.us-east-2.amazonaws.com/Prod/charge_info/"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extrair_valor_linha(linhas, chave):
    for linha in linhas:
        if chave in linha:
            try:
                partes = linha.split(":")
                if len(partes) > 1:
                    return float(partes[1].strip())
            except:
                pass
    return None

def consultar_dados_reais_aws(esp_id):
    try:
        url_completa = f"{AWS_API_BASE}{esp_id}"
        requisicao = urllib.request.Request(url_completa, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(requisicao, timeout=10) as response:
            resposta_bruta = response.read().decode('utf-8')
            dados_json = json.loads(resposta_bruta)
            
        mensagem_interna = dados_json.get("message", "")
        if "Nao foi possivel" in mensagem_interna or not mensagem_interna:
            return {"status_conexao": "OFFLINE"}
            
        linhas = mensagem_interna.split("<br>")
        return {
            "status_conexao": "ONLINE",
            "voltageInst": extrair_valor_linha(linhas, "voltageInst"),
            "voltageInst2": extrair_valor_linha(linhas, "voltageInst2"),
            "voltageInst3": extrair_valor_linha(linhas, "voltageInst3"),
            "currentInst": extrair_valor_linha(linhas, "currentInst"),
            "currentInst2": extrair_valor_linha(linhas, "currentInst2"),
            "currentInst3": extrair_valor_linha(linhas, "currentInst3"),
            "powerInst": extrair_valor_linha(linhas, "powerInst"),
            "energyAcc": extrair_valor_linha(linhas, "energyAcc"),
            "pLow": extrair_valor_linha(linhas, "plow"),
            "pHigh": extrair_valor_linha(linhas, "phigh"),
            "pState": extrair_valor_linha(linhas, "pState"),
            "evState": extrair_valor_linha(linhas, "evState"),
            "evseState": extrair_valor_linha(linhas, "evseState"),
            "breakerState": extrair_valor_linha(linhas, "breakerState"),
            "maxCurrent": extrair_valor_linha(linhas, "maxCurrent")
        }
    except:
        return {"status_conexao": "OFFLINE"}

def enviar_email_via_gmail(conteudo_ticket, assunto_dinamico):
    try:
        remetente = os.getenv("GMAIL_USER")       
        senha_app = os.getenv("GMAIL_APP_PASS")   
        destinatario = "suporte@power2go.com.br"  
        
        if not remetente or not senha_app:
            return False

        senha_limpa = senha_app.replace(" ", "").strip()

        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto_dinamico
        msg.attach(MIMEText(conteudo_ticket, 'plain', 'utf-8'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(remetente, senha_limpa)
        server.sendmail(remetente, destinatario, msg.as_string())
        server.quit()
        return True
    except:
        return False

@functions_framework.http
def chat_ochamado(request):
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        dados = request.get_json()
        if not dados or 'historico' not in dados:
            return (jsonify({"erro": "Historico ausente"}), 400, headers)

        historico_bruto = dados.get("historico", [])
        ultima_msg = historico_bruto[-1]["content"] if historico_bruto else ""
        texto_usuario_upper = ultima_msg.upper()
        
        conversa_completa_upper = " ".join([m["content"].upper() for m in historico_bruto])
        
        eh_funcionario = "FUNCIONÁRIO" in conversa_completa_upper or "FUNCIONARIO" in conversa_completa_upper
        
        quer_abrir_chamado = any(termo in texto_usuario_upper for termo in ["ABRIR CHAMADO", "ABRIR TICKET", "ENVIAR EMAIL", "GERAR CHAMADO"])

        esp_detectado = None
        palavras = conversa_completa_upper.replace("?", "").replace(".", "").replace(",", "").split()
        for palavra in palavras:
            if len(palavra) == 12 and any(c.isdigit() for c in palavra):
                esp_detectado = palavra
                break

        dados_reais_aws = ""
        telemetria = None
        if esp_detectado and eh_funcionario:
            telemetria = consultar_dados_reais_aws(esp_detectado)
            if telemetria:
                dados_reais_aws = f"\n\n[DADOS REAIS DA AWS PARA O ESP {esp_detectado}]:\n{json.dumps(telemetria, indent=2)}\n"

        # --- FLUXO DE DISPARO DE TICKET AUTOMÁTICO ---
        if quer_abrir_chamado:
            comando_ticket = f"{dados_reais_aws}\n[COMANDO CRÍTICO]: O usuário solicitou o ticket. "
            if eh_funcionario:
                comando_ticket += "Preencha estritamente o '[MODELO TICKET: FUNCIONÁRIO]' com os dados da AWS, a localização/proprietário informada e as ações relatadas. Não use negritos. Retorne APENAS o bloco do ticket."
            else:
                comando_ticket += "Preencha estritamente o '[MODELO TICKET: CLIENTE]' usando as informações coletadas do cliente (Nome, Telefone, Localização/Proprietário, LEDs). Não use negritos. Retorne APENAS o bloco do ticket."

            mensagens_groq = [{"role": "system", "content": promptia.INSTRUCAO_SISTEMA + comando_ticket}]
            completion_ticket = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=mensagens_groq,
                temperature=0.1
            )
            ticket_preenchido = completion_ticket.choices[0].message.content
            
            # --- CAPTURA DINÂMICA DO ASSUNTO (PARA AMBOS OS FLUXOS) ---
            assunto_final = ""
            linhas_ticket = ticket_preenchido.split("\n")
            
            for linha in linhas_ticket:
                if "NOME DO LOCAL / CLIENTE PROPRIETÁRIO:" in linha.upper():
                    assunto_final = linha.split(":")[-1].strip()
                    break
            
            # Fallback caso dê algum erro na captura da linha
            if not assunto_final or assunto_final == "" or "[" in assunto_final:
                assunto_final = f"[CHAMADO TÉCNICO] ESP {esp_detectado}" if eh_funcionario else "[CHAMADO CLIENTE] Novo Registro"

            email_enviado = enviar_email_via_gmail(ticket_preenchido, assunto_final)
            
            if email_enviado:
                if eh_funcionario:
                    resposta = f"Entendi, parceiro! O chamado técnico para o ESP {esp_detectado} foi enviado com sucesso.\n\nAssunto gerado: **{assunto_final}**\n\nCópia do Ticket:\n\n{ticket_preenchido}"
                else:
                    resposta = f"Registrei o seu relato e um especialista irá analisar o seu caso e entrar em contato. Caso seja algo urgente, você também pode ligar para o nosso suporte no número (11) 92009-9822.\n\n*(Interno: Chamado enviado com o assunto '{assunto_final}'!)*"
            else:
                resposta = f"Montei a estrutura do chamado, mas houve um problema SMTP. Segue o texto para envio manual para o email suporte@power2go.com.br ou ligar para o nosso suporte no número (11) 92009-9822:\n\n{ticket_preenchido}"
                
            return (jsonify({"resposta": resposta}), 200, headers)

        # --- FLUXO DE CONVERSA REGULAR ---
        instrucao_final = promptia.INSTRUCAO_SISTEMA + dados_reais_aws
        mensagens_groq = [{"role": "system", "content": instrucao_final}]
        
        for msg in historico_bruto:
            papel = "assistant" if msg["role"] in ["bot", "model", "assistant"] else "user"
            mensagens_groq.append({"role": papel, "content": msg["content"]})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensagens_groq,
            temperature=0.3,
            max_tokens=1024
        )

        resposta_final = completion.choices[0].message.content
        return (jsonify({"resposta": resposta_final}), 200, headers)

    except Exception as e:
        return (jsonify({"erro": f"Erro interno: {str(e)}"}), 500, headers)