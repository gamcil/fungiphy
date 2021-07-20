"""Import organism table."""

from __future__ import annotations

import re
import csv
import requests

from typing import IO, Dict, Collection

from fungphy.models import (
    Marker,
    MarkerType,
    Genus,
    Subgenus,
    Section,
    Species,
    Strain,
    StrainName,
)
from fungphy.database import session


def marker_is_valid(text: str) -> bool:
    """Tests if a given marker is an NCBI accession or nucleotide sequence."""
    if re.match(r"[A-Z]{1,2}[0-9]{5,8}", text):
        return True
    if set(text) == {"A", "C", "G", "T"}:
        return True
    return False


def parse_fasta(handle: IO) -> Dict[str, str]:
    """Parse sequences in a FASTA file."""
    sequences = {}
    header = ""
    for line in handle:
        try:
            line = line.decode().strip()
        except AttributeError:
            line = line.strip()
        if line.startswith(">"):
            header = line[1:]
            sequences[header] = ""
        else:
            if not header:
                continue
            sequences[header] += line
    return sequences


def efetch_sequences_request(headers: Collection) -> requests.Response:
    """Sends POST request for sequence retrieval from NCBI Entrez."""
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


def efetch_sequences(headers: Collection) -> Dict[str, str]:
    """Retrieves protein sequences from NCBI for supplied accessions."""
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


def query_dict(model, key="name"):
    return {getattr(obj, key): obj for obj in session.query(model)}


def parse_csv(fp):
    """Parse marker table, delimited by '|'.

    Assumes columns:
        Genus|Subgenus|Section|Epithet|Reference|MycoBank ID|Type|Ex-types|*markers

    Ex-types should be delimited by ' = ', as in taxonomy papers.

    Assumes there is a header row; this is how marker types are discovered.
    """
    reader = csv.reader(fp, delimiter="|")

    # Create new MarkerType objects if not in the database
    print("Validating provided marker types")
    marker_types = next(reader)[8:]
    marker_type_objects = query_dict(MarkerType)
    for marker in marker_types:
        if marker in marker_type_objects:
            continue
        print(f"  Creating new MarkerType: {marker}")
        marker_type_objects[marker] = MarkerType(name=marker)

    # 
    genera = query_dict(Genus)
    subgenera = query_dict(Subgenus)
    sections = query_dict(Section)

    all_markers = {}

    for row in reader:
        (
            genus,
            subgenus,
            section,
            epithet,
            reference,
            mycobank,
            herb,
            extype,
            *markers
        ) = row

        # Add any new Genera/Subgenera/Sections
        if genus not in genera:
            print(f"Creating new genus: {genus}")
            genera[genus] = Genus(name=genus)
        if subgenus not in subgenera:
            print(f"Creating new subgenus: {subgenus}")
            subgenera[subgenus] = Subgenus(name=subgenus, genus=genera[genus])
        if section not in sections:
            print(f"Creating new section: {section}")
            sections[section] = Section(name=section, subgenus=subgenera[subgenus])

        # Retrieve any species matches
        species = (
            session
            .query(Species)
            .filter(Species.epithet == epithet and Species.section == subgenera[subgenus])
            .first()
        )

        if not species:
            print(f"Creating new species: {genus} {epithet}")
            species = Species(
                type=herb,
                epithet=epithet,
                reference=reference,
                mycobank=mycobank,
            )
            sections[section].species.append(species)

        # Find a matching strain, if any
        numbers = extype.split(" = ")
        strain = (
            session
            .query(Strain)
            .join(Strain.strain_names)
            .filter(Strain.strain_names.any(StrainName.name.in_(numbers)))
            .first()
        )

        # If not, create one
        if not strain:
            print(f"  Creating new strain: {numbers}")
            strain = Strain(species=species, is_ex_type=type is not None)

        # Add any new strain names
        for number in numbers:
            if number in strain.names:
                continue
            print(f"  Adding new strain name: {number}")
            number = StrainName(name=number, strain=strain)

        # Add any new markers to:
        # - marker_type_objects, to attach to relevant MarkerType object
        # - strain.markers, to attach to relevant Strain object 
        # - all_markers, to retrieve sequences in batch from NCBI at end
        strain_markers = set(m.marker for m in strain.markers)
        for marker_type, accession in zip(marker_types, markers):
            if not accession or marker_type in strain_markers:
                continue
            print(f"  Adding new marker: {accession} [{marker_type}]")
            marker = Marker()

            # If the accession matches the pattern for an NCBI nucleotide accession,
            # mark it for download; otherwise, should just be nucleotide seqeunce.
            if re.match(r"[A-Z]{1,2}[0-9]{5,8}", accession):
                marker.accession = accession
                all_markers[accession] = marker
            elif set(accession) == {"A", "C", "G", "T"}:
                marker.sequence = accession
            else:
                print(f"Invalid marker: {accession}")
                continue

            for obj in (marker_type_objects[marker_type].markers, strain.markers):
                obj.append(marker)

    print(f"Fetching {len(all_markers)} sequences from NCBI")
    for accession, sequence in efetch_sequences(all_markers).items():
        all_markers[accession].sequence = sequence

    print("Saving updates to the database.")
    session.add_all(genera.values())
    session.commit()

    print("Done!")
