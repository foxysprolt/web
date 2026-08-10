document.addEventListener('DOMContentLoaded', async () => {
  const parametrosURL = new URLSearchParams(window.location.search);
  const idProduto = parametrosURL.get('id');

  try {
    const resposta = await fetch('./produtos.json');
    const produtos = await resposta.json();
    const produtoEncontrado = produtos.find(item => item.id === idProduto);

    if (produtoEncontrado) {
      document.title = `${produtoEncontrado.nome} — Melin Flores`;
      document.getElementById('detalhe-imagem').src = produtoEncontrado.imagem;
      document.getElementById('detalhe-imagem').alt = produtoEncontrado.nome;
      document.getElementById('detalhe-nome').textContent = produtoEncontrado.nome;
      document.getElementById('detalhe-preco').textContent = produtoEncontrado.preco;
      document.getElementById('detalhe-descricao').textContent = produtoEncontrado.descricao;

      const mensagemWA = encodeURIComponent(`Olá! Gostaria de encomendar o produto: ${produtoEncontrado.nome} (${produtoEncontrado.preco}).`);
      document.getElementById('detalhe-link-wa').href = `https://wa.me/5511999999999?text=${mensagemWA}`;
    } else {
      document.getElementById('detalhe-nome').textContent = "Produto não encontrado";
      document.getElementById('detalhe-descricao').textContent = "O item solicitado não está disponível no catálogo.";
      document.getElementById('detalhe-preco').style.display = 'none';
      document.getElementById('detalhe-link-wa').style.display = 'none';
    }

    // Passa a lista do JSON para o mecanismo de busca do Header
    inicializarBuscaHeader(produtos);

  } catch (erro) {
    console.error('Erro ao buscar detalhes no JSON:', erro);
  }
});

function inicializarBuscaHeader(produtosBase) {
  const campoPesquisa = document.getElementById('campo-pesquisa');
  const containerDropdown = document.getElementById('catalogo-produtos');

  if (!campoPesquisa || !containerDropdown) return;

  window.filtrarProdutos = function() {
    const termo = campoPesquisa.value.toLowerCase().trim();
    containerDropdown.innerHTML = '';

    if (termo === '') return;

    const filtrados = produtosBase.filter(prod =>
      prod.nome.toLowerCase().includes(termo)
    );

    if (filtrados.length === 0) {
      containerDropdown.innerHTML = '<p style="font-size:12px; color:#888; text-align:center; padding:10px;">Nenhum produto encontrado.</p>';
      return;
    }

    filtrados.forEach(prod => {
      containerDropdown.innerHTML += `
        <div class="card-produto-mini">
          <img src="${prod.imagem}" alt="${prod.nome}">
          <div class="card-produto-info">
            <h4>${prod.nome}</h4>
            <p class="preco">${prod.preco}</p>
          </div>
          <a href="produto.html?id=${prod.id}" class="btn-pedir-mini">Ver</a>
        </div>
      `;
    });
  };

  document.addEventListener('click', function(event) {
    const searchBox = document.querySelector('.search-box');
    if (searchBox && !searchBox.contains(event.target)) {
      containerDropdown.innerHTML = '';
      campoPesquisa.value = '';
    }
  });
}