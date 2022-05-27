from unicodedata import name
from xml.dom import minidom
from bs4 import BeautifulSoup, Comment
from shutil import copyfile, copytree
import json
import re
import os
import datetime
import subprocess

def kilobytes(filename):
    st = os.stat(filename)
    return st.st_size / 1000

# mkdir processed
os.makedirs("processed", exist_ok=True)
copyfile("style.css", "processed/style.css")
copyfile("lwarp.css", "processed/lwarp.css")
copyfile("pgfmanual.js", "processed/pgfmanual.js")
copyfile("lwarp-mathjax-emulation.js", "processed/lwarp-mathjax-emulation.js")
copytree("pgfmanual-images", "processed/pgfmanual-images", dirs_exist_ok=True)
copytree("standalone", "processed/standalone", dirs_exist_ok=True)
copytree("banners/social-media-banners", "processed/social-media-banners", dirs_exist_ok=True)
copytree("banners/toc-banners", "processed/toc-banners", dirs_exist_ok=True)

meta_descriptions = json.load(open("meta-descriptions.json"))

## table of contents and anchor links
def rearrange_heading_anchors(soup):
    heading_tags = ["h4", "h5", "h6"]
    for tag in soup.find_all(heading_tags):
        # add paragraph links
        if tag.name in ["h5", "h6"]:
            for entry in tag.children:
                if "class" in entry.attrs and "sectionnumber" in entry["class"]:
                    anchor = "sec-" + entry.text.strip().split("\u2003")[0]
                    entry["id"] = anchor
                    link = soup.new_tag('a', href=f"#{anchor}")
                    link['class'] = 'anchor-link'
                    link.append("¶")
                    tag.append(link)
                    break
        # find human-readable link target and re-arrange anchor
        for sibling in tag.next_siblings:
            if sibling.name is None:
                continue
            if sibling.name == 'a' and 'id' in sibling.attrs:
                # potential link target
                if 'pgfmanual-auto' in sibling['id']:
                    continue
                # print(f"Human ID: {tag['id']} -> {sibling['id']}")
                # found a human-readable link target
                a_tag = sibling.extract()
                tag.insert(0, a_tag)
                break
            else:
                break

def add_copyright_comment_block(filename, soup):
    # open tex file to fetch copyright block (initial lines starting in %)
    stem = os.path.splitext(filename)[0]
    tex_filename = f"pgfmanual-en-{stem}.tex"
    copyright_lines = []
    if os.path.isfile(tex_filename):
        with open(tex_filename, "r") as file:
            for line in file:
                if line.startswith("%"):
                    copyright_lines.append(line[1:].strip())
                else:
                    break
    if not copyright_lines:
        copyright_lines = [
            "Copyright 2019 by Till Tantau",
            "",
            "This file may be distributed and/or modified",
            "",
            "1. under the LaTeX Project Public License and/or",
            "2. under the GNU Free Documentation License.",
            "",
            "See the file doc/generic/pgf/licenses/LICENSE for more details."
        ]
    # add copyright block to html
    comment = Comment("\n".join(copyright_lines).replace("the file doc/generic/pgf/licenses/LICENSE","https://tikz.dev/license"))
    soup.html.insert(0, comment)

def make_page_toc(soup):
    container = soup.find(class_="bodyandsidetoc")
    toc_container = soup.new_tag('div')
    # toc_container['class'] = 'page-toc-container'
    toc_container['class'] = 'sidetoccontainer'
    toc_container['id'] = 'local-toc-container'
    toc_nav = soup.new_tag('nav')
    toc_nav['class'] = 'sidetoc'
    toc_container.append(toc_nav)
    toctitle = soup.new_tag('div')
    toctitle['class'] = 'sidetoctitle'
    toctitle_text = soup.new_tag('p')
    toctitle_text.append("On this page")
    toctitle.append(toctitle_text)
    toc_nav.append(toctitle)
    toc = soup.new_tag('div')
    toc['class'] = 'sidetoccontents'
    toc_nav.append(toc)
    heading_tags = ["h5", "h6"]
    for tag in soup.find_all(heading_tags):
        anchor = tag.find(class_="sectionnumber").get('id')
        item = soup.new_tag('p')
        # a = soup.new_tag('a', href=f"#{tag.get('id')}")
        a = soup.new_tag('a', href=f"#{anchor}")
        a.string = tag.text.strip().split("\u2003")[1].replace("¶", "")
        if tag.name == "h5":
            a['class'] = 'tocsubsection'
        elif tag.name == "h6":
            a['class'] = 'tocsubsubsection'
        item.append(a)
        toc.append(item)
        pass
    container.insert(0,toc_container)

