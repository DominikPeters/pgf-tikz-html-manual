# [tikz.dev](https://tikz.dev) - HTML version of the PGF-TikZ documentation

This is a browsable [HTML version](https://tikz.dev) of the package documentation for [PGF/TikZ](https://github.com/pgf-tikz/pgf), whose [PDF version](https://pgf-tikz.github.io/pgf/pgfmanual.pdf) is 1300+ pages long. 
It is built using the incredibly powerful [`lwarp`](https://ctan.org/pkg/lwarp?lang=en) package by [Brian Dunn](https://bdtechconcepts.com/LaTeX-HTML-Converter-The-Lwarp-package.html).

The documentation is produced using the following steps.

1. Separately compile examples that use animation with [`dvisvgm`](https://dvisvgm.de/) in `standalone` [files](https://github.com/DominikPeters/pgf-tikz-html-manual/tree/master/doc/generic/pgf/standalone), produced by a [python script](https://github.com/DominikPeters/pgf-tikz-html-manual/blob/master/doc/generic/pgf/make-standalones.py).
2. Compile documentation using [`lwarp`](https://ctan.org/pkg/lwarp?lang=en), which also generates tikz pictures in SVG format.
3. Postprocess the resulting HTML using a [python script](https://github.com/DominikPeters/pgf-tikz-html-manual/blob/master/doc/generic/pgf/postprocessing.py) built with [`BeautifulSoup`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) for HTML parsing:
   - Highlight the current page in the side table of contents
   - Build a table of contents for the current page
   - Add visible HTML anchor links ¶
   - Add clipboard buttons
   - Annotate `<img>` tags with weight and height by parsing the SVG files
   - Add header and footer
4. Prettify the HTML files with [`prettier`](https://prettier.io/).
5. Reduce SVG file sizes with [`svgo`](https://github.com/svg/svgo).

To get `lwarp` to compile, some fixing of the macros for pretty printing was necessary and edits throughout the documentation. The end product is combined with some css and a sprinkling of javascript. Search uses Algolia's [DocSearch](https://docsearch.algolia.com/docs/legacy/run-your-own).

Project started December 2021 by [Dominik Peters](https://dominik-peters.de/).
