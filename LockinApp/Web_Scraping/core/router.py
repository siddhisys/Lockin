from config.sources import SCRAPING_SOURCES

def get_domains():
    return list(SCRAPING_SOURCES.keys())

def get_subdomains(domain):
    return list(SCRAPING_SOURCES.get(domain, {}).keys())

def get_sources(domain, subdomain):
    return SCRAPING_SOURCES[domain][subdomain]
