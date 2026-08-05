/* ==========================================
   ESTILOS DA SEÇÃO DE CATÁLOGO COMPLETO
   ========================================== */
.secao-catalogo {
  max-width: 1200px;
  margin: 60px auto;
  padding: 0 20px;
}

.titulo-catalogo {
  text-align: center;
  margin-bottom: 40px;
}

.titulo-catalogo h2 {
  font-size: 28px;
  color: #333333;
  margin-bottom: 8px;
}

.titulo-catalogo p {
  font-size: 16px;
  color: #777777;
}

/* Grid dinâmico que reaproveita o estilo das suas .box */
.grid-catalogo-produtos {
  display: grid;
  grid-template-columns: repeat(1, 1fr); /* 1 produto por linha no celular */
  gap: 25px;
}

/* Ajustes para tablet e computador */
@media (min-width: 600px) {
  .grid-catalogo-produtos {
    grid-template-columns: repeat(2, 1fr); /* 2 por linha em telas médias */
  }
}

@media (min-width: 992px) {
  .grid-catalogo-produtos {
    grid-template-columns: repeat(4, 1fr); /* 4 por linha no PC */
  }
}