def add_class(tag, c):
    if 'class' in tag.attrs:
        tag['class'].append(c)
    else:
        tag['class'] = [c]

def _add_mobile_toc(soup):
    "on part overview pages, add a list of sections for mobile users"
    mobile_toc = soup.new_tag('div')
    mobile_toc['class'] = 'mobile-toc'
    mobile_toc_title = soup.new_tag('strong')
    mobile_toc_title.string = "Sections"
    mobile_toc.append(mobile_toc_title)
    mobile_toc_list = soup.new_tag('ul')
    mobile_toc.append(mobile_toc_list)
    # get toc contents
    toc_container = soup.find(class_="sidetoccontainer")
    toc_items = toc_container.find_all('a', class_="tocsection")
    for item in toc_items:
        li = soup.new_tag('li')
        a = soup.new_tag('a', href=item.get('href'))
        a.string = item.text
        li.append(a)
        mobile_toc_list.append(li)
    # add toc to section class="textbody", after the h2
    textbody = soup.find(class_="textbody")
    h2_index = textbody.contents.index(soup.h2)
    textbody.insert(h2_index+1, mobile_toc)

## shorten sidetoc
def shorten_sidetoc_and_add_part_header(soup, is_home=False):
    container = soup.find(class_="sidetoccontainer")
    container['id'] = "chapter-toc-container"
    sidetoc = soup.find(class_="sidetoccontents")
    if soup.h4 is None:
        my_file_id = soup.h2['id']    
        is_a_section = False
    else:
        my_file_id = soup.h4['id']
        is_a_section = True
    toc = []
    last_part = None
    my_part = None
    for entry in sidetoc.children:
        if entry.name != 'p':
            continue
        # Skip home link
        # if entry.a['href'] == "index.html":
        #     continue
        if "linkhome" in entry.a['class']:
            entry.a.decompose()
            continue
        if len(entry.a['href'].split('#')) < 2:
            print(f"WARNING: {entry.a['href']}")
        filename = entry.a['href'].split('#')[0]
        file_id = entry.a['href'].split('#')[1]
        entry.a['href'] = filename.replace(".html", "") # get rid of autosec in toc, not needed
        # get rid of sectionnumber
        new_a = soup.new_tag('a', href=entry.a['href'])
        new_a['class'] = entry.a['class']
        contents = entry.a.contents[2:]
        contents[0] = contents[0][1:] # delete tab
        if contents[-1] == ' Zeichenprogramm':
            contents = contents[:2] + ['Z']
        new_a.extend(contents)
        entry.a.replace_with(new_a)
        # Skip introduction link because it doesn't have a part
        if entry.a['href'] == "index-0":
            entry.a['class'] = ['linkintro']
            if is_home:
                entry['class'] = ['current']
            continue
        if "tocpart" in entry.a['class']:
            element = {
                "tag": entry,
                "file_id": file_id,
                "children": []
            }
            last_part = element
            toc.append(element)
            if file_id == my_file_id:
                assert 'class' not in entry
                entry['class'] = ["current"]
                soup.title.string = entry.a.get_text() + " - PGF/TikZ Manual"
                my_part = element
        elif "tocsection" in entry.a['class']:
            element = {
                "tag": entry,
                "file_id": file_id,
            }
            if last_part:
                last_part['children'].append(element)
            if file_id == my_file_id:
                assert 'class' not in entry
                entry['class'] = ["current"]
                soup.title.string = entry.a.get_text() + " - PGF/TikZ Manual"
                my_part = last_part
        else:
            print(f"unknown class: {entry.a['class']}")
    for part in toc:
        if part != my_part:
            for section in part['children']:
                section['tag'].decompose()
        else:
            add_class(part['tag'], "current-part")
            for section in part['children']:
                add_class(section['tag'], "current-part")
            if is_a_section:
                h2 = soup.new_tag('h2')
                h2['class'] = ['inserted']
                # contents = part['tag'].a.contents[1:]
                # h2.append(contents[1].replace("\u2003", ""))
                part_name = part['tag'].a.get_text()
                assert part_name is not None
                h2.append(part_name)
                soup.h1.insert_after(h2)
    if not is_a_section and not is_home:
        # this is a part overview page
        # let's insert an additional local table of contents for mobile users
        _add_mobile_toc(soup)

