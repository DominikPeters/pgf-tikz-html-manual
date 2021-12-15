from bs4 import BeautifulSoup
from shutil import copyfile, copytree
import re
import os
import subprocess

copyfile("style.css", "processed/style.css")
copyfile("lwarp.css", "processed/lwarp.css")
copyfile("pgfmanual.js", "processed/pgfmanual.js")

## table of contents and anchor links
def rearrange_heading_anchors(soup):
    heading_tags = ["h4", "h5", "h6"]
    for tag in soup.find_all(heading_tags):
        # print(f"{tag.name} -> {tag.text.strip()} -> {tag.get('id')}")
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
    heading_tags = ["h4", "h5", "h6"]
    for tag in soup.find_all(heading_tags):
        # print(f"{tag.name} -> {tag.text.strip()} -> {tag.get('id')}")
        item = soup.new_tag('p')
        a = soup.new_tag('a', href=f"#{tag.get('id')}")
        a.string = tag.text.strip()
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
        if entry.a['href'] == "index.html":
            continue
        if len(entry.a['href'].split('#')) < 2:
            print(f"WARNING: {entry.a['href']}")
        filename = entry.a['href'].split('#')[0]
        file_id = entry.a['href'].split('#')[1]
        entry.a['href'] = filename.replace(".html", "") # get rid of autosec in toc, not needed
        # Skip intro link because it doesn't have a part
        if file_id == "autosec-7":
            entry.a['class'].append('toc-intro-link')
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
                my_part = element
        elif "tocsection" in entry.a['class']:
            element = {
                "tag": entry,
                "file_id": file_id,
            }
            last_part['children'].append(element)
            if file_id == my_file_id:
                assert 'class' not in entry
                entry['class'] = ["current"]
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
                contents = part['tag'].a.contents[1:]
                contents[1].replace("\u2003", "")
                h2 = soup.new_tag('h2')
                h2.contents = contents
                h2['class'] = ['inserted']
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

def add_header(soup):
    header = soup.new_tag('header')
    h1 = soup.new_tag('h1')
    link = soup.new_tag('a', href="/")
    h1.append(link)
    link.append("PGF/Ti")
    k = soup.new_tag("i")
    k.append("k")
    link.append(k)
    link.append("Z Manual")
    header.append(h1)
    search_input = soup.new_tag('input', type="search", placeholder="Search")
    search_input['class'] = "search-input"
    header.append(search_input)
    soup.body.insert(0, header)

    # import search elements
    link = soup.new_tag('link', rel="stylesheet", href="https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/docsearch.min.css")
    soup.head.append(link)

    script = soup.new_tag('script', src="https://cdn.jsdelivr.net/npm/docsearch.js@2/dist/cdn/docsearch.min.js")
    soup.body.append(script)
    script = soup.new_tag('script')
    script.append("""
      docsearch({
        // Your Search API Key
        apiKey: 'ae66ec3fc9df4b52b4d6f24fc8508fd3',
        // The index populated by the DocSearch scraper
        indexName: 'tikz.dev',
        // Your Algolia Application ID
        appId: 'Q70NNMA9GC',
        // Replace inputSelector with a CSS selector
        // matching your search input
        inputSelector: '.search-input',
        // Set debug to true to inspect the dropdown
        debug: false,
    });
    """)
    soup.body.append(script)


os.makedirs("processed", exist_ok=True)
for filename in sorted(os.listdir(".")):
    if filename.endswith(".html"):
        if filename in ["description.html", "pgfmanual_html.html"]:
            continue
        else:
            print(f"Processing {filename}")
            with open(filename, "r") as fp:
                soup = BeautifulSoup(fp, 'html5lib')
                if filename == "index.html":
                    remove_html_from_links(filename, soup)
                    remove_mathjax_if_possible(filename, soup)
                    add_header(soup)
                    write_to_file(soup, "processed/"+filename)
                    continue
                rearrange_heading_anchors(soup)
                shorten_sidetoc_and_add_part_header(soup)
                make_page_toc(soup)
                remove_mathjax_if_possible(filename, soup)
                make_entryheadline_anchor_links(soup)
                remove_html_from_links(filename, soup)
                remove_useless_elements(soup)
                add_header(soup)
                write_to_file(soup, "processed/"+filename)


copytree("pgfmanual-images", "processed/pgfmanual-images", dirs_exist_ok=True)


# prettify
# run command with subprocess
print("Prettifying")
subprocess.run(["prettier", "--write", "processed"])
