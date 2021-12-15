
function debounce(func, timeout = 300){
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => { func.apply(this, args); }, timeout);
  };
}

function updateTOC() {
  var current = "NOTHING";

  sections.forEach((section) => {
    const sectionTop = section.offsetTop;
    if (scrollY >= sectionTop - 60) {
      current = section.getAttribute("id");
    }
  });

  navLi.forEach((li) => {
    li.classList.remove("current");
    if (li.href.includes(current)) {
      li.classList.add("current");
    }
  });
}

document.addEventListener('DOMContentLoaded', (event) => {
  sections = document.querySelectorAll("h4,h5,h6");
  navLi = document.querySelectorAll("#local-toc-container a");

  window.onscroll = () => {
    debounce(updateTOC,75)();
  };
});