## make anchor tags to definitions
def get_entryheadline_p(tag):
    for child in tag.find_all(name="p"):
        if child.name is not None:
            if child.name == 'p':
                return child
    return None
def get_entryheadline_a(p_tag):
    for child in p_tag.children:
        if child.name is not None:
            if child.name == 'a':
                return child
    return None
def make_entryheadline_anchor_links(soup):
    for tag in soup.find_all(class_="entryheadline"):
        p_tag = get_entryheadline_p(tag)
        if p_tag is None:
            continue
        a_tag = get_entryheadline_a(p_tag)
        if a_tag is None:
            continue
        anchor = a_tag.get('id')
        if "pgf" not in anchor:
            continue
        link = soup.new_tag('a', href=f"#{anchor}")
        link['class'] = 'anchor-link'
        link.append("¶")
        p_tag.append(link)

## write to file
def write_to_file(soup, filename):
    with open(filename, "w") as file:
        html = soup.encode(formatter="html5").decode("utf-8")
        html = html.replace("index-0","/")
        lines = html.splitlines()
        new_lines = []
        for line in lines:
            # count number of spaces at the start of line
            spaces_at_start = len(re.match(r"^\s*", line).group(0))
            line = line.strip()
            # replace multiple spaces by a single space
            line = re.sub(' +', ' ', line)
            # restore indentation
            line = " " * spaces_at_start + line
            new_lines.append(line)
        html = "\n".join(new_lines)
        file.write(html)

def remove_mathjax_if_possible(filename, soup):
    with open(filename, "r") as file:
        content = file.read()
        if content.count("\(") == 61:
            # mathjax isn't actually used
            soup.find(class_="hidden").decompose()
            # remove element with id "MathJax-script"
            soup.find(id="MathJax-script").decompose()
            # go through all script tags and remove the ones that contain the word "emulation"
            for tag in soup.find_all('script'):
                if "Lwarp MathJax emulation code" in tag.string:
                    tag.decompose()
                    break
        else:
            soup.find(id="MathJax-script").attrs['async'] = None
            # externalize emulation code
            for tag in soup.find_all('script'):
                # print(tag.string)
                if tag.string is not None and "Lwarp MathJax emulation code" in tag.string:
                    tag.decompose()
                    script = soup.new_tag('script', src="lwarp-mathjax-emulation.js")
                    script.attrs['async'] = None
                    soup.head.append(script)
                    break

def remove_html_from_links(filename, soup):
    for tag in soup.find_all("a"):
        if 'href' in tag.attrs:
            if tag['href'] == "index.html" or tag['href'] == "index":
                tag['href'] = "/"
            tag['href'] = tag['href'].replace('.html', '')
            if filename == "index.html":
                if "#" in tag['href']:
                    tag['href'] = tag['href'].split('#')[0]

def remove_useless_elements(soup):
    # soup.find("h1").decompose()
    soup.find(class_="topnavigation").decompose()
    soup.find(class_="botnavigation").decompose()

def addClipboardButtons(soup):
    for example in soup.find_all(class_="example-code"):
        button = soup.new_tag('button', type="button")
        button['class'] = "clipboardButton"
        button.string = "copy"
        example.insert(0,button)

