"""Import organism table."""


import csv
import sys

import requests

from fungphy.database import (
    Genus,
    Marker,
    Section,
    Species,
    Strain,
    StrainName,
    Subgenus,
    db,
)


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

    species = []
    genuses = {}
    sections = {}
    subgenera = {}
    sequences = {}

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

        sp = Species(
            type=ty,
            epithet=sp,
            reference=ref,
            mycobank=mbank,
            section=sections[sect],
        )

        st = Strain(is_ex_type=True, species=sp)

        for name in ex.split(" = "):
            sn = StrainName(name=name, strain=st)

        for name, marker in zip(marker_names, markers):
            sequences[marker] = (index, name)

        species.append(sp)

    print(f"Fetching {len(sequences)} sequences from NCBI")
    for accession, sequence in efetch_sequences(sequences).items():
        sp_id, marker = sequences[accession]
        species[sp_id].strains[0].markers.append(
            Marker(marker=marker, accession=accession, sequence=sequence)
        )

    print(f"Committing {len(species)} organisms to DB")
    db.session.add_all(species)
    db.session.commit()
