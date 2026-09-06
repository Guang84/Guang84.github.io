export function initHeader(){const h=document.querySelector(".site-header");if(!h)return;const u=()=>h.classList.toggle("is-scrolled",scrollY>10);addEventListener("scroll",u,{passive:true});u()}