def add_header(soup):
    header = soup.new_tag('header')

    hamburger = soup.new_tag('div')
    hamburger['id'] = "hamburger-button"
    hamburger.string = "☰"
    header.append(hamburger)

    h1 = soup.new_tag('strong')
    link = soup.new_tag('a', href="/")
    h1.append(link)
    link.append("PGF/")
    k = soup.new_tag("span")
    k['class'] = "tikzname"
    k.append("TikZ")
    link.append(k)
    link.append(" Manual")
    header.append(h1)
    soup.find(class_="bodyandsidetoc").insert(0, header)

    # Docsearch 2
    # search_input = soup.new_tag('input', type="search", placeholder="Search..")
    # search_input['class'] = "search-input"
    # header.append(search_input)

    # link = soup.new_tag('link', rel="stylesheet", href="https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/docsearch.min.css")
    # soup.head.append(link)

    # script = soup.new_tag('script', src="https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/docsearch.min.js")
    # soup.body.append(script)
    # script = soup.new_tag('script')
    # script.append("""
    #   docsearch({
    #     apiKey: 'ae66ec3fc9df4b52b4d6f24fc8508fd3',
    #     indexName: 'tikz.dev',
    #     appId: 'Q70NNMA9GC',
    #     inputSelector: '.search-input',
    #     // Set debug to true to inspect the dropdown
    #     debug: false,
    # });
    # """)
    # soup.body.append(script)

    # Docsearch 3
    search_input = soup.new_tag('div', id="search")
    header.append(search_input)

    link = soup.new_tag('link', rel="stylesheet", href="https://unpkg.com/@docsearch/css@alpha")
    soup.head.append(link)

    script = soup.new_tag('script', src="https://cdn.jsdelivr.net/npm/@docsearch/js@alpha")
    soup.body.append(script)
    script = soup.new_tag('script')
    script.append("""
      docsearch({
        apiKey: 'ae66ec3fc9df4b52b4d6f24fc8508fd3',
        indexName: 'tikz.dev',
        appId: 'Q70NNMA9GC',
        container: '#search',
    });
    """)
    soup.body.append(script)

def favicon(soup):
    link = soup.new_tag('link', rel="icon", type="image/png", sizes="16x16", href="/favicon-16x16.png")
    soup.head.append(link)
    link = soup.new_tag('link', rel="icon", type="image/png", sizes="32x32", href="/favicon-32x32.png")
    soup.head.append(link)
    link = soup.new_tag('link', rel="apple-touch-icon", type="image/png", sizes="180x180", href="/apple-touch-icon.png")
    soup.head.append(link)
    link = soup.new_tag('link', rel="manifest", href="/site.webmanifest")
    soup.head.append(link)

def add_footer(soup):
    footer = soup.new_tag('footer')
    footer_left = soup.new_tag('div')
    footer_left['class'] = "footer-left"
    # Link to github
    link = soup.new_tag('a', href="https://github.com/pgf-tikz/pgf")
    link.string = "Github"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link to license
    link = soup.new_tag('a', href="/license")
    link.string = "License"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link to CTAN
    link = soup.new_tag('a', href="https://ctan.org/pkg/pgf")
    link.string = "CTAN"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link to PDF version
    link = soup.new_tag('a', href="https://pgf-tikz.github.io/pgf/pgfmanual.pdf")
    link.string = "PDF version"
    footer_left.append(link)
    footer_left.append(" · ")
    # Issue tracker
    link = soup.new_tag('a', href="https://github.com/DominikPeters/tikz.dev-issues/issues")
    link.string = "Feedback and issues"
    footer_left.append(link)
    footer_left.append(" · ")
    # Link to About the HTML version
    link = soup.new_tag('a', href="https://github.com/DominikPeters/pgf-tikz-html-manual")
    link.string = "About this HTML version"
    footer_left.append(link)
    #
    footer.append(footer_left)
    footer_right = soup.new_tag('div')
    footer_right['class'] = "footer-right"
    today = datetime.date.today().isoformat()
    em = soup.new_tag('em')
    em.append("Manual last updated: " + today)
    footer_right.append(em)
    footer.append(footer_right)
    soup.find(class_="bodyandsidetoc").append(footer)

