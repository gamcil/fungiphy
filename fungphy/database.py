from flask import Flask
from flask_sqlalchemy import SQLAlchemy

DB_PATH = "fungphy.db"


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "secret key"

db = SQLAlchemy(app)


class Marker(db.Model):
    """A phylogenetic marker."""

    id = db.Column(db.Integer, primary_key=True)

    marker = db.Column(db.String)
    accession = db.Column(db.String)
    sequence = db.Column(db.String)

    organism_id = db.Column(db.Integer, db.ForeignKey("organism.id"))
    organism = db.relationship("Organism", backref=db.backref("markers", lazy=True))

    def __str__(self):
        return f"{self.marker}: {self.accession or 'NoAccession'}"

    def fasta(self):
        return f">{self.organism.id}\n{self.sequence}"


class Organism(db.Model):
    """An organism.

    This mirrors a species description from e.g. Samson 2014.

    i.e. type_strain represents the herbarium/type officially tied to the name
    (culture permanently preserved in a metabolically inactive state), and
    ex_types holds strain designations for living isolates obtained from
    the type strain.

    For example:
        The type strain of Aspergillus nidulans is IMI 86806; the ex-types (living
        isolates) are CBS 589.65, NRRL 187, ATCC 10074, IHEM 3563, IMI 126691,
        IMI 86806, QM 1985, Thom 4640.5 and WB 187.

    Thus, markers tied to an Organism object may actually be deposited on NCBI
    under any of the linked names (type or ex-type).
    """

    id = db.Column(db.Integer, primary_key=True)

    species = db.Column(db.String)
    mycobank = db.Column(db.String)
    reference = db.Column(db.String)
    type_strain = db.Column(db.String)

    section_id = db.Column(db.Integer, db.ForeignKey("section.id"))
    section = db.relationship("Section", backref=db.backref("organisms", lazy=True))

    def __str__(self):
        return self.name

    @property
    def name(self):
        return f"{self.genus} {self.species}"

    @property
    def genus(self):
        return str(self.section.subgenus.genus.name)


class ExType(db.Model):
    """An ex-type (i.e. alive) designation."""

    id = db.Column(db.Integer, primary_key=True)
    strain = db.Column(db.String)

    organism_id = db.Column(db.Integer, db.ForeignKey("organism.id"))
    organism = db.relationship("Organism", backref=db.backref("extypes", lazy=True))

    def __str__(self):
        return self.strain


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    subgenus_id = db.Column(db.Integer, db.ForeignKey("subgenus.id"))
    subgenus = db.relationship("Subgenus", backref=db.backref("sections", lazy=True))

    def __str__(self):
        return self.name


class Subgenus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    genus_id = db.Column(db.Integer, db.ForeignKey("genus.id"))
    genus = db.relationship("Genus", backref=db.backref("subgenera", lazy=True))

    def __str__(self):
        return self.name


class Genus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __str__(self):
        return self.name
