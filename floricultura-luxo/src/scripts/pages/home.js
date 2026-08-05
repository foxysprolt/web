fetch('./produtos.json')
  .then(response => {
    if (!response.ok) {
      throw new Error('Não foi possível carregar o arquivo produtos.json');
    }
    return response.json();
  })
  .then(produtos => {
    // Sua lógica de exibir produtos aqui
    console.log('Produtos carregados com sucesso:', produtos);
  })
  .catch(error => console.error('Erro:', error));