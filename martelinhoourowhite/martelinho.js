document.addEventListener('DOMContentLoaded', async () => {

  // 1. CARREGA OS SERVIÇOS DO ARQUIVO JSON
  try {
    const resposta = await fetch('servicos.json');
    const servicos = await resposta.json();

    const container = document.getElementById('grid-servicos-martelinho');
    if (container) {
      container.innerHTML = servicos.map(s => `
        <div class="card-servico-item">
          <h3>${s.nome}</h3>
          <p>${s.descricao}</p>
          <a href="#orcamento-rapido" class="btn-primary" style="text-align:center; justify-content:center;">
            Solicitar Orçamento
          </a>
        </div>
      `).join('');
    }
  } catch (erro) {
    console.error('Erro ao carregar servicos.json:', erro);
  }

  // 2. LÓGICA DE UPLOAD E PREVIEW DA FOTO
  const fileInput = document.getElementById('foto-amassado');
  const dropZone = document.getElementById('drop-zone');
  const previewContainer = document.getElementById('preview-container');
  const imgPreview = document.getElementById('img-preview');
  const btnRemove = document.getElementById('btn-remove-foto');
  const formOrcamento = document.getElementById('form-orcamento-express');
  const btnSubmit = document.getElementById('btn-submit-form');

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          imgPreview.src = event.target.result;
          previewContainer.style.display = 'flex';
          dropZone.style.display = 'none';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  if (btnRemove) {
    btnRemove.addEventListener('click', () => {
      fileInput.value = '';
      imgPreview.src = '';
      previewContainer.style.display = 'none';
      dropZone.style.display = 'block';
    });
  }

  // 3. ENVIO DO FORMULÁRIO COM ANEXO VIA EMAILJS
  if (formOrcamento) {
    formOrcamento.addEventListener('submit', async (e) => {
      e.preventDefault();

      btnSubmit.disabled = true;
      btnSubmit.innerHTML = "Enviando orçamento... <i class='bx bx-loader-alt bx-spin'></i>";

      const nome = document.getElementById('nome-cliente').value.trim();
      const carro = document.getElementById('modelo-carro').value.trim();
      const peca = document.getElementById('peca-amassada').value;
      const tipo = document.getElementById('tipo-amassado').value;
      const obs = document.getElementById('observacoes').value.trim();

      const templateParams = {
        cliente_nome: nome,
        cliente_carro: carro,
        peca_atingida: peca,
        tipo_dano: tipo,
        observacoes: obs || "Nenhuma observação informada.",
      };

      // Converte imagem para Base64 se o usuário anexou arquivo
      if (fileInput.files.length > 0) {
        try {
          const base64Image = await convertBase64(fileInput.files[0]);
          templateParams.foto_anexo = base64Image;
        } catch (err) {
          console.error("Erro ao processar imagem:", err);
        }
      }

      // Substitua com seus IDs reais do painel do EmailJS
      emailjs.send("SEU_SERVICE_ID", "SEU_TEMPLATE_ID", templateParams)
        .then(() => {
          alert("Orçamento e foto enviados com sucesso! A oficina entrará em contato em breve.");
          formOrcamento.reset();
          if (btnRemove) btnRemove.click();
        })
        .catch((error) => {
          console.error("Erro ao enviar e-mail:", error);
          alert("Ocorreu um erro ao enviar o formulário. Tente novamente.");
        })
        .finally(() => {
          btnSubmit.disabled = false;
          btnSubmit.innerHTML = "Enviar Orçamento com Foto por E-mail <i class='bx bx-paper-plane'></i>";
        });
    });
  }
});

// Converter imagem para Base64
function convertBase64(file) {
  return new Promise((resolve, reject) => {
    const fileReader = new FileReader();
    fileReader.readAsDataURL(file);
    fileReader.onload = () => resolve(fileReader.result);
    fileReader.onerror = (error) => reject(error);
  });
}