def _add_dimensions(tag, svgfilename):
    with open(svgfilename, "r") as svgfile:
        svg = minidom.parse(svgfile)
        width_pt = svg.documentElement.getAttribute("width").replace("pt", "")
        height_pt = svg.documentElement.getAttribute("height").replace("pt", "")
    width_px = float(width_pt) * 1.33333
    height_px = float(height_pt) * 1.33333
    tag['width'] = "{:.3f}".format(width_px)
    tag['height'] = "{:.3f}".format(height_px)
    return (width_px, height_px)

def process_images(soup):
    for tag in soup.find_all("img"):
        if "svg" in tag['src']: 
            width_px, height_px = _add_dimensions(tag, tag['src'])
            # very large SVGs are pathological and empty, delete them
            if height_px > 10000:
                tag.decompose()
                continue
            tag["loading"] = "lazy"
            # replace all SVGs by PNGs except if that's a big filesize penalty
            # doing this because the SVGs are missing some features like shadows
            png_filename = tag['src'].replace("svg", "png")
            if kilobytes(png_filename) < 5 * kilobytes(tag['src']):
                tag['src'] = png_filename
    for tag in soup.find_all("object"):
        if "svg" in tag['data']: 
            _add_dimensions(tag, tag['data'])

def rewrite_svg_links(soup):
    for tag in soup.find_all("a"):
        if tag.has_attr('href') and "svg" in tag['href']:
            img = tag.img
            if img and "inlineimage" in img['class']:
                object = soup.new_tag('object')
                object['data'] = img['src']
                object['type'] = "image/svg+xml"
                tag.replace_with(object)

def add_version_to_css_js(soup):
    "to avoid caching, add a version number to the URL"
    today = datetime.date.today().isoformat().replace("-", "")
    for tag in soup.find_all("link"):
        if tag.has_attr('href') and tag['href'] == "style.css":
            tag['href'] += "?v=" + today
    for tag in soup.find_all("script"):
        if tag.has_attr('src') and tag['src'] == "pgfmanual.js":
            tag['src'] += "?v=" + today

def semantic_tags(soup):
    for example in soup.find_all(class_="example"):
        example.name = "figure"
    for examplecode in soup.find_all(class_="example-code"):
        p = examplecode.find("p")
        p.name = "code"

def add_meta_tags(filename, soup):
    stem = os.path.splitext(filename)[0]
    # title
    if filename == "index-0.html":
        soup.title.string = "PGF/TikZ Manual - Complete Online Documentation"
    # descriptions
    if filename == "index-0.html":
        meta = soup.new_tag('meta', content="Full online version of the documentation of PGF/TikZ, the TeX package for creating graphics.")
        meta['name'] = "description"
        soup.head.append(meta)
        og_meta = soup.new_tag('meta', property="og:description", content="Full online version of the documentation of PGF/TikZ, the TeX package for creating graphics.")
        soup.head.append(og_meta)
    elif stem in meta_descriptions:
        meta = soup.new_tag('meta', content=meta_descriptions[stem])
        meta['name'] = "description"
        soup.head.append(meta)
        og_meta = soup.new_tag('meta', property="og:description", content=meta_descriptions[stem])
        soup.head.append(og_meta)
    # canonical
    if filename == "index-0.html":
        link = soup.new_tag('link', rel="canonical", href="https://tikz.dev/")
        soup.head.append(link)
        meta = soup.new_tag('meta', property="og:url", content="https://tikz.dev/")
        soup.head.append(meta)
    else:
        link = soup.new_tag('link', rel="canonical", href="https://tikz.dev/" + stem)
        soup.head.append(link)
        meta = soup.new_tag('meta', property="og:url", content="https://tikz.dev/" + stem)
        soup.head.append(meta)
    # thumbnail
    img_filename = "social-media-banners/" + stem + ".png"
    if os.path.isfile("banners/"+img_filename):
        meta = soup.new_tag('meta', property="og:image", content="https://tikz.dev/" + img_filename)
        soup.head.append(meta)
        # allow Google Discover
        meta = soup.new_tag('meta', content="max-image-preview:large")
        meta['name'] = "robots"
        soup.head.append(meta)
    # og.type = article
    meta = soup.new_tag('meta', property="og:type", content="article")
    soup.head.append(meta)
    # get og.title from soup.title
    meta = soup.new_tag('meta', property="og:title", content=soup.title.string)
    soup.head.append(meta)
    # twitter format
    meta = soup.new_tag('meta', content="summary_large_image")
    meta['name'] = "twitter:card"
    soup.head.append(meta)

