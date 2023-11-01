let sections;
let navLi;

function debounce(func, timeout = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
}

function updateTOC() {
  var current = "NOTHING";

  sections.forEach((section) => {
    const sectionTop = section.offsetTop;
    if (scrollY >= sectionTop - 122) {
      current = section.getAttribute("id");
    }
  });

  navLi.forEach((li) => {
    li.parentElement.classList.remove("current");
    if (li.href.endsWith(current)) {
      li.parentElement.classList.add("current");
      li.parentElement.scrollIntoView({ block: "nearest" });
    }
  });
}

function initClipboardButtons() {
  for (elem of document.getElementsByClassName("clipboardButton")) {
    elem.addEventListener("click", function (e) {
      var target = e.target;
      var copyText = target.parentElement
        .getElementsByTagName("code")[0]
        .innerText.trim();
      navigator.clipboard.writeText(copyText).then(
        function () {
          target.innerHTML = "&#x2713;";
          setTimeout(() => {
            target.innerHTML = "copy";
          }, 2000);
        },
        function (err) {
          target.innerHTML = "Error";
          setTimeout(() => {
            target.innerHTML = "Copy";
          }, 2000);
        }
      );
    });
  }
}

function makeAnchorButtons() {
  const pdfManualURL = "https://pgf-tikz.github.io/pgf/pgfmanual.pdf";
  document.querySelectorAll('a.anchor-link').forEach((element) => {
    const links = [];

    if (element.dataset.pdfDestination) {
      // Create the PDF link element
      const pdfLink = document.createElement('a');
      pdfLink.href = `${pdfManualURL}#nameddest=${element.dataset.pdfDestination}`;
      pdfLink.className = 'anchor-pdf-link';
      pdfLink.setAttribute('aria-label', 'Link to this section in PDF version');
      pdfLink.title = `Open PDF (page ${element.dataset.pdfPage})`;
      pdfLink.style.marginLeft = 'auto';
      pdfLink.target = '_blank';
      pdfLink.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-file-pdf" viewBox="0 0 16 16"><path d="M4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H4zm0 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z"/><path d="M4.603 12.087a.81.81 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645 19.701 19.701 0 0 0 1.062-2.227 7.269 7.269 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.187-.012.395-.047.614-.084.51-.27 1.134-.52 1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 1.334.05c.364.065.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.716 5.716 0 0 1-.911-.95 11.642 11.642 0 0 0-1.997.406 11.311 11.311 0 0 1-1.021 1.51c-.29.35-.608.655-.926.787a.793.793 0 0 1-.58.029zm1.379-1.901c-.166.076-.32.156-.459.238-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361.01.022.02.036.026.044a.27.27 0 0 0 .035-.012c.137-.056.355-.235.635-.572a8.18 8.18 0 0 0 .45-.606zm1.64-1.33a12.647 12.647 0 0 1 1.01-.193 11.666 11.666 0 0 1-.51-.858 20.741 20.741 0 0 1-.5 1.05zm2.446.45c.15.162.296.3.435.41.24.19.407.253.498.256a.107.107 0 0 0 .07-.015.307.307 0 0 0 .094-.125.436.436 0 0 0 .059-.2.095.095 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a3.881 3.881 0 0 0-.612-.053zM8.078 5.8a6.7 6.7 0 0 0 .2-.828c.031-.188.043-.343.038-.465a.613.613 0 0 0-.032-.198.517.517 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822.024.111.054.227.09.346z"/></svg>';
      links.push(pdfLink);
    }

    if (element.dataset.htmlLink) {
      // Create the HTML link element
      const htmlLink = document.createElement('a');
      htmlLink.href = `#${element.dataset.htmlLink}`;
      htmlLink.className = 'anchor-html-link';
      htmlLink.setAttribute('aria-label', 'Permalink to this section in HTML version');
      htmlLink.title = 'Share link';
      htmlLink.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-link" viewBox="0 0 16 16"><path d="M 10.5,15 C 10.223858,15 10,14.776142 10,14.5 V 2 H 9 v 12.5 c 0,0.666666 -1,0.666666 -1,0 L 7.9351199,7.077646 H 7.0029165 C 2.9055303,7.077646 2.7647133,1 7,1 h 5.5 c 0.666666,0 0.666666,1 0,1 H 11 v 12.5 c 0,0.276142 -0.223858,0.5 -0.5,0.5 z"/></svg>';
      if (!element.dataset.pdfDestination) {
        htmlLink.style.marginLeft = 'auto';
      }
      links.push(htmlLink);
    }

    element.replaceWith(...links);
  });
}

