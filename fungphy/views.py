import io
import time
import zipfile

from collections import defaultdict

from flask import Blueprint, render_template, jsonify, request, send_file
from flask import current_app as app
from sqlalchemy import func
from sqlalchemy.ext import compiler
from sqlalchemy.sql import ColumnElement

from fungphy.database import session
from fungphy import plot
from fungphy import phylogeny as phy
from fungphy.models import (
    Strain,
    Species,
    Section,
    Subgenus,
    Genus,
    Marker,
    MarkerType
)


view = Blueprint("view", __name__, template_folder="templates")


@view.route("/page", methods=["GET", "POST"])
@view.route("/page/<page>", methods=["GET", "POST"])
def index(page=None):
    query = (
        session.query(Strain)
        .join(Species, Section, Subgenus, Genus)
        .order_by(Strain.id, Genus.name, Species.epithet)
    )
    return render_template(
        "index.html",
        markers=[m.name for m in session.query(MarkerType)],
        strains=get_page(query, per_page=20, page=page)
    )


@view.route("/markers")
def get_marker_types():
    return {
        "markers": [
            marker[0]
            for marker in session.query(MarkerType.name)
        ]
    }


class group_fasta(ColumnElement):
    def __init__(self, header, sequence):
        self.header = header
        self.sequence = sequence
        self.type = header.type


@compiler.compiles(group_fasta, 'sqlite')
def compile_group_fasta(element, compiler, **kw):
    return 'group_concat(">" || {} || "\n" || {}, "\n")'.format(
        compiler.process(element.header),
        compiler.process(element.sequence),
    )


def form_zip(records):
    """Creates a .zip file in memory containing the given records.
    """
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, mode="w") as zip_file:
        for record in records:
            data = zipfile.ZipInfo(record["name"])
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zip_file.writestr(data, record["content"])
    memory.seek(0)
    return memory


# TODO: implement rate limiting using Flask-Limiter
#       e.g. limit this call to one per 10s or something
@view.route("/react/sequences", methods=["POST"])
def get_marker_sequences():
    if request.method != "POST":
        raise ValueError("Expected POST request to /react/sequences")

    content = request.get_json()

    form = content["format"] if "format" in content else "fasta"

    if not ("strains" in content and "markers" in content):
        raise KeyError("Expected strains and markers")

    if not (content["strains"] and content["markers"]):
        raise ValueError("Recieved empty content")

    query = (
        session.query(Marker)
        .join(MarkerType)
        .join(Strain)
        .filter(Strain.id.in_(content["strains"]))
        .filter(MarkerType.name.in_(content["markers"]))
        .order_by(Marker.marker_type_id)
    )

    if form == "json":
        records = {}

        for marker in query.order_by(Marker.marker_type_id):
            if marker.marker_type.name not in records:
                records[marker.marker_type.name] = []

            record = {
                "id": marker.id,
                "strain_id": marker.strain_id,
                "sequence": marker.sequence,
                "genus": marker.strain.species.section.subgenus.genus,
                "epithet": marker.strain.species.epithet,
                "strains": marker.strain.names,
            }

            records[marker.marker_type.name].append(record)

    elif form == "fasta":
        records = defaultdict(list)

        for marker in query:
            sequence = phy.Sequence(
                # marker.strain_id,
                f"{marker.strain.species.name} {marker.strain.names[0]}".replace(
                    " ", "_"
                ),
                marker.sequence
            )
            records[marker.marker_type.name].append(sequence)

        if content["aligned"]:
            for marker, sequences in records.items():
                records[marker] = phy.align_sequences(
                    sequences,
                    marker,
                    tool="muscle",
                    trim_msa=True
                )

            if content["concatenated"]:
                msa = phy.MultiMSA([msa for msa in records.values()])
                archive = form_zip([
                    {"name": "markers.fna", "content": msa.fasta()},
                    {"name": "partitions.text", "content": msa.raxml_partitions()},
                ])
            else:
                msas = [
                    {"name": f"{marker}.fna", "content": msa.fasta()}
                    for marker, msa in records.items()
                ]
                archive = form_zip(msas)
        else:
            fastas = [
                {
                    "name": f"{marker}.fna",
                    "content": "\n".join(s.fasta() for s in sequences)
                }
                for marker, sequences in records.items()
            ]
            archive = form_zip(fastas)

    return send_file(
        archive,
        mimetype="application/zip",
        as_attachment=True,
        attachment_filename="fungiphy.zip",
    )


@view.route("/react/align", methods=["POST"])
def get_marker_alignment():
    content = request.get_json()

    if not content:
        return "No content received", 404

    ids = content["ids"].split(",")
    markers = content["markers"].split(",")

    strains = plot.get_species(strain_ids=ids)
    msa = plot.align_strains(strains, markers, trim_msa=True)

    return msa.fasta()


@view.route("/strains")
def get_strains(strain_ids=None):
    query = (
        session.query(Strain)
        .join(Species, Section, Subgenus, Genus)
        .order_by(Strain.id, Genus.name, Species.epithet)
    )

    if strain_ids:
        query = query.filter(Strain.id.in_(strain_ids))

    return {
        "strains": [
            {
                "id": strain.id,
                "mycobank": strain.species.mycobank,
                "subgenus": strain.species.section.subgenus,
                "section": strain.species.section.name,
                "genus": strain.species.genus,
                "epithet": strain.species.epithet,
                "strains": [sn.name for sn in strain.strain_names],
                "holotype": strain.species.type,
                "is_ex_type": strain.is_ex_type,
                "markers": {m.marker: m.accession for m in strain.markers},
                **{m.marker: m.accession for m in strain.markers}
            }
            for strain in query
        ]
    }
