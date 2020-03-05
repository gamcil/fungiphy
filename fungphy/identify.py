"""Workflow for identifying and adding markers from new species.

1. Search HMM database of known markers against assembly
2. Extract env coordinates from assembly per best marker hit
3. Insert sequences, insert organism, get row IDs
4. Insert junction table
"""


import subprocess
