document.addEventListener('DOMContentLoaded', () => {
  // Animação suave para links âncora internos
  const linksSuaves = document.querySelectorAll('a[href^="#"]');

  linksSuaves.forEach(link => {
    link.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;

      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
});