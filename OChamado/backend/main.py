import os
import functions_framework
from flask import jsonify
from groq import Groq
import promptia  # Importa o seu arquivo de instruções técnicas

# Inicializa o cliente Groq usando a chave de ambiente
# Certifique-se de que a variável GROQ_API_KEY esteja configurada no seu provedor de nuvem
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@functions_framework.http
def chat_ochamado(request):
    # --- TRATAMENTO DE CORS (Necessário para requisições do App/Web) ---
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}

    try:
        # 1. Recebe os dados da requisição
        dados = request.get_json()
        if not dados or 'historico' not in dados:
            return (jsonify({"erro": "O historico de mensagens e obrigatorio."}), 400, headers)

        historico_bruto = dados.get("historico", [])
        
        # 2. Lógica de Identificação de Persona (Filtro Binário)
        # Analisamos o histórico para saber se o usuário se identificou como funcionário
        conversa_completa = " ".join([m["content"].lower() for m in historico_bruto])
        
        if "funcionário" in conversa_completa or "funcionario" in conversa_completa:
            # Se for funcionário da casa, ativa o modo técnico seco
            modo_persona = "\n\n[INSTRUCAO ADICIONAL: MODO FUNCIONARIO POWER2GO ATIVO. Use tom tecnico, sem emojis e exija dados de EVSE e Firmware.]"
        else:
            # Para todos os outros (clientes, supervisores de hotel, etc), tom amigável
            modo_persona = "\n\n[INSTRUCAO ADICIONAL: MODO CLIENTE ATIVO. Use tom amigavel, emojis, e foque no reset do disjuntor DR e identificacao por cores.]"

        # 3. Montagem das Mensagens para o Groq (Llama 3.3)
        # O Groq segue o padrão: System (instruções) -> User/Assistant (conversa)
        mensagens_groq = [
            {
                "role": "system", 
                "content": promptia.INSTRUCAO_SISTEMA + modo_persona
            }
        ]
        
        for msg in historico_bruto:
            # Converte os nomes de 'role' para o padrão que o Groq aceita
            papel = "assistant" if msg["role"] in ["bot", "model", "assistant"] else "user"
            mensagens_groq.append({"role": papel, "content": msg["content"]})

        # 4. Chamada ao motor Llama 3.3 70B (Velocidade e Precisão)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensagens_groq,
            temperature=0.6, # Temperatura levemente baixa para manter a precisão técnica
            max_tokens=1024,
            top_p=1,
            stream=False
        )

        # 5. Captura a resposta gerada
        resposta_texto = completion.choices[0].message.content
        
        return (jsonify({"resposta": resposta_texto}), 200, headers)

    except Exception as e:
        # Log de erro para depuração no console do Google Cloud
        print(f"ERRO NO OCHAMADO: {str(e)}")
        return (jsonify({"erro": "Erro interno no processamento da mensagem."}), 500, headers)