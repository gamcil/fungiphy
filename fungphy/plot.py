"""Plot phylogenetic tree using ETE toolkit."""

import csv

from collections import defaultdict

from ete3 import Tree, TreeStyle, faces, NodeStyle
from ete3.treeview.faces import DynamicItemFace, TextFace
from PyQt5 import QtCore
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem

import fungphy.phylogeny as phy
from fungphy.database import session
from fungphy.models import (
    Genus,
    Section,
    Species,
    Strain,
    StrainName,
    Subgenus,
    Marker,
    MarkerType,
)


def get_species(
    genera=None,
    subgenera=None,
    sections=None,
    species=None,
    strains=None,
    strain_ids=None,
    markers=None,
    types=False,
):
    """Query database for species."""
    q = session.query(Strain).join(Species, Section, Subgenus, Genus)
    if genera:
        q = q.filter(Genus.name.in_(genera))
    if subgenera:
        q = q.filter(Subgenus.name.in_(subgenera))
    if sections:
        q = q.filter(Section.name.in_(sections))
    if species:
        q = q.filter(Species.epithet.in_(species))
    if strains:
        q = q.filter(
            Strain.strain_names.any(StrainName.name.in_(strains))
            | Species.type.in_(strains)
        )
    if strain_ids:
        q = q.filter(Strain.id.in_(strain_ids))
    if types:
        q = q.filter(Strain.is_ex_type==True)
    if markers:
        mq = session.query(MarkerType).filter(MarkerType.name.in_(markers)).all()
        if len(mq) != len(markers):
            raise ValueError("Marker mismatch; misspelled marker name?")
        q = q.filter(*[Strain.markers.any(marker_type=m) for m in mq])
    return q.all()


def get_marker_sequences(strains, marker, header_source="organism", header_attr="id"):
    if header_source not in ("organism", "marker"):
        raise ValueError("Expected 'organism' or 'marker'")

    return [
        phy.Sequence(
            header=getattr(s if header_source == "organism" else m, header_attr),
            sequence=m.sequence,
        )
        for s in strains
        for m in s.markers
        if m.marker == marker
    ]


class Summary:
    """A summary table."""

    def __init__(self, headers=None, rows=None):
        self.headers = headers if headers else []
        self.rows = rows if rows else []

    def __iter__(self):
        return iter(self.rows)

    @classmethod
    def from_strains(cls, strains, markers, delimiter=","):
        accessions = []
        for marker in markers:
            a = [
                m.header
                for m in get_marker_sequences(
                    strains, marker, header_source="marker", header_attr="accession"
                )
            ]
            accessions.append(a)

        headers = ["ID", "Genus", "Subgenus", "Section", "Species", "Strain", *markers]
        rows = [
            [s.id, s.species.genus, s.species.subgenus, s.species.section.name,
             s.species.epithet, s.names, *accs]
            for s, *accs in zip(strains, *accessions)
        ]
        return cls(headers, rows)

    @classmethod
    def from_table(cls, fp, has_headers=False, delimiter=","):
        headers, rows = [], []

        if has_headers:
            headers = next(fp).strip().split(delimiter)

        for row in fp:
            row = row.strip().split(delimiter)
            rows.append(row)

        return cls(headers=headers, rows=rows)

    def format(self, delimiter=",", show_headers=False):
        def join(array):
            return delimiter.join(str(element) for element in array)

        rows = [self.headers, *self.rows] if show_headers else self.rows
        return "\n".join(join(row) for row in rows)


def match_strain_markers(strains, markers):
    """Return subset of Strain objects possessing all specified markers."""
    good, bad = [], []
    for strain in strains:
        if set(markers).issubset(strain.marker_types):
            good.append(strain)
        else:
            bad.append(strain)
    return good, bad


def align_strains(strains, markers, **kwargs):
    """Align markers from a list of Organism objects."""
    msas = []
    for marker in markers:
        print(f"Aligning {marker}")
        sequences = get_marker_sequences(strains, marker)
        msa = phy.align_sequences(sequences, name=marker, **kwargs)
        msas.append(msa)
    return phy.MultiMSA(msas)


