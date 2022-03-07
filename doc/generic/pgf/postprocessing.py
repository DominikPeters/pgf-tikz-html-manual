from xml.dom import minidom
from bs4 import BeautifulSoup
from shutil import copyfile, copytree
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
copytree("pgfmanual-images", "processed/pgfmanual-images", dirs_exist_ok=True)
copytree("standalone", "processed/standalone", dirs_exist_ok=True)

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

## shorten sidetoc
def shorten_sidetoc_and_add_part_header(soup):
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

## make anchor tags to definitions
def get_entryheadline_p(tag):
    for child in tag.children:
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
            soup.find(class_="hidden").decompose()
            # remove element with id "MathJax-script"
            soup.find(id="MathJax-script").decompose()
            # go through all script tags and remove the ones that contain the word "emulation"
            for tag in soup.find_all('script'):
                if "Lwarp MathJax emulation code" in tag.string:
                    tag.decompose()
        else:
            soup.find(id="MathJax-script").attrs['async'] = None

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
    h1 = soup.new_tag('strong')
    link = soup.new_tag('a', href="/")
    h1.append(link)
    link.append("PGF/Ti")
    k = soup.new_tag("i")
    k.append("k")
    link.append(k)
    link.append("Z Manual")
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
    footer_left = soup.new_tag('div', class_="footer-left")
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
    # Link to About the HTML version
    link = soup.new_tag('a', href="https://github.com/DominikPeters/pgf-tikz-html-manual")
    link.string = "About this HTML version"
    footer_left.append(link)
    #
    footer.append(footer_left)
    footer_right = soup.new_tag('div', class_="footer-right")
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

def semantic_tags(soup):
    for example in soup.find_all(class_="example"):
        example.name = "figure"
    for examplecode in soup.find_all(class_="example-code"):
        p = examplecode.find("p")
        p.name = "code"

for filename in sorted(os.listdir()):
    if filename.endswith(".html"):
        if filename in ["description.html", "pgfmanual_html.html", "home.html"]:
            continue
        else:
            print(f"Processing {filename}")
            with open(filename, "r") as fp:
                soup = BeautifulSoup(fp, 'html5lib')
                add_footer(soup)
                shorten_sidetoc_and_add_part_header(soup)
                rearrange_heading_anchors(soup)
                make_page_toc(soup)
                remove_mathjax_if_possible(filename, soup)
                make_entryheadline_anchor_links(soup)
                remove_html_from_links(filename, soup)
                remove_useless_elements(soup)
                addClipboardButtons(soup)
                rewrite_svg_links(soup)
                process_images(soup)
                add_header(soup)
                favicon(soup)
                semantic_tags(soup)
                soup.find(class_="bodyandsidetoc")['class'].append("grid-container")
                if filename == "index-0.html":
                    soup.h4.decompose() # don't need header on start page
                    meta = soup.new_tag('meta', content="Full online version of the documentation of PGF/TikZ, the TeX package for creating graphics.")
                    meta['name'] = "description"
                    soup.head.append(meta)
                    soup.title.string = "PGF/TikZ Manual - Complete Online Documentation"
                    write_to_file(soup, "processed/index.html")
                else:
                    write_to_file(soup, "processed/"+filename)


# prettify
# run command with subprocess
print("Prettifying")
subprocess.run(["prettier", "--write", "processed"])
