#!/usr/bin/env python3
"""Push the two Parquet tables and the files that explain them to the Hub.

Unlike the sister repositories this does not build a datasets.Dataset and call
push_to_hub. 62.5 million name rows do not belong in memory, and the Parquet
files are already the published form, so they are uploaded as they are.

That also reverses the ordering those repositories need. push_to_hub writes a
dataset_info block into the card's front matter, so there the card has to go
first or it is erased. Nothing here rewrites the card, so the data goes first
instead, and the repository is never in a state where the card promises files
that are not there yet.

    python3 src/publish.py             # dry run, checks the card against the data
    python3 src/publish.py --push      # uploads
"""
import argparse
import os
import sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REPO = "yuiseki/wikidata-gazetteer"
TABLES = ("places.parquet", "names.parquet")


def counts(directory):
    import pyarrow.parquet as pq
    out = {}
    for name in TABLES:
        path = os.path.join(directory, name)
        if not os.path.exists(path):
            raise SystemExit(f"missing {path}")
        f = pq.ParquetFile(path)
        out[name] = (f.metadata.num_rows, os.path.getsize(path),
                     [c for c in f.schema_arrow.names])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="/home/yuiseki/yuisekinai-data/wikidata/parquet",
                    help="directory holding places.parquet and names.parquet")
    ap.add_argument("--card", default=os.path.join(BASE, "data/README.md"))
    ap.add_argument("--extra", nargs="*", default=[
        os.path.join(BASE, "data/LICENSE"),
        os.path.join(BASE, "data/provenance.yaml")])
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true", help="actually upload")
    a = ap.parse_args()

    tables = counts(a.parquet)
    total = 0
    for name, (rows, size, columns) in tables.items():
        total += size
        print(f"{name:16s} {rows:>12,} rows  {size/1e6:8.1f} MB")
        print(f"{'':16s} {', '.join(columns)}")
    print(f"{'total':16s} {'':>12s}  {total/1e6:8.1f} MB")

    card = open(a.card, encoding="utf-8").read()
    for name, (rows, _, _) in tables.items():
        if f"{rows:,}" not in card:
            raise SystemExit(
                f"the card does not mention {rows:,} rows for {name}; "
                "it is stale, rebuild it before publishing")
    print(f"card mentions both row counts")

    for p in [a.card] + a.extra:
        if not os.path.exists(p):
            raise SystemExit(f"missing {p}")
    print("card " + os.path.relpath(a.card, BASE) + ", plus " +
          ", ".join(os.path.relpath(p, BASE) for p in a.extra))

    if not a.push:
        print("dry run. pass --push to upload")
        return 0

    from huggingface_hub import HfApi

    api = HfApi()
    # Nothing else creates it. upload_file answers 404 when it is not there.
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True)

    for name in TABLES:
        print(f"uploading {name} ...", flush=True)
        api.upload_file(path_or_fileobj=os.path.join(a.parquet, name),
                        path_in_repo=name, repo_id=a.repo, repo_type="dataset")
    for p in a.extra:
        api.upload_file(path_or_fileobj=p, path_in_repo=os.path.basename(p),
                        repo_id=a.repo, repo_type="dataset")
    api.upload_file(path_or_fileobj=a.card, path_in_repo="README.md",
                    repo_id=a.repo, repo_type="dataset")
    print(f"pushed to https://huggingface.co/datasets/{a.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
