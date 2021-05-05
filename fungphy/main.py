import json
import argparse

from pathlib import Path

from fungphy import plot
from fungphy import phylogeny as phy


def paths_exist(paths):
    found = False
    if isinstance(paths, str):
        found = Path(paths).exists()
    else:
        for path in paths:
            if Path(path).exists():
                found = True
    if not found:
        raise FileNotFoundError(f"Could not find: {path}")


def get_parser():
    parser = argparse.ArgumentParser("fungphy")

    filters = parser.add_argument_group("Species selection")
    filters.add_argument("-ge", "--genera", nargs="+", help="Filter by genus")
    filters.add_argument("-sg", "--subgenera", nargs="+", help="Filter by subgenus")
    filters.add_argument("-se", "--sections", nargs="+", help="Filter by section")
    filters.add_argument("-sp", "--species", nargs="+", help="Filter by species name")
    filters.add_argument("-st", "--strains", nargs="+", help="Filter by strain number")
    filters.add_argument("-si", "--strain_ids", nargs="+", help="Filter by strain ID")
    filters.add_argument("-js", "--json_filters", help="Filters in JSON format")
    filters.add_argument("-m", "--markers", nargs="+", help="Phylogenetic markers")

    fasta = parser.add_argument_group("FASTA")
    fasta.add_argument("-fi", "--fasta_in", nargs="+", help="Input FASTA file/s")
    fasta.add_argument("-fo", "--fasta_out", help="Output FASTA file template")

    aligns = parser.add_argument_group("Marker alignment")
    aligns.add_argument("-mi", "--msa_in", nargs="+", help="Input MSA file/s")
    aligns.add_argument("-mo", "--msa_out", help="Output MSA file template")
    aligns.add_argument("-mt", "--msa_tool", default="mafft", choices=["mafft", "muscle"], help="Alignment program")
    aligns.add_argument("-tm", "--trim_msa", action="store_true", help="Trim sequence alignments")
    aligns.add_argument("-pi", "--partition_in", help="Input partition file (RAxML format)")
    aligns.add_argument("-po", "--partition_out", help="Output partition file (RAxML format)")

    fasttree = parser.add_argument_group("FastTree settings")
    fasttree.add_argument("-ft", "--fasttree", action="store_true", help="Generate a tree using FastTree")
    fasttree.add_argument("--ft_gtr", action="store_true", help="Use GTR model")
    fasttree.add_argument("--ft_gamma", action="store_true", help="Use gamma model")

    tree = parser.add_argument_group("Tree visualisation")
    tree.add_argument("-ti", "--tree_in", nargs="+", help="Input tree file/s")
    tree.add_argument("-to", "--tree_out", help="Output tree file")
    tree.add_argument("-ts", "--tree_style", nargs="+", help="ETE3 Treestyle parameters in JSON format")
    tree.add_argument("-tb", "--tree_bold", nargs="+", help="Use bold leaf labels")
    tree.add_argument("-tt", "--tree_type", nargs="+", help="Use type strain numbers")
    tree.add_argument("-tf", "--tree_flip", action="store_true", help="Reverse tree ordering")
    tree.add_argument("-og", "--outgroup", help="Outgroup species")

    table = parser.add_argument_group("Marker accession table")
    table.add_argument("-bi", "--table_in", help="Input table file")
    table.add_argument("-bo", "--table_out", help="Output table file")
    table.add_argument("-bd", "--table_delimiter", help="Delimiter used in table file")
    table.add_argument("-bh", "--table_headers", action="store_true", help="Table has headers")

    return parser


