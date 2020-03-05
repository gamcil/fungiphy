"""Scrape aspergilluspenicillium.org using BeautifulSoup"""

import re
import unicodedata

import requests

from bs4 import BeautifulSoup


BASE = "https://www.aspergilluspenicillium.org"

URLS = {
    "aspergillus-names": ["a-h", "i-p", "q-z"],
    "penicillium-names": ["a-h", "i-p", "q-z", "a-h-2", "i-p-2", "q-z-2"],
}

PATTERN = re.compile(
    r"\*(\w+?)\s([A-Za-z_-]+?)\s"
    r"(.+?) "
    r"\[MB(\w+)\]"
    r"\.? — type: (.+?)"
    r"\. ex-type: (.+?)"
    r"\. sect (.+?)"
    r"\. ITS barcode: ?(\S.+?) .+?"
    r"BenA ?= ?(.+?); "
    r"CaM ?= ?(.+?); "
    r"RPB2 ?= ?(.+?)?\)"
)


def form_url(genus, span, letter):
    return f"{BASE}/{genus}-{span}/{genus}-{letter}"


def get_letters(span):
    span = span[:3]  # cut off -2 for talaromyces
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    start, end = [alphabet.find(c) for c in span.split("-")]
    return alphabet[start : end + 1]


def iter_urls():
    for genus, spans in URLS.items():
        for span in spans:
            for letter in get_letters(span):
                yield form_url(genus, span, letter)


def get_species(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features="html.parser")
    return [sp.get_text() for sp in soup.find_all("p")]


def scrape(urls=None):
    if not urls:
        urls = iter_urls()
    good, bad = [], []
    for url in urls:
        print(f"Scraping: {url}")
        spp = get_species(url)
        for sp in spp:
            try:
                groups = [
                    unicodedata.normalize("NFKD", g)
                    for g in PATTERN.search(sp).groups()
                ]
                good.append(groups)
            except:
                bad.append(sp)
    return good, bad
