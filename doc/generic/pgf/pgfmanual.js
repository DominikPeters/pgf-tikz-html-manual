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
    if (li.href.includes(current)) {
      li.parentElement.classList.add("current");
      li.parentElement.scrollIntoView({block: "nearest"});
    }
  });
}

function initClipboardButtons() {
  for (elem of document.getElementsByClassName("clipboardButton")) {
    elem.addEventListener("click", function (e) {
      var target = e.target;
      var copyText = target.parentElement
        .getElementsByTagName("p")[0]
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

document.addEventListener("DOMContentLoaded", (event) => {
  sections = document.querySelectorAll("h4,h5,h6");
  navLi = document.querySelectorAll("#local-toc-container a");

  window.onscroll = () => {
    debounce(updateTOC, 75)();
  };

  initClipboardButtons();
});

window.addEventListener("load", () => {
  document.querySelector("#chapter-toc-container p.current").scrollIntoView({block: "nearest"});
});