def layout(node):
    """Layout function for TreeStyle object.

    1. Hides dots at tree nodes
    2. Fixes line width to 1px for better rendering
    3. Draws support values without introducing gaps between branches

    Support values are not drawn if:
        1) node is a leaf, or is the tree root
        2) tree is rooted and node is a child of the root
           (a tree is rooted if only 2 branches under the root node)
    """

    node.img_style["size"] = 0
    node.img_style["hz_line_width"] = 1
    node.img_style["vt_line_width"] = 1

    if node.is_leaf() or node.is_root():
        return

    root = node.get_tree_root().get_children()
    if len(root) == 2 and node in root:
        return

    def format_support(value):
        support = "*" if value in (100, 1.0) else f"{value:g}"
        return support

    if hasattr(node, "multi_support"):
        multi = "/".join(
            format_support(sup) if isinstance(sup, (float, int)) else sup
            for sup in node.multi_support
        )
        support = TextFace(multi, fsize=7)
    else:
        support = TextFace(format_support(node.support), fsize=7)

    support.margin_right = 4
    support.margin_bottom = 15

    faces.add_face_to_node(support, node, position="float", column=1)


def get_tree_style(**kwargs):
    style = TreeStyle()
    style.layout_fn = layout
    style.allow_face_overlap = True
    style.branch_vertical_margin = 5
    style.complete_branch_lines_when_necessary = False
    style.draw_aligned_faces_as_table = False
    style.scale = 1500
    style.scale_length = 0.05
    style.show_branch_support = False
    style.show_leaf_name = False

    for key, value in kwargs.items():
        if value == "True":
            value = True
        else:
            try:
                value = float(value)
            except ValueError:
                pass
        setattr(style, key, value)

    return style


def add_support(node, support):
    try:
        node.multi_support.append(support)
    except AttributeError:
        node.add_feature("multi_support", [node.support, support])


def merge_support_values(trees):
    """Combine support values for common nodes in two Trees.

    Iterates all nodes in both trees, and combines support values if child leaves
    are identical. Note that as ETE forces the `support` attribute to be a float,
    the combined values are stored under `multi_support`.

    e.g. Posterior probability % = 100, bootstrap = 95 => 100/95
    """

    if any(not isinstance(t, Tree) for t in trees):
        raise TypeError("Expected ete3.Tree objects")

    base, *others = trees

    new = base.copy()
    new.add_feature("base_trees", trees)

    for node in new.get_descendants():
        leaves = node.get_leaf_names()
        found_match = False
        if not leaves:
            continue
        for other in others:
            for node2 in other.get_descendants():
                if set(leaves) != set(node2.get_leaf_names()):
                    continue
                add_support(node, node2.support)
                found_match = True
            if not found_match:
                add_support(node, "-")

    return new


def label_maker(node, label):
    """Form correctly formatted leaf label."""

    face = QGraphicsTextItem()
    face.setHtml(label)

    # Create parent RectItem with TextItem in center
    fbox = face.boundingRect()
    rect = QGraphicsRectItem(0, 0, fbox.width(), fbox.height())
    rbox = rect.boundingRect()
    face.setPos(rbox.x(), rbox.center().y() - fbox.height() / 2)

    # Remove border
    rect.setPen(QPen(QtCore.Qt.NoPen))

    # Set as parent item so DynamicItemFace can use .rect() method
    face.setParentItem(rect)

    return rect


def add_section_annotations(tree: Tree) -> None:
    """Annotates taxonomic sections.

    Pretty hacky. Finds first common ancestor of leaf nodes per section,
    then sets a bgcolor. If a section contains a single node, then only
    that node is styled. Also adds a section label, but exact position
    is determined by which node gets found first using search_nodes().

    Relies on accurate section annotation - FP strains were set to Talaromyces
    which breaks this.
    """
    leaves = tree.get_leaf_names()
    sections = defaultdict(list)
    for strain in session.query(Strain).filter(Strain.id.in_(leaves)):
        if "FP" in strain.species.epithet:
            continue
        sections[strain.species.section.name].append(str(strain.id))

    index = 0
    colours = [
        "LightSteelBlue",
        "Moccasin",
        "DarkSeaGreen",
        "Khaki",
        "LightSalmon",
        "Turquoise",
        "Thistle"
    ]

    for section, ids in sections.items():
        # Find MRCA and set bgcolor of its node
        style = NodeStyle()
        style["bgcolor"] = colours[index]
        if len(ids) == 1:
            node = tree.search_nodes(name=ids[0])[0]
        else:
            node = tree.get_common_ancestor(*ids)
        node.set_style(style)

        # Grab first node found in this section, and add section label
        node = tree.search_nodes(name=ids[0])[0]
        face = faces.TextFace(section, fsize=20)
        node.add_face(face, column=1, position="aligned")

        # Wraparound colour scheme
        index += 1
        if index > len(colours) - 1:
            index = 0


