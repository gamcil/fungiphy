"""Plot phylogenetic tree using ETE toolkit."""

from ete3 import NodeStyle, Tree, TreeStyle, faces
from ete3.treeview.faces import DynamicItemFace, TextFace
from PyQt5 import QtCore
from PyQt5.QtGui import QPen
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem

import fungphy.phylogeny as phy
from fungphy.database import Genus, Organism, Section, Subgenus, db


def get_species(genera=None, subgenera=None, sections=None, species=None, oids=None):
    """Query database for species."""

    q = Organism.query.join(Section, Subgenus, Genus)

    if genera:
        q = q.filter(Genus.name.in_(genera))

    if subgenera:
        q = q.filter(Subgenus.name.in_(subgenera))

    if sections:
        q = q.filter(Section.name.in_(sections))

    if species:
        q = q.filter(Organism.species.in_(species))

    if oids:
        q = q.filter(Organism.id.in_(oids))

    return q.all()


def get_marker_sequences(organisms, marker, header_source="organism", header_attr="id"):
    if header_source not in ("organism", "marker"):
        raise ValueError("Expected 'organism' or 'marker'")

    return [
        phy.Sequence(
            header=getattr(o if header_source == "organism" else m, header_attr),
            sequence=m.sequence,
        )
        for o in organisms
        for m in o.markers
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
    def make(cls, organisms, markers, delimiter=","):
        accessions = []
        for marker in markers:
            a = [
                m.header
                for m in get_marker_sequences(
                    organisms, marker, header_source="marker", header_attr="accession"
                )
            ]
            accessions.append(a)

        headers = ["Organism", *markers]
        rows = [[o.name, *accs] for o, *accs in zip(organisms, *accessions)]
        return cls(headers, rows)

    def format(self, delimiter=",", show_headers=False):
        def join(array):
            return delimiter.join(str(element) for element in array)
        rows = [self.header, *self.rows] if show_headers else self.rows
        return "\n".join(join(row) for row in rows)


def align_organisms(organisms, markers=None, **kwargs):
    """Align markers from a list of Organism objects."""

    if not markers:
        raise ValueError("Expected marker")

    msas = []

    for marker in markers:
        print(f"Aligning {marker}")
        sequences = get_marker_sequences(organisms, marker)
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

    if hasattr(node, "multi_support"):
        multi = "/".join(
            f"{sup:g}" if isinstance(sup, (float, int)) else sup
            for sup in node.multi_support
        )
        support = TextFace(multi, fsize=7)
    else:
        support = TextFace(f"{node.support:g}", fsize=7)

    support.margin_right = 4
    support.margin_top = 16

    faces.add_face_to_node(support, node, position="float", column=1)


def get_tree_style():
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
    return style


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

    def add_support(node, support):
        try:
            node.multi_support.append(support)
        except AttributeError:
            node.add_feature("multi_support", [node.support, support])

    for node in new.get_descendants():
        leaves = node.get_leaf_names()
        found_match = False
        if not leaves:
            continue

        for other in others:
            for node2 in other.get_descendants():
                if leaves != node2.get_leaf_names():
                    continue
                add_support(node, node2.support)
                found_match = True

            if not found_match:
                add_support(node, "-")
    return new


def label_maker(node, organism, bold=False, type_strain=False):
    """Form correctly formatted leaf label."""

    face = QGraphicsTextItem()

    name = f"<i>{organism.genus[0]}. {organism.species}</i>  {organism.type_strain}"

    if type_strain:
        name += "<sup>T</sup>"

    if bold:
        name = f"<b>{name}</b>"

    face.setHtml(name)

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


def read_tree(nwk, outgroup=None, bold=None, nontypes=None, min_support=2):
    """Read in a Newick format tree."""

    tree = Tree(nwk)

    oids = list(tree.iter_leaf_names())
    organisms = {str(o.id): o for o in get_species(oids=oids)}

    for leaf in tree.iter_leaves():
        o = organisms[leaf.name]

        # Generate nice leaf labels using HTML
        # However, requires editing in .pdf format rather than .svg, which chunks
        # text into separate parts and messes up spacing
        label = DynamicItemFace(
            label_maker,
            organism=o,
            bold=True if bold and o.species in bold else False,
            type_strain=not nontypes or (nontypes and o.species not in nontypes),
        )

        leaf.add_face(label, 0)

    if outgroup:
        tree.set_outgroup(outgroup)

    return tree


def read_tree_from_path(path, **kwargs):
    with open(path) as fp:
        nwk = fp.read()
    return read_tree(nwk, **kwargs)


def read_trees_from_paths(paths, merge=False, **kwargs):
    trees = []
    for path in paths:
        tree = read_tree(path, **kwarg)
        trees.append(tree)
    if merge:
        return merge_support_values(trees)
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
    oids=None,
    markers=None,
    bold=None,
    nontypes=None,
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
            nontypes=nontypes,
            outgroup=outgroup,
        )
        if show_tree:
            show(tree)

    return table, msa, tree
