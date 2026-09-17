"""Stream a Wikidata JSON dump and emit one JSONL record per geographic item.

Selection is P625 (coordinate location) or P1566 (GeoNames ID). Both are cheap
substring tests before any JSON parsing, which is what makes a full pass viable.
"""
import sys, json

def claims_of(item, prop):
    return item.get("claims", {}).get(prop, [])

def entity_values(item, prop):
    out = []
    for c in claims_of(item, prop):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "id" in v:
            out.append(v["id"])
    return out

def string_values(item, prop):
    out = []
    for c in claims_of(item, prop):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, str):
            out.append(v)
    return out

def coord(item):
    for c in claims_of(item, "P625"):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and v.get("latitude") is not None:
            return round(v["latitude"], 6), round(v["longitude"], 6)
    return None, None


def quantity(item, prop):
    """The amount of a quantity claim, preferring the statement Wikidata prefers.

    Population is stated many times over, once per census. Rank is Wikidata's
    own answer to which one is current, so use it, and fall back to the latest
    point in time (P585) when no statement is ranked.
    """
    best = None
    for c in claims_of(item, prop):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if not isinstance(v, dict) or "amount" not in v:
            continue
        when = ""
        for q in (c.get("qualifiers") or {}).get("P585", []):
            t = q.get("datavalue", {}).get("value", {})
            if isinstance(t, dict):
                when = t.get("time") or ""
        key = (c.get("rank") == "preferred", when)
        if best is None or key > best[0]:
            best = (key, v["amount"])
    if best is None:
        return None
    try:
        return float(best[1])
    except (TypeError, ValueError):
        return None


def convert(item):
    lat, lon = coord(item)
    labels = {k: v["value"] for k, v in (item.get("labels") or {}).items()}
    aliases = {k: [a["value"] for a in v] for k, v in (item.get("aliases") or {}).items()}
    return {
        "qid": item["id"],
        "lat": lat, "lon": lon,
        "p31": entity_values(item, "P31"),
        "p131": entity_values(item, "P131"),
        "p17": entity_values(item, "P17"),
        "geonames": string_values(item, "P1566"),
        # The downward hierarchy, stated rather than inferred by reversing P131.
        "p150": entity_values(item, "P150"),
        "p36": entity_values(item, "P36"),
        # The direct link to OpenStreetMap, which is how the overlap between
        # the two can be measured instead of assumed.
        "osm": string_values(item, "P402"),
        "iso3166_2": string_values(item, "P300"),
        "population": quantity(item, "P1082"),
        "area": quantity(item, "P2046"),
        "sitelinks": len(item.get("sitelinks") or {}),
        "labels": labels,
        "aliases": aliases,
    }

def main():
    kept = seen = 0
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip().rstrip(",")
        if not line or line in ("[", "]"):
            continue
        seen += 1
        try:
            item = json.loads(line)
        except Exception:
            continue
        if item.get("type") != "item":
            continue
        if not (item.get("claims", {}).get("P625") or item.get("claims", {}).get("P1566")):
            continue
        kept += 1
        out.write(json.dumps(convert(item), ensure_ascii=False) + "\n")
    print(f"seen {seen} kept {kept}", file=sys.stderr)

main()
