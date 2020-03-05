#!/usr/bin/env python3

import phylogeny
import sys

print("Generating multiMSA")
msa = phylogeny.MultiMSA.from_fasta_files(sys.argv[2:], tool=sys.argv[1])

print("Writing concatenated MSA to combined.msa")
with open("combined.msa", "w") as fp:
    fp.write(msa.fasta())

print("Writing partitions to partitions.txt")
with open("partitions.txt", "w") as fp:
    fp.write(msa.raxml_partitions())

for m in msa:
    print(f"Writing {m.name} MSA to {m.name}.msa")
    with open(f"{m.name}.msa", "w") as fp:
        fp.write(m.fasta())
