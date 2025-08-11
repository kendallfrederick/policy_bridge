from bs4 import BeautifulSoup, NavigableString, Tag
import pandas as pd
import html
import re


def parse_structured_summary(summary_text: str) -> pd.DataFrame:
    """
    Parse a legislative summary into a DataFrame with division, title, and text chunks.
    """
    records = []

    current_division = None
    current_title_number = None
    current_title_header = None
    current_text = []

    lines = summary_text.strip().splitlines()

    division_pattern = re.compile(r'^DIVISION\s+([A-Z])--(.+)', re.IGNORECASE)
    title_pattern = re.compile(r'^TITLE\s+([IVXLCDM]+)--(.+)', re.IGNORECASE)
    bullet_pattern = re.compile(r'^[-•*]\s+.+')  # detect bullet lines

    def flush_text():
        if current_text:
            # Join all lines, strip trailing punctuation, and normalize
            flat_text = ", ".join(line.rstrip(";,") for line in current_text if line)
            flat_text = re.sub(r'\s+', ' ', flat_text).strip()
            records.append({
                "division_number": current_division,
                "title_number": current_title_number,
                "title_header": current_title_header,
                "text_chunk": flat_text
            })
            current_text.clear()


    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for DIVISION header
        div_match = division_pattern.match(line)
        if div_match:
            flush_text()
            current_division = f"{div_match.group(1)}"
            # Division header text is not reused, but could be captured with div_match.group(2)
            continue

        # Check for TITLE header
        title_match = title_pattern.match(line)
        if title_match:
            flush_text()
            current_title_number = f"{title_match.group(1)}"
            current_title_header = title_match.group(2).strip()
            continue

        # Otherwise, it's content (paragraph or bullet)
        current_text.append(line)

    # Flush last chunk
    flush_text()

    return pd.DataFrame(records)


def parse_summary_with_subparts(summary_text):
    summary_text = summary_text.replace("–", "-").replace("—", "-")

    # Regex to split into titles
    title_blocks = re.split(r'(TITLE\s+[IVXLCDM]+)--\s*([^\n]+)', summary_text)

    records = []

    for i in range(1, len(title_blocks), 3):
        title_number = title_blocks[i].strip()
        title_text = title_blocks[i+1].strip()
        title_content = title_blocks[i+2].strip()

        subtitle = None
        part = None

        # Split on Subtitle, Part, and Section with minimal lookahead conflicts
        chunks = re.split(
            r'(Subtitle\s+[A-Z]+\s*--[^\n]+|Part\s+\d+\s*--[^\n]+|\(Sec\.\s*\d{5}\))',
            title_content
        )

        # First chunk is the high-level summary for the title
        full_title_summary = chunks[0].strip()

        j = 1
        while j < len(chunks) - 1:
            header = chunks[j].strip()
            content = chunks[j+1].strip()

            if header.startswith("Subtitle"):
                subtitle = header
            elif header.startswith("Part"):
                part = header
            elif header.startswith("(Sec."):
                match = re.match(r"\(Sec\.\s*(\d{5})\)", header)
                if match:
                    section_number = match.group(1)
                    records.append({
                        "title_number": title_number,
                        "title_text": title_text,
                        "subtitle": subtitle,
                        "part": part,
                        "section_number": section_number,
                        "section_summary": content,
                        "full_title_summary": full_title_summary
                    })

            j += 2

    return pd.DataFrame(records)


def parse_summary_with_subparts_original(summary_text):
    summary_text = summary_text.replace("–", "-").replace("—", "-")

    # Split into titles using regex, capturing TITLE header and title text
    title_blocks = re.split(r'(TITLE\s+[IVXLCDM]+)--\s*([^\n]+)', summary_text)

    records = []

    # Iterate over every title
    for i in range(1, len(title_blocks), 3):
        title_number = title_blocks[i].strip()
        title_text = title_blocks[i+1].strip()
        title_content = title_blocks[i+2].strip()

        # Initialize state variables
        subtitle = None
        part = None

        # Split title content by Subtitle, Part, or Section
        # Keep track of all headers and section texts
        chunks = re.split(r'(Subtitle\s+[A-Z]+\s*--[^\n]+|Part\s+\d+\s*--[^\n]+|\(Sec\.\s*\d{5}\))', title_content)

        # First chunk is preamble for title-level summary
        full_title_summary = chunks[0].strip()
        
        j = 1
        while j < len(chunks) - 1:
            header = chunks[j].strip()
            content = chunks[j+1].strip()

            if header.startswith("Subtitle"):
                subtitle = header
            elif header.startswith("Part"):
                part = header
            elif header.startswith("(Sec."):
                # Extract section number from header
                match = re.match(r"\(Sec\.\s*(\d{5})\)", header)
                if match:
                    section_number = match.group(1)
                    records.append({
                        "title_number": title_number,
                        "title_text": title_text,
                        "subtitle": subtitle,
                        "part": part,
                        "section_number": section_number,
                        "section_summary": content,
                        "full_title_summary": full_title_summary
                    })
            j += 2

    return pd.DataFrame(records)

