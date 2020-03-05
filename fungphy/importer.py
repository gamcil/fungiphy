"""Import organism table."""


import csv
import sys

import requests

from database import db, Genus, Organism, ExType, Marker, Section, Subgenus


def parse_fasta(handle):
    """Parse sequences in a FASTA file."""
    sequences = {}
    for line in handle:
        try:
            line = line.decode().strip()
        except AttributeError:
            line = line.strip()
        if line.startswith(">"):
            header = line[1:]
            sequences[header] = ""
        else:
            sequences[header] += line
    return sequences


def efetch_sequences_request(headers):
    response = requests.post(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?",
        params={"db": "nuccore", "rettype": "fasta"},
        files={"id": ",".join(headers)},
    )

    if response.status_code != 200:
        raise requests.HTTPError(
            f"Error fetching sequences from NCBI [code {response.status_code}]."
            " Bad query IDs?"
        )

    return response


def efetch_sequences(headers):
    """Retrieve protein sequences from NCBI for supplied accessions."""
    response = efetch_sequences_request(headers)
    sequences = {}
    for key, value in parse_fasta(response.text.split("\n")).items():
        for header in headers:
            if header not in sequences and header in key:
                sequences[header] = value
                break
    return sequences


def parse_csv(fp):
    """Parse marker table, delimited by '|'.

    Assumes columns:
        Genus|Species|Reference|MycoBank ID|Type|Ex-types|Subgenus|Section|*markers

    Ex-types should be delimited by ' = ', as in taxonomy papers.

    Assumes there is a header row; this is how marker types are discovered.
    """

    genuses = {}
    sections = {}
    subgenera = {}
    sequences = {}
    organisms = []

    marker_names = None

    reader = csv.reader(fp, delimiter="|")

    print(f"Parsing: {fp.name}")
    for index, row in enumerate(reader, -1):
        gen, sp, ref, mbank, ty, ex, subg, sect, *markers = row

        if index == -1:  # start enum at -1 so matches organism index at 0
            marker_names = markers
            continue

        if gen not in genuses:
            genuses[gen] = Genus(name=gen)

        if subg not in subgenera:
            subgenera[subg] = Subgenus(name=subg, genus=genuses[gen])

        if sect not in sections:
            sections[sect] = Section(name=sect, subgenus=subgenera[subg])

        o = Organism(
            species=sp,
            reference=ref,
            mycobank=mbank,
            type_strain=ty,
            section=sections[sect],
            extypes=[ExType(strain=e) for e in ex.split(" = ")],
        )

        for name, marker in zip(marker_names, markers):
            sequences[marker] = {"type": name, "org": index}

        organisms.append(o)

    print(f"Fetching {len(sequences)} sequences from NCBI")
    for accession, sequence in efetch_sequences(sequences).items():
        org_id = sequences[accession]["org"]
        marker = sequences[accession]["type"]
        m = Marker(marker=marker, accession=accession, sequence=sequence)
        organisms[org_id].markers.append(m)

    print(f"Committing {len(organisms)} organisms to DB")
    db.session.add_all(organisms)
    db.session.commit()