def add_leaf_labels(tree, bold=None, types=None):
    """Form leaf labels for an ETE3 Tree object.

    Generates nice leaf labels using HTML formatting. Trying to use multiple separate
    faces with separate columns results in weird spacing when exporting/editing.

    However, requires editing in .pdf format rather than .svg.
    """

    leaves = tree.get_leaf_names()

    strains = {
        str(strain.id): strain
        for strain in session.query(Strain).filter(Strain.id.in_(leaves))
    }

    for leaf in tree.iter_leaves():
        s = strains[leaf.name]

        genus = s.species.genus
        epithet = s.species.epithet

        use_type = True if types and epithet in types else False
        use_bold = True if bold and epithet in bold else False

        name = s.strain_names[0].name if not use_type else s.species.type
        label = f"<i>{genus[0]}. {epithet}</i>  {name}"

        if s.is_ex_type and not use_type:
            label += "<sup>T</sup>"
        if use_bold:
            label = f"<b>{label}</b>"

        face = DynamicItemFace(label_maker, label=label)
        leaf.add_face(face, 0)


def set_outgroup(tree, species):
    """Set an outgroup on an ETE3 Tree object."""

    leaves = tree.get_leaf_names()

    q = session.query(Strain.id).filter(Strain.id.in_(leaves)).join(Species)

    if isinstance(species, str):
        q = q.filter(Species.epithet == species)
    else:
        q = q.filter(Species.epithet.in_(species))

    count = q.count()

    if count == 0:
        raise ValueError("Found no match for given species")

    if count == 1:
        node = str(q.first()[0])
        tree.set_outgroup(node)

    elif count > 1:
        node = tree.get_common_ancestor(*[str(record[0]) for record in q])
        tree.set_outgroup(node)


def read_tree(nwk, outgroup=None, bold=None, types=None, label_leaves=True):
    """Read in a Newick format tree."""
    tree = Tree(nwk)
    if label_leaves:
        add_section_annotations(tree)
        add_leaf_labels(tree, bold=bold, types=types)
    if outgroup:
        set_outgroup(tree, outgroup)
    return tree


def read_tree_from_path(path, **kwargs):
    with open(path) as fp:
        nwk = fp.read()
    return read_tree(nwk, **kwargs)


def read_trees_from_paths(paths, merge=False, bold=None, types=None, outgroup=None):
    trees = []
    for path in paths:
        if merge:
            tree = read_tree(path, outgroup=outgroup, label_leaves=False)
        else:
            tree = read_tree(path, outgroup=outgroup, bold=bold, types=types)
        trees.append(tree)
    if merge:
        tree = merge_support_values(trees)
        add_section_annotations(tree)
        add_leaf_labels(tree, bold=bold, types=types)
        return tree
    if len(paths) == 1:
        return trees[0]
    return trees


def show(tree, ts=None):
    if not ts:
        ts = get_tree_style()
    tree.show(tree_style=ts)


def _run(
    genera=None,
    subgenera=None,
    sections=None,
    species=None,
    strains=None,
    oids=None,
    markers=None,
    bold=None,
    types=None,
    outgroup=None,
    trim_msa=False,
    run_fasttree=False,
    gtr=True,
    gamma=True,
    show_tree=False,
    delimiter=",",
):
    table, msa, tree = None, None, None

    print("Fetching organisms from FungPhy")
    orgs = get_species(
        genera=genera,
        subgenera=subgenera,
        sections=sections,
        species=species,
        strains=strains,
        oids=oids,
    )

    print("Generating summary table")
    table = Summary.make(orgs, markers=markers, delimiter=delimiter)

    print("Aligning markers")
    msa = align_organisms(orgs, markers=markers, trim_msa=trim_msa)

    if run_fasttree:
        print("Generating tree with FastTree")
        tree = read_tree(
            phy.fasttree(msa, gtr=gtr, gamma=gamma),
            bold=bold,
            types=types,
            outgroup=outgroup,
        )
        if show_tree:
            show(tree)

    return table, msa, tree
