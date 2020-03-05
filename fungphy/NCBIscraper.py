"""NCBI phylogenetic marker scraper.


"""

import re
import sqlite3

from collections import defaultdict

import requests

import database


ENTREZ_URI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


MARKERS = {
    "ITS": ["internal+transcribed+spacer", "ITS"],
    "BenA": ["beta+tubulin", "bena"],
    "CaM": ["calmodulin", "cam"],
    "RPB1": ["RPB1"],
    "RPB2": ["RPB2"],
    "LSU": ["large+subunit+ribosomal+RNA"],
    "tsr1": ["tsr1"],
    "cct8": ["cct8"],
}

LENGTHS = {
    "ITS": (400, 2000),
    "BenA": (400, 2000),
    "CaM": (400, 2000),
    "RPB1": (500, 1200),
    "RPB2": (500, 1200),
    "LSU": (500, 1200),
    "tsr1": (500, 1300),
    "cct8": (500, 1300),
}

PATTERNS = {
    "search": re.compile(
        r"<eSearchResult>"
        r"<Count>(\d+)<\/Count>.+?"
        r"<QueryKey>(\S+)<\/QueryKey>"
        r"<WebEnv>(\S+)<\/WebEnv>"
    ),
    "xml": re.compile(
        r"<GBSeq_primary-accession>(\w+?)<\/GBSeq_primary-accession>"
        r".+?"
        r"<GBSeq_organism>(.+?) (.+?)<\/GBSeq_organism>"
        r".+?"
        r"<GBQualifier_name>(?:strain|isolate)<\/GBQualifier_name>"
        r".+?"
        r"<GBQualifier_value>(.+?)<\/GBQualifier_value>"
        r".+?"
        r"<GBSeq_sequence>(\w+)<\/GBSeq_sequence>",
        re.DOTALL,
    ),
}


def wrap(text, length=70, indent=4):
    lines = [text[i : i + length] for i in range(0, len(text), length)]
    return f"\n".join(f"{' ' * indent}{line}" for line in lines)


def form_entrez_query(marker):
    base = "aspergillus[orgn]"

    # Filter sequences outside of range specified in LENGTHS
    # Have to substitute : for %3A, e.g. 600:1000[SLEN]
    slen_min, slen_max = LENGTHS[marker]
    slen = f"{slen_min}%3A{slen_max}[SLEN]"

    # Substitute quotation marks with %22, join each alias with +OR+
    aliases = MARKERS[marker]
    aliases = "+OR+".join(f"%22{alias}%22[Title]" for alias in aliases)

    # Filter out uncertain species
    unsure = ["isolate", "sp.", "var.", "cf.", "aff."]
    filters = "+OR+".join(f"%22{key}%22[Title]" for key in unsure)

    # Build the query
    return f"{base}+AND+{slen}+AND+({aliases})+NOT+({filters})"

    "search": re.compile(
        r"<eSearchResult>"
        r"<Count>(\d+)<\/Count>.+?"
        r"<QueryKey>(\S+)<\/QueryKey>"
        r"<WebEnv>(\S+)<\/WebEnv>"
    ),

def search_marker(marker, xml_save=None):
    # Form the query URL
    db = "nuccore"
    query = form_entrez_query(marker)
    url = f"{ENTREZ_URI}/esearch.fcgi?db={db}&term={query}&usehistory=y"

    # Run ESearch
    print(f"Querying ESearch for '{marker}' sequences:\n{wrap(url)}")
    response = requests.get(url)

    # Parse WebEnv and QueryKey and form EFetch query
    count, key, web = PATTERNS["search"].search(response.text).groups()
    url = f"{ENTREZ_URI}/efetch.fcgi?db={db}&query_key={key}&WebEnv={web}&retmode=xml"
    print(f"Querying EFetch for {count} results:\n{wrap(url)}\n")
    response = requests.get(url)

    if xml_save:
        with open(xml_save, "w") as fp:
            fp.write(response.text)

    return response.text


def parse_xml(marker, xml):
    """Parse XML text"""

    # Genus -> Species -> Strain -> Marker -> Sequence
    organisms = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for match in PATTERNS["xml"].finditer(xml):
        accession, genus, species, strain, sequence = match.groups()
        species = species.split(" ")[0]  # e.g. strain name in organism field
        organisms[genus][species][strain][marker] = (accession, sequence)

    return organisms


def search_markers(markers):
    dics = [parse_xml(marker, search_marker(marker)) for marker in markers]
    return merge_dictionaries(dics)


def update_dictionary(d1, d2):
    for genus, species in d2.items():
        for sp, strains in species.items():
            for strain, markers in strains.items():
                d1[genus][sp][strain].update(markers)


def merge_dictionaries(dictionaries):
    first, *rest = dictionaries
    merged = first.copy()
    for d in rest:
        update_dictionary(merged, d)
    return merged


def summarise(d, spaces=0):
    for key in d:
        if isinstance(d[key], tuple):
            print("  " * spaces, f"{key}: {d[key][0]}")
        else:
            print("  " * spaces + str(key))
            summarise(d[key], spaces + 1)


def filter(organisms, threshold=-1, require=None):
    """Filter out organisms with less than threshold marker sequences."""
    new = {}
    for organism, markers in organisms.items():
        if threshold > 0 and len(markers) < threshold:
            continue
        if require and not set(require).issubset(markers):
            continue
        new[organism] = markers
    return new


def _insert(organisms, conn, cursor):
    # Get starting row ID
    first_id = cursor.execute("SELECT max(id) from organism;").fetchone()
    if not first_id[0]:
        # Since this returns (None,) if no previous rows
        first_id = (0,)
    print(f"Last row ID currently in db: {first_id[0]}")

    print("Inserting organisms into organism table")
    cursor.executemany(
        "INSERT INTO organism (genus, species, strain) VALUES (?, ?, ?)",
        [tuple(organism.split("|")) for organism in organisms],
    )
    conn.commit()

    print("Retrieving row IDs for inserted organisms")
    select = "SELECT id, genus, species, strain FROM organism WHERE id > ?"
    ids = {
        f"{genus}|{species}|{strain}": row_id
        for (row_id, genus, species, strain) in cursor.execute(select, first_id)
    }

    inserts = []
    for organism, markers in organisms.items():
        row_id = ids[organism]
        for marker, sequences in markers.items():
            inserts.extend(
                (marker, accession, sequence, row_id)
                for (accession, sequence) in sequences
            )

    print(f"Inserting {len(inserts)} marker sequences")
    cursor.executemany(
        "INSERT INTO sequence (marker, accession, sequence, organism_id) "
        "VALUES (?, ?, ?, ?)",
        inserts,
    )
    conn.commit()


def insert(organisms):
    try:
        conn, cursor = database.get_connection()
        _insert(organisms, conn, cursor)
    except sqlite3.OperationalError:
        conn.rollback()
        raise
