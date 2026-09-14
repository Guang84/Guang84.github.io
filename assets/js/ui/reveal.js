const SELECTOR = '.section,.archive-intro,.project-card,.writing-item,.important-link-card,.interest-card,.detail-section,.content-hero';

export function initReveal() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;
  const nodes = [...document.querySelectorAll(SELECTOR)];
  nodes.forEach((node, index) => {
    node.classList.add('reveal-ready');
    node.style.setProperty('--reveal-delay', `${Math.min(index % 5, 4) * 45}ms`);
  });
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-revealed');
      observer.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  nodes.forEach((node) => observer.observe(node));
}