def add_spotlight_toc(filename):
    spotlight_files = ["index", "tutorials-guidelines", "tikz", "libraries", "gd", "dv"]
    if not any(filename == x + ".html" for x in spotlight_files):
        return
    # read as string
    with open("processed/"+filename, "r") as f:
        html = f.read()
    # read replacement string
    with open("spotlight-tocs/spotlight-toc-"+filename, "r") as f:
        toc = f.read()
    # replace
    if filename == "index.html":
        html = html.replace('<div class="titlepagepic">', toc)
    else:
        html = html.replace('</section>', toc+'</section>')
    # write back
    with open("processed/"+filename, "w") as f:
        f.write(html)

def handle_code_spaces(soup):
    # these are throwaway tags, only used to avoid overfull boxes
    for tag in soup.find_all(class_="numsp"):
        tag.decompose()
    # some links within codes have extra spaces, strip them
    for codeblock in soup.find_all(class_="example-code"):
        for link in codeblock.find_all("a"):
            link.string = link.string.strip()

for filename in sorted(os.listdir()):
    if filename.endswith(".html"):
        if filename in ["description.html", "pgfmanual_html.html", "home.html"] or "spotlight" in filename:
            continue
        else:
            print(f"Processing {filename}")
            with open(filename, "r") as fp:
                soup = BeautifulSoup(fp, 'html5lib')
                add_footer(soup)
                shorten_sidetoc_and_add_part_header(soup, is_home=(filename == "index-0.html"))
                rearrange_heading_anchors(soup)
                make_page_toc(soup)
                remove_mathjax_if_possible(filename, soup)
                make_entryheadline_anchor_links(soup)
                remove_html_from_links(filename, soup)
                remove_useless_elements(soup)
                addClipboardButtons(soup)
                rewrite_svg_links(soup)
                add_version_to_css_js(soup)
                process_images(soup)
                add_header(soup)
                favicon(soup)
                semantic_tags(soup)
                add_meta_tags(filename, soup)
                add_copyright_comment_block(filename, soup)
                handle_code_spaces(soup)
                soup.find(class_="bodyandsidetoc")['class'].append("grid-container")
                if filename == "index-0.html":
                    soup.h4.decompose() # don't need header on start page
                    soup.body['class'] = "index-page"
                    write_to_file(soup, "processed/index.html")
                    add_spotlight_toc("index.html")
                else:
                    write_to_file(soup, "processed/"+filename)
                    add_spotlight_toc(filename)


# prettify
# run command with subprocess
print("Prettifying")
subprocess.run(["prettier", "--write", "processed/*.html"])

def numspace_to_spaces(filename):
    "replace numspaces by normal spaces in code blocks"
    with open("processed/"+filename, "r") as f:
        html = f.read()
    for num_copies in range(30,1,-1):
        pattern = "&numsp;"*num_copies
        replacement = '<span class="spaces">'+' '*num_copies+'</span>'
        html = html.replace(pattern, replacement)
    for opener in [">", "}", "]", ","]:
        for closer in ["<", "{", "["]:
            pattern = opener+"&numsp;"+closer
            replacement = opener+" "+closer
            html = html.replace(pattern, replacement)
    html = html.replace("&numsp;", '<span class="spaces"> </span>')
    with open("processed/"+filename, "w") as f:
        f.write(html)

for filename in sorted(os.listdir()):
    if filename.endswith(".html"):
        if filename in ["index-0.html", "description.html", "pgfmanual_html.html", "home.html"] or "spotlight" in filename:
            continue
        else:
            numspace_to_spaces(filename)

print("Finished")