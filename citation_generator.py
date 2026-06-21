def _format_authors(authors: str):
    items = [a.strip() for a in authors.split(",") if a.strip()]
    return items


def generate_citation(style, title, authors, year, journal, volume, issue, pages, doi):
    author_list = _format_authors(authors)
    if not author_list:
        author_list = ["Unknown Author"]
    year = year or "n.d."
    journal = journal or "Unknown Source"
    volume = volume or ""
    issue = issue or ""
    pages = pages or ""
    doi = doi or ""

    if style.upper() == "APA":
        formatted_authors = ", ".join(author_list)
        vol_issue = f", {volume}({issue})" if volume and issue else f", {volume}" if volume else ""
        page_part = f", {pages}" if pages else ""
        doi_part = f" {doi}" if doi else ""
        return f"{formatted_authors} ({year}). {title}. {journal}{vol_issue}{page_part}.{doi_part}".strip()

    if style.upper() == "IEEE":
        formatted_authors = ", ".join(author_list)
        vol_part = f", vol. {volume}" if volume else ""
        issue_part = f", no. {issue}" if issue else ""
        pages_part = f", pp. {pages}" if pages else ""
        doi_part = f", {doi}" if doi else ""
        return f"{formatted_authors}, \"{title},\" {journal}{vol_part}{issue_part}{pages_part}, {year}{doi_part}."

    if style.upper() == "MLA":
        formatted_authors = ", ".join(author_list)
        vol_part = f", vol. {volume}" if volume else ""
        issue_part = f", no. {issue}" if issue else ""
        pages_part = f", pp. {pages}" if pages else ""
        doi_part = f", {doi}" if doi else ""
        return f"{formatted_authors}. \"{title}.\" {journal}{vol_part}{issue_part}, {year}{pages_part}{doi_part}."

    return "Unsupported citation style."