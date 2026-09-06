export function initProjects(){
  const cards=[...document.querySelectorAll('[data-project-card]')];
  const filters=document.querySelector('[data-project-filters]');
  const search=document.querySelector('[data-project-search]');
  if(!cards.length)return;
  let category='All',query='';
  const categories=['All',...new Set(cards.map(card=>card.dataset.category).filter(Boolean))];
  const render=()=>{
    const q=query.trim().toLowerCase();
    let visible=0;
    cards.forEach(card=>{
      const show=(category==='All'||card.dataset.category===category)&&(!q||(card.dataset.search||'').includes(q));
      card.hidden=!show;if(show)visible++;
    });
    let empty=document.querySelector('[data-project-empty]');
    if(!visible){if(!empty){empty=document.createElement('div');empty.className='empty-state';empty.dataset.projectEmpty='';empty.textContent='No projects match this search.';cards[0].parentElement.append(empty)}}else empty?.remove();
  };
  if(filters){
    const draw=()=>{filters.replaceChildren(...categories.map(name=>{const b=document.createElement('button');b.type='button';b.className='filter-button';b.textContent=name;b.classList.toggle('active',name===category);b.setAttribute('aria-pressed',String(name===category));b.addEventListener('click',()=>{category=name;draw();render()});return b}))};draw();
  }
  search?.addEventListener('input',()=>{query=search.value.toLowerCase();render()});
  render();
}
