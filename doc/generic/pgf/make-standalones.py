import os
import subprocess
import time
import sys

DELETE_TOKEN = "\%\% PYTHON DELETE LINE\n"

HEADER = r"""
\documentclass{standalone}
\def\pgfsysdriver{pgfsys-dvisvgm.def}
\usepackage{tikz}
\usetikzlibrary{animations,views}

\begin{document}
"""

SEAGULLHEADER = r"""
\documentclass{standalone}
\def\pgfsysdriver{pgfsys-dvisvgm.def}
\usepackage{tikz}
\usetikzlibrary{animations,views}
\tikzset{
  seagull/.pic={
    % Code for a "seagull". Do you see it?...
    \draw (-3mm,0) to [bend left] (0,0) to [bend left] (3mm,0);
  }
}
\begin{document}
"""

PGFHEADER = r"""
\documentclass{standalone}
\def\pgfsysdriver{pgfsys-dvisvgm.def}
\usepackage{tikz}
\usetikzlibrary{animations,views}

\makeatletter

\def\animationexample#1#2#3{%
  \tikz[fill=blue!25, draw=blue, ultra thick] {
    \pgfidrefnextuse{\objid}{#1}
    \pgfsysanimkeywhom{\objid}{#2}
    \pgfidrefnextuse{\nodeid}{node}
    \pgfsysanimkeyevent{\nodeid}{}{click}{}{begin}
    #3
    \node [font=\footnotesize, circle, fill, draw, align=center]
      (node) {Click \\ here};
  }%
}

\def\animationcanvasexample#1#2{%
  \animationexample{ball}{}{%
    \pgfsysanimkeycanvastransform{#1}{#2}%
    \pgfsysanimkeytime{0}{1}{1}{0}{0}
    \pgfsysanimvaltranslate{0cm}{0cm}%
    \pgfsysanimkeytime{2}{1}{1}{0}{0}
    \pgfsysanimvaltranslate{1cm}{0cm}%
    \pgfsysanimate{translate}
    \fill [ball color=red,name=ball] (1,0) circle [radius=3mm]; }
  \animationexample{ball}{}{%
    \pgfsysanimkeycanvastransform{#1}{#2}%
    \pgfsysanimkeytime{0}{1}{1}{0}{0}
    \pgfsysanimvalscalar{0}%
    \pgfsysanimkeytime{2}{1}{1}{0}{0}
    \pgfsysanimvalscalar{90}%
    \pgfsysanimate{rotate}
    \fill [ball color=blue,name=ball] (1,0) circle [radius=3mm]; } }

\begin{document}
"""

END = r"""
\end{document}
"""

images = []

# iterate through all .tex files in directory
for filename in os.listdir('.'):
    if not filename.endswith('.tex') or "macros" in filename:
        continue
    image_no = 1
    base_filename = filename.split('.')[0]
    # open file
    with open(filename, 'r') as f:
        # read file
        lines = f.readlines()
    made_changes = False
    for i, line in enumerate(lines):
        if "\\begin{codeexample}" in line:
            is_animation = False
            precode = False
            codeexample_start = i
            # find next line with \end{codeexample}
            for j, line2 in enumerate(lines[i:]):
                if "\\end{codeexample}" in line2:
                    codeexample_end = j + i
                    break
            # find line with "]"
            for j, line2 in enumerate(lines[i:]):
                if "pre=" in line2:
                    precode = True
                if "animation list" in line2:
                    is_animation = True
                if "]" in line2:
                    options_end = j + i
                    break
            if not is_animation:
                continue
            if precode:
                print("Precode detected in " + filename)
            # found animation codeblock
            made_changes = True
            image_filename = f"{base_filename}-animation-{image_no}"
            lines[codeexample_start] = f"\\begin{{codeexample}}[imagesource={{standalone/{image_filename}.svg}}]\n"
            for j in range(codeexample_start + 1, options_end + 1):
                lines[j] = DELETE_TOKEN
            example_code = lines[options_end + 1:codeexample_end]
            lines[codeexample_end] = "\\end{codeexample}\n"
            # write examplecode to file
            with open("standalone/"+image_filename+".tex", 'w') as f:
                if "pgfsys" in filename:
                    f.write(PGFHEADER)
                elif any("seagull" in line for line in example_code):
                    f.write(SEAGULLHEADER)
                else:
                    f.write(HEADER)
                if example_code[-1] == '\n':
                    example_code = example_code[:-1]
                for line in example_code:
                    f.write(line)
                f.write(END)
            images.append(image_filename)
            image_no += 1
    if made_changes:
        print("Made changes to", filename)
        with open("standalone/"+filename, 'w') as f:
            for line in lines:
                if line != DELETE_TOKEN:
                    f.write(line)

print("Compiling")
images.append("pgfmanual-en-tikz-pics-animation-1")
for image in images:
    subprocess.run(["lualatex", "--output-format=dvi", "-interaction=batchmode", "-output-directory", "standalone/dvi", "standalone/"+image+".tex"])
    subprocess.run(["dvisvgm", "standalone/dvi/"+image+".dvi", "-o", "standalone/"+image+".svg"])