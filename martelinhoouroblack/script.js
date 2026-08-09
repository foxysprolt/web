document.addEventListener('DOMContentLoaded', async () => {
  try {
    const resposta = await fetch('servicos.json');
    const servicos = await resposta.json();

    const automotivos = servicos.filter(s => s.categoria === 'automotivo');
    const residenciais = servicos.filter(s => s.categoria === 'residencial');

    renderizarCards(automotivos, 'grid-servicos-automotivos');
    renderizarCards(residenciais, 'grid-servicos-residenciais');
  } catch (erro) {
    console.error('Erro ao carregar o catálogo de serviços:', erro);
  }
});

function renderizarCards(lista, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = lista.map(item => `
    <div class="card-servico-box">
      <img src="${item.imagem}" alt="${item.nome}" onerror="this.src='https://images.unsplash.com/photo-1520340356584-f9917d1eea6f?auto=format&fit=crop&w=600&q=80'">
      <div class="card-servico-conteudo">
        <h3>${item.nome}</h3>
        <p>${item.descricao}</p>
        <a href="https://wa.me/5511999999999?text=Olá!%20Gostaria%20de%20agendar%20o%20serviço:%20${encodeURIComponent(item.nome)}" target="_blank" class="btn-primary full">
          Agendar Serviço
        </a>
      </div>
    </div>
  `).join('');
}