function italicizeKinTikZnames() {
  for (elem of document.getElementsByClassName("tikzname")) {
    elem.innerHTML = "Ti<i>k</i>Z";
  }
}

document.addEventListener("DOMContentLoaded", (event) => {
  sections = document.querySelectorAll("span.sectionnumber");
  navLi = document.querySelectorAll("#local-toc-container a");

  window.onscroll = () => {
    debounce(updateTOC, 75)();
    const pgfplots = document.getElementById("pgfplots-link");
    if (pgfplots) {
      pgfplots.style.display = scrollY == 0 ? "block" : "none";
    }
  };

  const hamburger = document.getElementById("hamburger-button");
  const chapterMenu = document.getElementById("chapter-toc-container");
  function toggleMenu() {
    if (chapterMenu.classList.contains("show-menu")) {
      chapterMenu.classList.remove("show-menu");
    } else {
      chapterMenu.classList.add("show-menu");
    }
  }
  hamburger.addEventListener("click", toggleMenu);

  initClipboardButtons();

  makeAnchorButtons();

  italicizeKinTikZnames();

  /*! instant.page v5.1.0 - (C) 2019-2020 Alexandre Dieulot - https://instant.page/license */
  let t,e;const n=new Set,o=document.createElement("link"),i=o.relList&&o.relList.supports&&o.relList.supports("prefetch")&&window.IntersectionObserver&&"isIntersecting"in IntersectionObserverEntry.prototype,s="instantAllowQueryString"in document.body.dataset,a="instantAllowExternalLinks"in document.body.dataset,r="instantWhitelist"in document.body.dataset,c="instantMousedownShortcut"in document.body.dataset,d=1111;let l=65,u=!1,f=!1,m=!1;if("instantIntensity"in document.body.dataset){const t=document.body.dataset.instantIntensity;if("mousedown"==t.substr(0,"mousedown".length))u=!0,"mousedown-only"==t&&(f=!0);else if("viewport"==t.substr(0,"viewport".length))navigator.connection&&(navigator.connection.saveData||navigator.connection.effectiveType&&navigator.connection.effectiveType.includes("2g"))||("viewport"==t?document.documentElement.clientWidth*document.documentElement.clientHeight<45e4&&(m=!0):"viewport-all"==t&&(m=!0));else{const e=parseInt(t);isNaN(e)||(l=e)}}if(i){const n={capture:!0,passive:!0};if(f||document.addEventListener("touchstart",function(t){e=performance.now();const n=t.target.closest("a");if(!h(n))return;v(n.href)},n),u?c||document.addEventListener("mousedown",function(t){const e=t.target.closest("a");if(!h(e))return;v(e.href)},n):document.addEventListener("mouseover",function(n){if(performance.now()-e<d)return;const o=n.target.closest("a");if(!h(o))return;o.addEventListener("mouseout",p,{passive:!0}),t=setTimeout(()=>{v(o.href),t=void 0},l)},n),c&&document.addEventListener("mousedown",function(t){if(performance.now()-e<d)return;const n=t.target.closest("a");if(t.which>1||t.metaKey||t.ctrlKey)return;if(!n)return;n.addEventListener("click",function(t){1337!=t.detail&&t.preventDefault()},{capture:!0,passive:!1,once:!0});const o=new MouseEvent("click",{view:window,bubbles:!0,cancelable:!1,detail:1337});n.dispatchEvent(o)},n),m){let t;(t=window.requestIdleCallback?t=>{requestIdleCallback(t,{timeout:1500})}:t=>{t()})(()=>{const t=new IntersectionObserver(e=>{e.forEach(e=>{if(e.isIntersecting){const n=e.target;t.unobserve(n),v(n.href)}})});document.querySelectorAll("a").forEach(e=>{h(e)&&t.observe(e)})})}}function p(e){e.relatedTarget&&e.target.closest("a")==e.relatedTarget.closest("a")||t&&(clearTimeout(t),t=void 0)}function h(t){if(t&&t.href&&(!r||"instant"in t.dataset)&&(a||t.origin==location.origin||"instant"in t.dataset)&&["http:","https:"].includes(t.protocol)&&("http:"!=t.protocol||"https:"!=location.protocol)&&(s||!t.search||"instant"in t.dataset)&&!(t.hash&&t.pathname+t.search==location.pathname+location.search||"noInstant"in t.dataset))return!0}function v(t){if(n.has(t))return;const e=document.createElement("link");e.rel="prefetch",e.href=t,document.head.appendChild(e),n.add(t)}
});

window.addEventListener("load", () => {
  document
    .querySelector("#chapter-toc-container p.current")
    .scrollIntoView({ block: "nearest" });
  updateTOC();
});
