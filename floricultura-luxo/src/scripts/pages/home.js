async function carregarProdutosHome() {
  try {
    const resposta = await fetch('./produtos.json');
    const produtos = await resposta.json();

    // 1. Filtra os produtos por categoria e status
    const bestSellers = produtos.filter(p => p.bestseller === true);
    const buques = produtos.filter(p => p.categoria === 'buques');
    const presentes = produtos.filter(p => p.categoria === 'presentes');

    // 2. Renderiza nas respectivas divs do HTML
    renderizarGaleria(bestSellers, 'galeria-bestsellers');
    renderizarGaleria(buques, 'galeria-buques');
    renderizarGaleria(presentes, 'galeria-presentes');

  } catch (erro) {
    console.error('Erro ao carregar o catálogo JSON na Home:', erro);
  }
}

function renderizarGaleria(lista, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = lista.map(prod => `
    <div class="box">
      <img src="${prod.imagem}" alt="${prod.nome}">
      <h3>${prod.nome}</h3>
      <h2>${prod.preco}</h2>
      <a href="produto.html?id=${prod.id}" style="text-decoration:none;">
        <button style="background-color: #d4af37;">Ver detalhes</button>
      </a>
    </div>
  `).join('');
}

function rolarCarrossel(idGaleria, direcao) {
  const container = document.getElementById(idGaleria);
  if (!container) return;
  
  container.scrollBy({
    left: direcao,
    behavior: 'smooth'
  });
}

document.addEventListener('DOMContentLoaded', carregarProdutosHome);