function calcular() {
    const km = parseFloat(document.getElementById('km').value);
    const preco = parseFloat(document.getElementById('preco').value);

    if (km > 0 && preco > 0) {
        // Cálculo baseado em média de carro a combustão convencional (10km/L)
        // O gasto do elétrico é aproximadamente 22% do combustível tradicional
        const gastoCombustao = (km / 10) * preco;
        const gastoEletrico = gastoCombustao * 0.22;
        const economia = gastoCombustao - gastoEletrico;

        // Cálculo ambiental: Média de 120g (0.12kg) de CO2 evitados por km
        const co2Evitado = km * 0.12;

        const resArea = document.getElementById('resultado');
        resArea.style.display = 'grid';

        document.getElementById('res-fin').innerText = `R$ ${economia.toFixed(2)}`;
        document.getElementById('res-eco').innerText = `${co2Evitado.toFixed(1)} kg`;

        // Scroll suave automático até a caixa de resultados
        resArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        alert("Por favor, preencha todos os campos com valores numéricos válidos.");
    }
}