import { promptia } from './artificialinteligenc/promptia.js'
let botao = document.querySelector(".botao-ajuda")
let input = document.querySelector(".caixa-texto")
let chat = document.querySelector("#chat")

let chave = "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"
let endereco = "https://api.groq.com/openai/v1/chat/completions"

let historico = [
    {
        role: "system",
        content: promptia
    }
]

// VERIFICA SE ELEMENTOS EXISTEM
if (!botao || !input || !chat) {
    console.error("Erro: elementos não encontrados no HTML")
}

// CRIA MENSAGEM
function adicionarMensagem(texto, tipo) {
    let div = document.createElement("div")
    div.classList.add("msg", tipo)
    div.innerHTML = texto.replace(/\n/g, "<br>")
    chat.appendChild(div)
    chat.scrollTop = chat.scrollHeight
}

async function enviarMensagem() {
    let texto = input.value.trim()
    if (!texto) return

    adicionarMensagem(texto, "user")

    historico.push({
        role: "user",
        content: texto
    })

    input.value = ""

    adicionarMensagem("Ochamado: analisando...", "bot")

    try {
        let resposta = await fetch(endereco, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${chave}`
            },
            body: JSON.stringify({
                model: "llama-3.3-70b-versatile", // 🔥 modelo mais estável
                messages: historico
            })
        })

        console.log("STATUS:", resposta.status)

        if (!resposta.ok) {
            throw new Error("Erro HTTP: " + resposta.status)
        }

        let dados = await resposta.json()
        console.log("RESPOSTA:", dados)

        chat.lastChild.remove()

        if (!dados.choices || !dados.choices[0]) {
            adicionarMensagem("Erro: IA não respondeu corretamente.", "bot")
            return
        }

        let resultado = dados.choices[0].message.content

        adicionarMensagem(resultado, "bot")

        historico.push({
            role: "assistant",
            content: resultado,

        })


    } catch (erro) {
        chat.lastChild.remove()
        adicionarMensagem("Erro ao chamar IA. Veja o console.", "bot")
        console.error("ERRO COMPLETO:", erro)
    }
}

// EVENTOS
botao.addEventListener("click", enviarMensagem)

input.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        enviarMensagem()
    }
})
