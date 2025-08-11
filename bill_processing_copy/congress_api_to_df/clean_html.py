from bs4 import BeautifulSoup, Comment, NavigableString, Tag
import re
from collections import defaultdict

import pandas as pd
import html


'''MY VERSION'''

def clean(xml):
    """
    Clean legislative XML and align it with the summary text.
    
    Args:
        xml (str): The XML string containing legislative text.
    
    Returns:
        pandas dataframe
        rows are chunks of text, columns contain title, subtitle, part, and text.
    """
    soup = BeautifulSoup(xml, features="lxml-xml")

    df = pd.DataFrame(columns=["title", "subtitle", "part", "section", "text"])

    #for title in soup.find_all("title"):
        
    
    

###############


def extract_element_text(element, level=0):
    parts = []
    indent = "  " * level  # Indentation to reflect hierarchy

    # Include section number if present
    enum = element.find("enum")
    if enum:
        parts.append(f"{indent}{enum.get_text(strip=True)}")

    # Include section header if present
    header = element.find("header")
    if header:
        parts.append(f"{indent}{header.get_text(strip=True)}")

    # Include inline text from <text> tags (not nested)
    for text_node in element.find_all("text", recursive=False):
        text_content = text_node.get_text(" ", strip=True)
        if text_content:
            parts.append(f"{indent}{text_content}")

    # Recursively process child structures (like subsection, paragraph, etc.)
    for child in element.find_all(recursive=False):
        if child.name in {"section", "subsection", "paragraph", "subparagraph", "clause", "quoted-block"}:
            parts.append(extract_element_text(child, level + 1))

    return "\n".join(parts)


def chunk_by_title(soup):
    """
    Groups legislative sections under titles and subtitles like 'TITLE I', 'TITLE II', etc.
    """
    chunks = {}
    current_title = "UNTITLED"

    for title in soup.find_all("title"):
        title_enum = title.find("enum")
        title_header = title.find("header")
        if title_enum and title_enum.get_text(strip=True).isupper():
            current_title = f"TITLE {title_enum.get_text(strip=True)}"
            chunks[current_title] = []

        # Capture all nested sections inside the title
        for section in title.find_all("section", recursive=True):
            section_text = extract_element_text(section)
            chunks[current_title].append(section_text)

    return {k: "\n\n".join(v) for k, v in chunks.items()}


def parse_summary_sections(summary_text):
    titles = {}
    current_title = None
    current_subtitle = None
    current_part = None

    lines = summary_text.splitlines()
    buffer = []

    def flush():
        nonlocal buffer
        text = "\n".join(buffer).strip()
        if text:
            titles[current_title][current_subtitle][current_part].append(text)
        buffer = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match TITLE lines
        title_match = re.match(r"(TITLE [IVXLCDM]+)--(.+)", line, re.IGNORECASE)
        if title_match:
            flush()
            current_title = title_match.group(1).upper()
            titles[current_title] = defaultdict(lambda: defaultdict(list))
            current_subtitle = "UNLABELED"
            current_part = "UNLABELED"
            continue

        # Match Subtitle lines
        subtitle_match = re.match(r"(Subtitle [A-Z])--(.+)", line, re.IGNORECASE)
        if subtitle_match:
            flush()
            current_subtitle = subtitle_match.group(1).title()
            current_part = "UNLABELED"
            continue

        # Match Part lines
        part_match = re.match(r"(Part \d+)--(.+)", line, re.IGNORECASE)
        if part_match:
            flush()
            current_part = part_match.group(1).title()
            continue

        # Otherwise, it's a paragraph of content
        buffer.append(line)

    flush()
    return titles


def align_chunks(legislative_chunks, summary_chunks):
    aligned = {}
    for title in summary_chunks:
        aligned[title] = {
            "summary": summary_chunks[title],
            "full_text": legislative_chunks.get(title, "[No matching text found]")
        }
    return aligned


def clean_legislative_xml(xml_tree, summary) -> str:
    """
    Return a dictionary with chunked summaries and their full text."""
    soup = BeautifulSoup(xml_tree, features="lxml-xml")

    title_chunks = chunk_by_title(soup)
    summary_chunks = parse_summary_sections(summary)
    if len(title_chunks) != len(summary_chunks):
        print("Warning: Number of titles in legislative text does not match summary text.")
        print(f"Legislative titles: {len(title_chunks)}, Summary titles: {len(summary_chunks)}")
    aligned_chunks = align_chunks(title_chunks, summary_chunks)

    return aligned_chunks


def clean_legislative_html(html_text: str) -> str:
    """
    Strip HTML from legislative text, preserving paragraphs and bullet points.
    """
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove comments
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()

    output = []

    def walk(el, indent=0):
        if isinstance(el, NavigableString):
            return el.strip()

        elif isinstance(el, Tag):
            if el.name == "p":
                text = " ".join(walk(child) for child in el.children if child)
                if text:
                    output.append(text.strip())

            elif el.name in {"ul", "ol"}:
                is_ordered = el.name == "ol"
                for i, li in enumerate(el.find_all("li", recursive=False), start=1):
                    bullet = f"{i}." if is_ordered else "-"
                    li_text = walk(li)
                    output.append("  " * indent + f"{bullet} {li_text.strip()}")

            elif el.name == "li":
                return " ".join(walk(child) for child in el.children if child)

            elif el.name in {"div", "section"}:
                for child in el.children:
                    walk(child, indent)

            elif el.name == "br":
                output.append("")

            else:
                return " ".join(walk(child) for child in el.children if child)

        return ""

    walk(soup.body if soup.body else soup)

    cleaned = "\n\n".join(line for line in output if line.strip())
    return html.unescape(cleaned)

