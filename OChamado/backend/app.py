import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
from promptia import INSTRUCAO_SISTEMA

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
app = Flask(__name__)
CORS(app)

# Conexão com a chave do seu arquivo .env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- FERRAMENTA DE APRENDIZADO TURBINADA (SISTEMA DE PONTOS) ---
def buscar_conhecimento_extra(pergunta):
    """Procura no JSON usando um sistema de pontuação por palavras-chave."""
    try:
        with open('tickets.json', 'r', encoding='utf-8') as f:
            tickets = json.load(f)
        
        pergunta_lower = pergunta.lower()
        melhor_ticket = None
        maior_pontuacao = 0
        
        for ticket in tickets:
            # Pega o problema do JSON e separa palavra por palavra
            palavras_chave = ticket["problema"].lower().split()
            
            # Conta quantas dessas palavras o usuário digitou na pergunta dele
            pontos = sum(1 for palavra in palavras_chave if palavra in pergunta_lower)
            
            # Se esse ticket teve mais acertos que o anterior, ele vira o novo favorito
            if pontos > 0 and pontos > maior_pontuacao:
                maior_pontuacao = pontos
                melhor_ticket = ticket
                
        # Se achou algum ticket vencedor, injeta a solução!
        if melhor_ticket:
            print(f">>> IA usou o ticket: {melhor_ticket['problema']} ({maior_pontuacao} pontos)")
            return f"\n\n[CONHECIMENTO TÉCNICO ENCONTRADO]: {melhor_ticket['solucao']}"
            
    except Exception as e:
        print(f"Erro ao ler banco de tickets: {e}")
    
    return ""

# --- ROTA PRINCIPAL ---
@app.route("/chat", methods=["POST"])
def chat():
    dados = request.get_json()
    historico_bruto = dados.get("historico", [])

    # 1. Identifica a última mensagem do usuário
    ultima_mensagem = ""
    if historico_bruto:
        # Pega o conteúdo da última mensagem que não seja do sistema
        ultima_mensagem = historico_bruto[-1]["content"]

    # 2. LÓGICA DE PERSONA: Identifica quem é o usuário no histórico
    conversa_str = " ".join([m["content"].lower() for m in historico_bruto])
    
    if "funcionário" in conversa_str or "funcionario" in conversa_str:
        modo_persona = "\n\n[MODO ATIVO: FUNCIONÁRIO] Use o formato técnico obrigatório: Resumo, Classificação, Ticket, Hardware e Ação."
    elif "cliente" in conversa_str:
        modo_persona = "\n\n[MODO ATIVO: CLIENTE] Ignore termos técnicos. Responda como FAQ amigável, em parágrafos simples e sem a estrutura de 'Ticket'."
    else:
        modo_persona = "\n\n[AVISO]: O usuário ainda não se identificou. Pergunte educadamente se ele é Cliente ou Funcionário antes de aprofundar."

    # 3. BUSCA CONHECIMENTO NO "BANCO DE DADOS" (RAG TURBINADO)
    conhecimento_extra = buscar_conhecimento_extra(ultima_mensagem)

    try:
        # 4. FORMATAÇÃO DA MEMÓRIA PARA O GEMINI
        mensagens_formatadas = []
        for msg in historico_bruto:
            if msg["role"] == "system":
                continue  # O sistema entra na config, não no corpo
            
            papel = "model" if msg["role"] in ["bot", "assistant"] else "user"
            mensagens_formatadas.append({
                "role": papel,
                "parts": [{"text": msg["content"]}]
            })

        # 5. MONTAGEM DA INSTRUÇÃO FINAL (Mix de tudo o que aprendemos)
        instrucao_final = INSTRUCAO_SISTEMA + modo_persona + conhecimento_extra

        # 6. CHAMADA DA IA
        resposta = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            config={"system_instruction": instrucao_final},
            contents=mensagens_formatadas
        )
        
        return jsonify({"resposta": resposta.text})

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        return jsonify({"erro": "O cérebro do Ochamado falhou. Tente novamente."}), 500

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print(">>> 🚀 OCHAMADO FULL-STACK ONLINE")
    print(">>> Memória: ATIVA | Busca Inteligente: ATIVA | Personas: ATIVA")
    app.run(debug=True, port=5000)
    