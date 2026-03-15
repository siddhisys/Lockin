import requests # type: ignore
import time
from config.settings import HEADERS, REQUEST_DELAY, MIN_TEXT_LENGTH
from parsers.generic_parser import parse
from core.cleaner import clean_text
from core.chunker import chunk_text


def scrape_url(url):

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        raw_text = parse(response.text)
        cleaned = clean_text(raw_text)

        if len(cleaned) < MIN_TEXT_LENGTH:
            return None

        chunks = chunk_text(cleaned)

        return chunks

    except Exception as e:
        return None


def scrape_sources(source_dict, domain, subdomain):

    results = []

    for source, urls in source_dict.items():

        for url in urls:

            chunks = scrape_url(url)

            if not chunks:
                results.append({
                    "domain": domain,
                    "subdomain": subdomain,
                    "source": source,
                    "url": url,
                    "status": "failed"
                })
            else:
                results.append({
                    "domain": domain,
                    "subdomain": subdomain,
                    "source": source,
                    "url": url,
                    "status": "success",
                    "chunks": chunks
                })

            time.sleep(REQUEST_DELAY)

    return results
