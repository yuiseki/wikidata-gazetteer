---
license: cc0-1.0
language:
- multilingual
size_categories:
- 10M<n<100M
task_categories:
- token-classification
tags:
- gazetteer
- wikidata
- geography
- toponym
- multilingual
pretty_name: Wikidata Gazetteer
configs:
- config_name: places
  data_files: places.parquet
- config_name: names
  data_files: names.parquet
---

# Wikidata Gazetteer

Every geographic item in Wikidata: 12,205,328 places carrying 62,506,107 names
in 552 languages, with coordinates, the administrative hierarchy, and a count
of how many Wikipedias write about each one.

Built from the `20260831` JSON dump. CC0, like Wikidata itself.

## Why this exists

Wikidata holds the deepest multilingual place-name data of any openly licensed
source. Measured against OpenStreetMap, which carries 4,200,089 localized names
across its 7,678,203 named `place=*` objects, this is 5.1 names per place
against 0.55.

The pieces were already published separately: full entity dumps, RDF triples,
per-language label tables. None of them is a gazetteer. This joins the names to
the positions and the hierarchy.

## Two tables

`places`, one row per place:

| column | |
|---|---|
| `qid` | Wikidata item id |
| `lat`, `lon` | P625 |
| `country` | P17, first value |
| `parent` | P131, first value |
| `instance_of` | P31, all values |
| `located_in` | P131, all values |
| `geonames_id` | P1566, first value |
| `sitelinks` | number of Wikipedia articles |
| `n_names` | rows this place has in `names` |

`names`, one row per name, joined back on `qid`:

| column | |
|---|---|
| `qid` | |
| `lang` | language code as Wikidata gives it |
| `name` | |
| `kind` | `label` or `alias` |

One row per name rather than a merged best name. Divergence between spellings
is information, and a reader deciding which form to prefer needs to see them
all.

## Coverage

| | places | share |
|---|---|---|
| coordinate | 12,133,776 | 99.4% |
| country (P17) | 12,086,915 | 99.0% |
| class (P31) | 12,050,921 | 98.7% |
| hierarchy (P131) | 10,806,828 | 88.5% |
| English label | 9,123,547 | 74.8% |
| at least one sitelink | 7,374,883 | 60.4% |
| GeoNames id (P1566) | 4,058,151 | 33.2% |
| Japanese label | 488,598 | 4.0% |

Names per place: 30.0% have one, 70.9% have three or fewer, 6.3% have more
than ten.

## What is actually in here, which is not only settlements

Selection is by `P625` or `P1566`, that is, anything with a location. The
twenty commonest classes:

| class | places | | class | places |
|---|---|---|---|---|
| mountain | 507,727 | | village | 205,770 |
| street | 504,665 | | stream | 195,084 |
| human settlement | 478,604 | | built structure | 192,382 |
| river | 409,860 | | watercourse | 165,724 |
| hill | 316,092 | | island | 151,872 |
| cemetery | 295,098 | | public school | 150,599 |
| lake | 294,257 | | primary school | 144,217 |
| building | 282,902 | | sports venue | 143,054 |
| church building | 270,944 | | hamlet | 135,274 |
| house | 233,771 | | valley | 133,346 |
| mosque | 233,308 | | hotel | 129,411 |

Physical features and buildings outnumber settlements. Filter on `instance_of`
if that is not what you want. In particular, matching every name in this table
against running text will produce a great many false positives, because street
names, house names and hotel names are in it.

## Known limits

Japanese labels reach only 4.0% of places, and other non-European languages are
thinner still. The language distribution follows Wikipedia's, so `ceb` has
3,459,736 labels from bot-generated articles while most languages have far
fewer.

33.2% of places carry a GeoNames id, so two thirds have no link to GeoNames at
all. That makes this a substantially independent source, which is useful when
weighing agreement between gazetteers, but it also means the two do not simply
overlap.

Wikidata is crowd-edited. Positions and hierarchies are as good as the last
person to touch them.

## Licence

CC0-1.0, inherited from Wikidata. The code that built it is Apache-2.0 at
https://github.com/yuiseki/wikidata-gazetteer
