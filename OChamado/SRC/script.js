import { promptia } from './artificialinteligenc/promptia.js'

let botao = document.querySelector(".botao-ajuda")
let input = document.querySelector(".caixa-texto")
let chat = document.querySelector("#chat")

// Endereço do seu "Garçom" Python no Render
let urlServidor = "https://ochamadochat.onrender.com/chat"

let historico = [
    {
        role: "system",
        content: promptia
    },
    {
        role: "assistant",
        content: "Olá! Antes de começarmos, você é um Cliente ou um Funcionário da Power2Go?"
    }
    // ❌ Removi a palavra "web" que estava sobrando aqui e quebrando o código
];

window.onload = () => {
    adicionarMensagem("Olá! Antes de começarmos, você é um Cliente ou um Funcionário da Power2Go?", "bot");
};

// 1. FUNÇÃO QUE CRIA OS BALÕES NA TELA
function adicionarMensagem(texto, tipo) {
    let div = document.createElement("div")
    div.classList.add("msg", tipo)
    // Substitui quebras de linha por <br> para o HTML entender
    div.innerHTML = texto.replace(/\n/g, "<br>")
    chat.appendChild(div)
    
    // Faz o chat rolar para baixo automaticamente
    chat.scrollTop = chat.scrollHeight
}

// 2. FUNÇÃO QUE FAZ A LIGAÇÃO PARA O PYTHON
async function enviarMensagem() {
    let texto = input.value.trim()
    if (!texto) return

    // Adiciona sua mensagem na tela
    adicionarMensagem(texto, "user")
    historico.push({ role: "user", content: texto }); 
    
    input.value = ""

    // Adiciona o balão de carregamento
    adicionarMensagem("Ochamado: analisando...", "bot")

    try {
        let resposta = await fetch(urlServidor, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ historico: historico }) 
        })

        if (!resposta.ok) {
            throw new Error("Erro no servidor: " + resposta.status)
        }

        let dados = await resposta.json()
        
        // Remove o balão de "analisando..."
        if (chat.lastChild) chat.lastChild.remove();

        let resultado = dados.resposta 
        adicionarMensagem(resultado, "bot")
        historico.push({ role: "assistant", content: resultado });

    } catch (erro) {
        if (chat.lastChild) chat.lastChild.remove();
        adicionarMensagem("Erro: Falha na comunicação com o cérebro.", "bot");
        console.error("Erro detalhado:", erro);
    }
}

// 3. GATILHOS
botao.addEventListener("click", enviarMensagem)

input.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        enviarMensagem()
    }
})