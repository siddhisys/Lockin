from bs4 import BeautifulSoup

def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    texts = []

    for tag in soup.find_all(["p", "li", "h1", "h2", "h3"]):
        txt = tag.get_text(strip=True)
        if len(txt) > 30:
            texts.append(txt)

    return " ".join(texts)
