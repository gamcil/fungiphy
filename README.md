# fungphy
Fungal marker-based phylogenetics toolkit

## Usage
Clone, set up virtualenv, install fungphy
```sh
git clone https://github.com/gamcil/fungphy.git
cd fungphy
python3 -m virtualenv venv
source venv/bin/activate
pip3 install -e .
```

Initialise database
```python3
from fungphy.database import db

db.create_all()
```

Scrape aspergilluspenicillium.org for Aspergillus, Penicillium & Talaromyces markers
```python
from fungphy import scraper

good, bad = scraper.scrape()

with open("table.csv", "w") as fp:
    for sp in good:
        columns = ",".join(sp)
        fp.write(columns) 
```

Import .csv
```python
# Genus|Species|Reference|MycoBank ID|Type|Ex-types|Subgenus|Section|*markers

from fungphy import importer

with open("table.csv") as fp:
    importer.parse_csv(fp)
```
