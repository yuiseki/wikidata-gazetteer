#!/usr/bin/env python3
"""Turn the extracted JSONL into the two Parquet tables that get published.

Two tables rather than one, because the shapes differ. A place has one
position and one hierarchy; it has many names. Keeping the names in their own
table means the coordinates are not repeated 62 million times, and it gives
each name its own row with its language beside it, which is the form a
gazetteer is actually read in.

    places : one row per place
    names  : one row per name, joined back on qid

Written in batches so that a table far larger than memory still builds.
"""
import argparse
import gzip
import json
import os

import pyarrow as pa
import pyarrow.parquet as pq

BATCH = 500_000

PLACES = pa.schema([
    ("qid", pa.string()),
    ("lat", pa.float64()),
    ("lon", pa.float64()),
    ("country", pa.string()),        # P17, first value
    ("parent", pa.string()),         # P131, first value
    ("instance_of", pa.list_(pa.string())),   # P31, all values
    ("located_in", pa.list_(pa.string())),    # P131, all values
    ("geonames_id", pa.string()),    # P1566, first value
    ("osm_relation", pa.string()),   # P402, first value
    ("capital", pa.string()),        # P36, first value
    ("iso_3166_2", pa.string()),     # P300, first value
    ("contains", pa.list_(pa.string())),      # P150, all values
    ("population", pa.float64()),    # P1082, the preferred or latest statement
    ("area", pa.float64()),          # P2046
    ("sitelinks", pa.int32()),
    ("n_names", pa.int32()),
])

NAMES = pa.schema([
    ("qid", pa.string()),
    ("lang", pa.string()),
    ("name", pa.string()),
    ("kind", pa.string()),           # label or alias
])


def first(values):
    return values[0] if values else None


def write(writer, schema, columns):
    writer.write_table(pa.Table.from_pydict(columns, schema=schema))


def empty(schema):
    return {field.name: [] for field in schema}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--out", required=True, help="directory for the parquet files")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    pw = pq.ParquetWriter(os.path.join(args.out, "places.parquet"), PLACES,
                          compression="zstd")
    nw = pq.ParquetWriter(os.path.join(args.out, "names.parquet"), NAMES,
                          compression="zstd")
    p, n = empty(PLACES), empty(NAMES)
    places = names = 0

    with gzip.open(args.jsonl, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            qid = r["qid"]
            labels, aliases = r["labels"], r["aliases"]
            count = len(labels) + sum(len(v) for v in aliases.values())

            p["qid"].append(qid)
            p["lat"].append(r["lat"])
            p["lon"].append(r["lon"])
            p["country"].append(first(r["p17"]))
            p["parent"].append(first(r["p131"]))
            p["instance_of"].append(r["p31"])
            p["located_in"].append(r["p131"])
            p["geonames_id"].append(first(r["geonames"]))
            p["osm_relation"].append(first(r["osm"]))
            p["capital"].append(first(r["p36"]))
            p["iso_3166_2"].append(first(r["iso3166_2"]))
            p["contains"].append(r["p150"])
            p["population"].append(r["population"])
            p["area"].append(r["area"])
            p["sitelinks"].append(r["sitelinks"])
            p["n_names"].append(count)
            places += 1

            for lang, value in labels.items():
                n["qid"].append(qid); n["lang"].append(lang)
                n["name"].append(value); n["kind"].append("label")
            for lang, values in aliases.items():
                for value in values:
                    n["qid"].append(qid); n["lang"].append(lang)
                    n["name"].append(value); n["kind"].append("alias")
            names += count

            if len(p["qid"]) >= BATCH:
                write(pw, PLACES, p); p = empty(PLACES)
            if len(n["qid"]) >= BATCH:
                write(nw, NAMES, n); n = empty(NAMES)

    if p["qid"]:
        write(pw, PLACES, p)
    if n["qid"]:
        write(nw, NAMES, n)
    pw.close(); nw.close()
    print(f"places {places:,}  names {names:,}")


if __name__ == "__main__":
    main()