def clean_legis_xml(xml_string):
    soup = BeautifulSoup(xml_string, "lxml-xml")
    legis_body = soup.find("legis-body")
    if not legis_body:
        print("No legis-body found in the XML.")
        return pd.DataFrame(columns=["division_number", "division_header", "title_number", "title_header", "subtitle", "part", "section_number", "section_header", "text"])

    def extract_text(element):
        parts = []
        for desc in element.descendants:
            if isinstance(desc, NavigableString):
                parts.append(str(desc))
            elif isinstance(desc, Tag):
                if desc.name == "external-xref":
                    continue
                elif desc.name == "enum":
                    parent_name = desc.parent.name
                    if parent_name in ("title", "section", "division"):
                        continue  # handled separately
                    parts.append(desc.get_text())
                elif desc.name in {"quote", "term", "italic"}:
                    continue  # strip formatting tags
        return html.unescape(" ".join(" ".join(parts).split()))

    rows = []
    current_context = {
        "division_number": None,
        "division_header": None,
        "title_number": None,
        "title_header": None,
        "subtitle": None,
        "part": None,
        "section_number": None,
        "section_header": None
    }

    def add_chunks(text, context):
        sentences = text.split('. ')
        chunk = ""
        for s in sentences:
            if len(chunk) + len(s) + 1 > 2500:
                if chunk:
                    rows.append({**context, "text": chunk.strip()})
                    chunk = ""
            chunk += s + ". "
        if chunk.strip():
            rows.append({**context, "text": chunk.strip()})

    for element in legis_body.descendants:
        if isinstance(element, Tag):
            tag_name = element.name
            if tag_name == "division":
                current_context["division_number"] = element.enum.get_text() if element.enum else None
                current_context["division_header"] = element.header.get_text() if element.header else None
                # Reset lower-level context when a new division starts
                current_context["title_number"] = None
                current_context["title_header"] = None
                current_context["subtitle"] = None
                current_context["part"] = None
                current_context["section_number"] = None
                current_context["section_header"] = None
            elif tag_name == "title":
                current_context["title_number"] = element.enum.get_text() if element.enum else None
                current_context["title_header"] = element.header.get_text() if element.header else None
                # Reset deeper levels
                current_context["subtitle"] = None
                current_context["part"] = None
                current_context["section_number"] = None
                current_context["section_header"] = None
            elif tag_name == "subtitle":
                current_context["subtitle"] = element.header.get_text() if element.header else None
                current_context["part"] = None
                current_context["section_number"] = None
                current_context["section_header"] = None
            elif tag_name == "part":
                current_context["part"] = element.header.get_text() if element.header else None
                current_context["section_number"] = None
                current_context["section_header"] = None
            elif tag_name == "section":
                current_context["section_number"] = element.enum.get_text() if element.enum else None
                current_context["section_header"] = element.header.get_text() if element.header else None
            elif tag_name in {"subsection", "paragraph", "subparagraph", "clause", "subclause"}:
                text = extract_text(element)
                if text:
                    add_chunks(text, current_context.copy())

    return pd.DataFrame(rows)


def clean_legis_xml_original(xml_string):
    soup = BeautifulSoup(xml_string, "lxml-xml")
    legis_body = soup.find("legis-body")
    if not legis_body:
        return pd.DataFrame(columns=["title_number", "title_header", "subtitle", "part", "section_number", "section_header", "text"])

    def extract_text(element):
        parts = []
        for desc in element.descendants:
            if isinstance(desc, NavigableString):
                parts.append(str(desc))
            elif isinstance(desc, Tag):
                if desc.name == "external-xref":
                    continue
                elif desc.name == "enum":
                    # Handle enum specially
                    parent_name = desc.parent.name
                    if parent_name in ("title", "section"):
                        continue  # handled separately
                    parts.append(desc.get_text())
                elif desc.name in {"quote", "term", "italic"}:
                    continue  # strip formatting tags
        return html.unescape(" ".join(" ".join(parts).split()))

    rows = []
    current_context = {
        "title_number": None,
        "title_header": None,
        "subtitle": None,
        "part": None,
        "section_number": None,
        "section_header": None
    }

    def add_chunks(text, context):
        sentences = text.split('. ')
        chunk = ""
        for s in sentences:
            if len(chunk) + len(s) + 1 > 2500:
                if chunk:
                    rows.append({**context, "text": chunk.strip()})
                    chunk = ""
            chunk += s + ". "
        if chunk.strip():
            rows.append({**context, "text": chunk.strip()})

    for element in legis_body.descendants:
        if isinstance(element, Tag):
            tag_name = element.name
            if tag_name == "title":
                current_context["title_number"] = element.enum.get_text() if element.enum else None
                current_context["title_header"] = element.header.get_text() if element.header else None
            elif tag_name == "subtitle":
                current_context["subtitle"] = element.header.get_text() if element.header else None
            elif tag_name == "part":
                current_context["part"] = element.header.get_text() if element.header else None
            elif tag_name == "section":
                current_context["section_number"] = element.enum.get_text() if element.enum else None
                current_context["section_header"] = element.header.get_text() if element.header else None
            elif tag_name in {"subsection", "paragraph", "subparagraph", "clause", "subclause"}:
                text = extract_text(element)
                if text:
                    add_chunks(text, current_context.copy())

    return pd.DataFrame(rows)
