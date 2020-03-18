from flask import Flask
from flask_sqlalchemy import SQLAlchemy

DB_PATH = "fungphy.db"


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "secret key"

db = SQLAlchemy(app)


class Genus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __str__(self):
        return self.name


class Subgenus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    genus_id = db.Column(db.Integer, db.ForeignKey("genus.id"))
    genus = db.relationship("Genus", backref=db.backref("subgenera", lazy=True))

    def __str__(self):
        return self.name


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    subgenus_id = db.Column(db.Integer, db.ForeignKey("subgenus.id"))
    subgenus = db.relationship("Subgenus", backref=db.backref("sections", lazy=True))

    def __str__(self):
        return self.name


class Species(db.Model):
    """A species.

    This mirrors a species description from e.g. Samson 2014.

    i.e. `type` represents the herbarium/type officially tied to the name
    (culture permanently preserved in a metabolically inactive state), and
    `strains` holds strain designations for living isolates obtained from
    the type strain.

    For example:
        The type strain of Aspergillus nidulans is IMI 86806; the ex-types (living
        isolates) are CBS 589.65, NRRL 187, ATCC 10074, IHEM 3563, IMI 126691,
        IMI 86806, QM 1985, Thom 4640.5 and WB 187.

    Thus, markers tied to an Organism object may actually be deposited on NCBI
    under any of the linked names (type or ex-type).
    """

    id = db.Column(db.Integer, primary_key=True)

    type = db.Column(db.String)
    epithet = db.Column(db.String)
    mycobank = db.Column(db.String)
    reference = db.Column(db.String)

    section_id = db.Column(db.Integer, db.ForeignKey("section.id"))
    section = db.relationship("Section", backref=db.backref("species", lazy=True))

    def __str__(self):
        return self.name

    @property
    def name(self):
        return f"{self.genus} {self.epithet}"

    @property
    def genus(self):
        return str(self.section.subgenus.genus.name)

    @property
    def markers(self):
        return [strain.markers for strain in self.strains]


class Strain(db.Model):
    """A strain of a species."""

    id = db.Column(db.Integer, primary_key=True, nullable=True)

    is_ex_type = db.Column(db.Boolean)

    species_id = db.Column(db.Integer, db.ForeignKey("species.id"))
    species = db.relationship("Species", backref=db.backref("strains", lazy="subquery"))

    def __str__(self):
        return self.names

    @property
    def names(self):
        return " = ".join(sn.name for sn in self.strain_names)


class StrainName(db.Model):
    """A unique strain designation.

    This is separate to facilitate identical strains held in different culture
    collections.
    """

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String)

    strain_id = db.Column(db.Integer, db.ForeignKey("strain.id"))
    strain = db.relationship("Strain", backref=db.backref("strain_names", lazy=True))

    def __str__(self):
        return self.name


class Marker(db.Model):
    """A phylogenetic marker."""

    id = db.Column(db.Integer, primary_key=True)

    marker = db.Column(db.String)
    accession = db.Column(db.String)
    sequence = db.Column(db.String)

    strain_id = db.Column(db.Integer, db.ForeignKey("strain.id"))
    strain = db.relationship("Strain", backref=db.backref("markers", lazy=True))

    def __repr__(self):
        return f"{self.marker}:{self.accession}"

    def __str__(self):
        return f"{self.marker}: {self.accession or 'NoAccession'}"

    def fasta(self):
        return f">{self.strain.species.id}\n{self.sequence}"
