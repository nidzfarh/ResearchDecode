from PyPDF2 import PdfReader

def extract_metadata(filepath):

    reader = PdfReader(filepath)

    pages = len(reader.pages)

    first_page = reader.pages[0].extract_text()

    lines = first_page.split("\n")

    # =====================================
    # CLEAN LINES
    # =====================================

    cleaned = []

    for line in lines:

        line = line.strip()

        if len(line) > 3:

            cleaned.append(line)

    # =====================================
    # TITLE
    # =====================================

    title = "Unknown Title"

    for i, line in enumerate(cleaned):

        if "Mobile Applications" in line:

            title = line

            # combine next line if title wraps
            if i + 1 < len(cleaned):

                next_line = cleaned[i + 1]

                if len(next_line) < 80 and \
                   "@" not in next_line and \
                   "Abstract" not in next_line:

                    title += " " + next_line

            break

    # =====================================
    # AUTHORS
    # =====================================

    authors = []

    for line in cleaned:

        if "@" in line:
            continue

        if "University" in line:
            continue

        if "ActionAid" in line:
            continue

        words = line.split()

        if len(words) >= 2 and \
           all(word[0].isupper() for word in words if word[0].isalpha()):

            if line != title:

                authors.append(line)

    # remove duplicates
    authors = list(dict.fromkeys(authors))

    # keep only first 2 probable names
    authors = authors[:2]

    author_text = ", ".join(authors)

    if not author_text:
        author_text = "Unknown Author"

    return {

        "title": title,

        "author": author_text,

        "pages": pages
    }