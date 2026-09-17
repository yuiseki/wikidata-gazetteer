# wikidata-gazetteer

Every geographic item in Wikidata, with its names in every language Wikidata
has them in, its position, its place in the administrative hierarchy, and a
count of how many Wikipedias write about it.

Wikidata holds the deepest multilingual place-name data of any openly licensed
source, and it is CC0. The pieces are published separately elsewhere, as full
entity dumps, as RDF triples, and as per-language label tables. Nobody had
joined them into a gazetteer.

## What is here

    src/extract.py         reads the Wikidata JSON dump, emits one JSONL record
                           per geographic item
    src/build_parquet.py   turns that into the two published tables
    data/                  the dataset card, its licence, and provenance

## Selection

An item is in if it carries `P625` (coordinate location) or `P1566` (GeoNames
ID). Both are testable as substrings before any JSON is parsed, which is what
keeps a pass over the 103 GB compressed dump to about 100 minutes; the binding
constraint is decompression, not parsing.

This selects things that have a location, not settlements. Mountains, rivers,
buildings and stations are in alongside cities and countries. `instance_of`
carries the Wikidata class so a reader can narrow it.

## Building

    python3 src/extract.py < dump.json > places.jsonl        # or pipe from lbzip2
    python3 src/build_parquet.py --jsonl places.jsonl.gz --out parquet/

The extract step expects the dump on stdin:

    lbzip2 -dc -n 24 wikidata-all.json.bz2 \
      | grep -aF -e '"P625"' -e '"P1566"' \
      | python3 src/extract.py \
      | pigz > places.jsonl.gz

## Licence

Code is Apache-2.0. Data is CC0-1.0, inherited from Wikidata. See `data/LICENSE`.
