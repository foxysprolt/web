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


document.addEventListener('DOMContentLoaded', () => {
  let ultimoScroll = 0;
  
  // Seleciona o elemento da logo
  const logo = document.querySelector('.logo') || document.querySelector('.top-bar-logo') || document.querySelector('header img');

  if (!logo) return;

  window.addEventListener('scroll', () => {
    if (window.innerWidth <= 768) {
      const scrollAtual = window.pageYOffset || document.documentElement.scrollTop;

      // Se estiver bem no topo da página, mantém a logo visível
      if (scrollAtual <= 15) {
        logo.classList.remove('logo-escondida');
        return;
      }

      // Cria uma margem de tolerância (só aciona se rolar mais de 8px)
      if (Math.abs(scrollAtual - ultimoScroll) < 8) return;

      // Roolou pra baixo -> Esconde a logo de forma fluida
      if (scrollAtual > ultimoScroll && scrollAtual > 40) {
        logo.classList.add('logo-escondida');
      } 
      ultimoScroll = scrollAtual;
    } else {
      logo.classList.remove('logo-escondida');
    }
  }, { passive: true }); // passive: true melhora a taxa de FPS e fluidez do scroll no celular
});