def fungphy(
    genera=None,
    subgenera=None,
    sections=None,
    species=None,
    strains=None,
    strain_ids=None,
    json_filters=None,
    markers=None,
    fasta_in=None,
    fasta_out=None,
    msa_in=None,
    msa_out=None,
    msa_tool="mafft",
    trim_msa=True,
    partition_in=None,
    partition_out=None,
    fasttree=False,
    ft_gtr=False,
    ft_gamma=False,
    tree_in=None,
    tree_out=None,
    tree_style=None,
    tree_bold=None,
    tree_type=None,
    tree_flip=False,
    outgroup=None,
    table_in=None,
    table_out=None,
    table_delimiter=",",
    table_headers=False,
):
    strains = None
    table, msa, tree = None, None, None

    if tree_in:
        print(f"Loading tree from: {tree_in}")
        tree = plot.read_trees_from_paths(
            tree_in,
            bold=tree_bold,
            types=tree_type,
            outgroup=outgroup,
            merge=True
        )
    else:
        if table_in:
            print(f"Loading table from: {table_in}")
            with open(table_file) as fp:
                table = plot.Summary.from_table(
                    fp,
                    delimiter=table_delimiter,
                    has_headers=table_headers
                )

        if fasta_in and not msa_in:
            print(f"Generating MultiMSA from FASTA files: {fasta_in}")
            msa = phy.MultiMSA.from_fasta_files(
                fasta_in,
                names=markers,
                align=True,
                tool=msa_tool,
                trim_msa=trim_msa
            )

        elif msa_in:
            if len(msa_in) == 1 and partition_in:
                print(f"Loading MultiMSA from: {msa_in} and {partition_in}")
                msa = phy.MultiMSA.from_partitioned(msa_in, partition_in)
            elif len(msa_in) > 1 and markers:
                print(f"Loading MultiMSA from: {msa_in}")
                msa = phy.MultiMSA.from_fasta_files(msa_in, names=markers)

        else:
            if json_filters:
                print(f"Finding strains matching filters in: {json_filters}")
                with open(json_filters) as fp:
                    filters = json.load(fp)

                for field in ["markers", "groups"]:
                    if field not in filters:
                        raise ValueError(f"Could not find required field: {field}")

                if not outgroup:
                    outgroup = filters.pop("outgroup", None)

                markers = filters["markers"]
                strains = [
                    strain
                    for group in filters["groups"]
                    for strain in plot.get_species(markers=markers, **group)
                ]
            else:
                if not any([genera, subgenera, sections, species, strains, strain_ids]):
                    raise ValueError("No filters have been entered")

                print("Finding strains matching filters")
                strains = plot.get_species(
                    genera=genera,
                    subgenera=subgenera,
                    sections=sections,
                    species=species,
                    strains=strains,
                    strain_ids=strain_ids,
                    markers=markers,
                )

            print(f"Found {len(strains)} strains matching filters")
            msa = plot.align_strains(strains, markers=markers, trim_msa=trim_msa)

        if not strains:
            strains = plot.get_species(strain_ids=msa.headers)

        if not table:
            table = plot.Summary.from_strains(strains, markers=markers)

        if fasttree and not tree:
            print("Generating tree with FastTree")
            tree = plot.read_tree(
                phy.fasttree(msa, gtr=ft_gtr, gamma=ft_gamma),
                bold=tree_bold,
                types=tree_type,
                outgroup=outgroup,
            )

        if fasta_out:
            for marker in markers:
                name = fasta_out.replace("*", marker)
                sequences = plot.get_marker_sequences(strains, marker)
                fasta = "\n".join(s.fasta() for s in sequences)

                print(f"Writing unaligned {marker} sequences to: {name}")
                with open(name, "w") as fp:
                    fp.write(fasta)

        if msa_out:
            if "*" in msa_out:
                for m in msa:
                    name = msa_out.replace("*", m.name)
                    print(f"Writing aligned {m.name} sequences to: {name}")
                    with open(name, "w") as fp:
                        fp.write(m.fasta())
            else:
                print(f"Writing combined alignment to: {msa_out}")
                with open(msa_out, "w") as fp:
                    fp.write(msa.fasta())

        if partition_out:
            print(f"Writing partitions to: {partition_out}")
            with open(partition_out, "w") as fp:
                fp.write(msa.raxml_partitions())

        if table_out:
            print(f"Writing marker accession table to: {table_out}")
            with open(table_out, "w") as fp:
                fp.write(
                    table.format(delimiter=table_delimiter, show_headers=table_headers)
                )

        if tree_out:
            print(f"Writing Newick tree to: {tree_out}")
            tree.write(format=0, outfile=tree_out)

    if tree:
        if tree_flip:
            for node in tree.traverse():
                node.swap_children()
        if tree_style:
            ts = plot.get_tree_style(**tree_style)
            plot.show(tree, ts=ts)
        else:
            plot.show(tree)

    return table, msa, tree


def handle_file_load_save_args(items):
    args, kwargs = handle_nested_kwargs(items)

    if args and not kwargs:
        return [], args

    markers, paths = [], []

    for key, value in kwargs.items():
        markers.append(key)
        paths.append(value)

    return markers, paths


def handle_nested_kwargs(items):
    args, kwargs = [], {}
    for item in items:
        try:
            key, value = item.split("=")
        except ValueError:
            args.append(item)
            continue
        if value.isdigit():
            value = float(value)
        kwargs[key] = value
    return args, kwargs


def set_markers(args, markers, source="fsa"):
    if args.markers:
        if markers and args.markers != markers:
            raise ValueError(f"Markers in -{source} do not match --markers")
        # else do nothing, raise exception in fungphy() if still no markers
    else:
        setattr(args, "markers", markers)


def validate_args(args):
    if args.fasta_in:
        markers, paths = handle_file_load_save_args(args.fasta_in)
        set_markers(args, markers)
        setattr(args, "fasta_in", paths)

    if args.msa_in:
        markers, paths = handle_file_load_save_args(args.msa_in)
        set_markers(args, markers, source="msa")
        setattr(args, "msa_in", paths)

    if args.tree_style:
        _, ts_kwargs = handle_nested_kwargs(args.tree_style)
        setattr(args, "tree_style", ts_kwargs)


def main():
    parser = get_parser()
    args = parser.parse_args()
    validate_args(args)
    fungphy(**vars(args))


if __name__ == "__main__":
    main()
