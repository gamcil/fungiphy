"""Import organism table."""


import csv
import sys
import unicodedata

import requests

from fungphy.models import (
    Marker,
    MarkerType,
    Section,
    Species,
    Strain,
    StrainName,
)
from fungphy.database import session


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


def get_sections():
    return {
        section.name: section.id
        for section in session.query(Section)
    }


def get_strain_names():
    return set(
        strain.name
        for strain in session.query(StrainName)
    )


def get_marker_types():
    return {
        marker.name: marker.id
        for marker in session.query(MarkerType)
    }


def get_marker_accessions():
    return set(
        marker.accession
        for marker in session.query(Marker)
    )


def parse_csv(fp):
    """Parse marker table, delimited by '|'.

    Assumes columns:
        Epithet|Reference|MycoBank ID|Type|Ex-types|Section|*markers

    Ex-types should be delimited by ' = ', as in taxonomy papers.

    Assumes there is a header row; this is how marker types are discovered.
    """

    # Get current sections/strains for comparison
    sections = get_sections()
    strain_names = get_strain_names()
    marker_types = get_marker_types()
    marker_accessions = get_marker_accessions()

    species = []
    sequences = {}
    marker_names = None

    reader = csv.reader(fp, delimiter="|")
    marker_ids = []

    # Validate marker types
    for marker in next(reader)[6:]:
        if marker not in marker_types:
            raise ValueError(
                f"Could not find marker {marker} in database,"
                f" exiting. Valid markers: {marker_types.keys()}"
            )
        marker_ids.append(marker_types[marker])

    print(f"Parsing: {fp.name}")
    species_index = 0
    for index, row in enumerate(reader):
        (
            epithet,
            ref,
            mbank,
            ty,
            ex,
            sect,
            *markers
        ) = [unicodedata.normalize("NFKC", field) for field in row]

        if sect not in sections:
            print(f"Could not find section {sect} in database, skipping")
            continue

        names = ex.split(" = ")
        if strain_names.issuperset(names):
            print(f"Row {index + 1} ({epithet}) has duplicate strain name, skipping")
            continue

        if marker_accessions.issuperset(markers):
            print(f"Row {index + 1} ({epithet}) has duplicate marker, skipping")
            continue

        sp = session.query(Species).filter(Species.epithet == epithet).first()

        if not sp:
            sp = Species(
                type=ty,
                epithet=sp,
                reference=ref,
                mycobank=mbank,
                section_id=sections[sect],
            )

        st = Strain(is_ex_type=True, species=sp)

        for name in ex.split(" = "):
            print("ex", ex.split(" = "))
            sn = StrainName(name=name, strain=st)

        for marker_id, marker in zip(marker_ids, markers):
            sequences[marker] = (species_index, len(sp.strains) - 1, marker_id)

        species.append(sp)
        species_index += 1

    if not species:
        print("No new species, exiting")
        return

    print(f"Fetching {len(sequences)} sequences from NCBI")
    for accession, sequence in efetch_sequences(sequences).items():
        sp_index, st_index, marker_id = sequences[accession]
        marker = Marker(
            marker_type_id=marker_id,
            accession=accession,
            sequence=sequence
        )
        species[sp_index].strains[st_index].markers.append(marker)

    print(f"Committing {len(species)} organisms to DB")
    session.add_all(species)
    session.commit()
