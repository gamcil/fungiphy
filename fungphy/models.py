from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from fungphy.database import Base


class Genus(Base):
    __tablename__ = "genus"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    subgenera = relationship("Subgenus", backref="genus", passive_deletes=True)

    def __str__(self):
        return self.name


class Subgenus(Base):
    __tablename__ = "subgenus"
    __table_args__ = (
        UniqueConstraint("genus_id", "name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String)

    genus_id = Column(Integer, ForeignKey("genus.id", ondelete="CASCADE"))
    sections = relationship("Section", backref="subgenus", passive_deletes=True)

    def __str__(self):
        return self.name or ""


class Section(Base):
    __tablename__ = "section"
    __table_args__ = (
        UniqueConstraint("subgenus_id", "name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String)

    subgenus_id = Column(Integer, ForeignKey("subgenus.id", ondelete="CASCADE"))
    species = relationship("Species", backref="section", passive_deletes=True)

    def __str__(self):
        return self.name or ""


class Species(Base):
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
    __tablename__ = "species"
    __table_args__ = (
        UniqueConstraint("section_id", "epithet"),
    )

    id = Column(Integer, primary_key=True)

    type = Column(String)
    epithet = Column(String)
    mycobank = Column(String)
    reference = Column(String)

    section_id = Column(Integer, ForeignKey("section.id", ondelete="CASCADE"))
    strains = relationship("Strain", backref="species", passive_deletes=True)

    # Adjacency list to allow synonymous species
    parent_id = Column(Integer, ForeignKey("species.id"))
    synonyms = relationship(
        "Species", backref=backref("parent", remote_side=[id])
    )

    def __str__(self):
        return self.name

    @property
    def name(self):
        return f"{self.genus} {self.epithet}"

    @property
    def genus(self):
        return str(self.section.subgenus.genus.name)

    @property
    def subgenus(self):
        return str(self.section.subgenus.name)

    @property
    def markers(self):
        return [strain.markers for strain in self.strains]


class Strain(Base):
    """A strain of a species."""

    __tablename__ = "strain"

    id = Column(Integer, primary_key=True, nullable=True)

    is_ex_type = Column(Boolean)

    species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"))
    strain_names = relationship("StrainName", backref="strain", passive_deletes=True)
    markers = relationship("Marker", backref="strain", passive_deletes=True)

    def __str__(self):
        return ", ".join(self.names)

    def get_marker(self, marker_type):
        for marker in self.markers:
            if marker.marker_type.name == marker_type:
                return marker
        return None

    @property
    def names(self):
        return [sn.name for sn in self.strain_names]

    @property
    def marker_types(self):
        return [marker.marker for marker in self.markers]


class StrainName(Base):
    """A unique strain designation.

    This is separate to facilitate identical strains held in different culture
    collections.
    """
    __tablename__ = "strain_name"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    strain_id = Column(Integer, ForeignKey("strain.id", ondelete="CASCADE"))

    def __str__(self):
        return self.name


class MarkerType(Base):
    __tablename__ = "marker_type"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

    markers = relationship("Marker", backref="marker_type", passive_deletes=True)

    def __repr__(self):
        return self.name


class Marker(Base):
    """A phylogenetic marker."""

    __tablename__ = "marker"

    id = Column(Integer, primary_key=True, nullable=True)
    accession = Column(String, unique=True)
    sequence = Column(String)

    marker_type_id = Column(Integer, ForeignKey("marker_type.id", ondelete="CASCADE"))
    strain_id = Column(Integer, ForeignKey("strain.id", ondelete="CASCADE")) 

    def __repr__(self):
        return f"{self.marker}:{self.accession}"

    def __str__(self):
        return f"{self.marker}: {self.accession or 'NoAccession'}"

    def fasta(self):
        return f">{self.strain_id}\n{self.sequence}"

    @property
    def marker(self):
        return self.marker_type.name
