document.addEventListener('DOMContentLoaded',function(){
 const toggle=document.querySelector('.mobile-nav-toggle'),menu=document.querySelector('#global-navigation');
 if(toggle&&menu){toggle.addEventListener('click',function(){const open=menu.classList.toggle('is-open');toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',open?'Đóng menu':'Mở menu');});}
 if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches&&'IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');observer.unobserve(entry.target);}})},{threshold:.08});
  document.querySelectorAll('.reveal').forEach(el=>observer.observe(el));
 }else{document.querySelectorAll('.reveal').forEach(el=>el.classList.add('is-visible'));}
});
