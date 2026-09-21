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

Code, provenance and the build pipeline:
https://github.com/yuiseki/wikidata-gazetteer

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
| `osm_relation` | P402, the OpenStreetMap relation id |
| `capital` | P36, first value |
| `iso_3166_2` | P300, first value |
| `contains` | P150, all values |
| `population` | P1082, the preferred statement, else the latest |
| `area` | P2046 |
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
| population (P1082) | 827,694 | 6.8% |
| area (P2046) | 617,676 | 5.1% |
| OSM relation (P402) | 536,581 | 4.4% |
| capital (P36) | 102,291 | 0.8% |
| contains (P150) | 80,862 | 0.7% |
| ISO 3166-2 (P300) | 5,526 | 0.0% |
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

Physical features and buildings outnumber settlements. That is a fact about
granularity rather than about importance: there are half a million mountains and
about two hundred countries, so any ranking by count puts mountains first and
countries nowhere. Which of them matters depends on the text being matched.

## Things in here that are not places at all

Selecting on `P625` takes everything Wikidata gives a coordinate to, and it
gives coordinates to more than places.

**Languages, 729 of them.** Wikidata places a language where it is spoken.
`Q150` French sits at 48.85, 2.35, which is Paris; `Q1860` English at 51.0, 0.0;
`Q7737` Russian at 55.0, 38.0. 729 items out of 12.2 million is nothing by
count and a tenth of the matches in running text, because a document writes
"French" far more often than it names most towns. Measured against two corpora,
removing them cut matches by 9.9% in an English travel guide and 10.7% in United
Nations documents.

**Organisations, about 36,000.** `nonprofit organization` 13,617, `business`
11,635, `organization` 11,250, carrying the coordinates of their premises. These
do less harm: their names are long and specific, like `Boston Children's
Museum`, so they rarely collide with ordinary text.

Of the 840,857 names that survive a one-word prominence filter, 1,786 resolve to
a language and 5,462 to an organisation.

### Removing them

    -- the language classes, found by taking the classes that co-occur with
    -- Q34770 language and keeping those whose label names a kind of language
    SELECT * FROM places WHERE NOT list_has_any(instance_of, [
      'Q315','Q1036511','Q1097949','Q11499915','Q1149626','Q11820611','Q1208380',
      'Q1288568','Q1322198','Q135295328','Q152559','Q17376908','Q1790577',
      'Q20162172','Q20671152','Q21663239','Q215844','Q2315359','Q23492',
      'Q250858','Q25295','Q2630831','Q2737212','Q2966838','Q3123468','Q33215',
      'Q332','Q33289','Q33384','Q335214','Q33742','Q33831','Q33956','Q3329375',
      'Q34228','Q34770','Q38058796','Q399495','Q4085712','Q436240','Q45762',
      'Q455374','Q4536543','Q470775','Q61566','Q645304','Q778873','Q838296',
      'Q839470','Q941501','Q951873'
    ]);

    -- and the organisations
    SELECT * FROM places WHERE NOT list_has_any(instance_of,
      ['Q163740','Q4830453','Q43229']);

Matching every name in this table against running text will still produce false
positives, because street names, house names and hotel names are in it, and
because a one-word name like `Council` names a town in Idaho. Two rules help,
measured on 1.31 billion characters of UN documents: require a match to cover a
whole run of capitalised words, and require a one-word name to clear a
prominence bar. At 100 sitelinks for single words, the top twenty-five names
matched in that corpus are all real.

## The hierarchy runs in both directions, unevenly

`located_in` (P131) is the one to build on. 10,806,828 places carry it, and
reversing it yields 395,046 distinct containers, of which 357,043 are rows in
this table, so 90.4% of the hierarchy resolves without leaving the dataset.

`contains` (P150) states the same relation downward, and is far sparser: only
80,862 places name their children, across 1,093,138 edges. Where it is present
it is well kept. Japan lists its 47 prefectures; Tokyo lists its 96 wards and
municipalities. Treat it as a cross-check on the reversed P131, not as the
hierarchy itself.

## How much of this is linked to the other big gazetteers

| | places |
|---|---|
| both a GeoNames id and an OSM relation | 273,599 |
| GeoNames only | 3,784,552 |
| OSM relation only | 262,982 |
| neither | 7,884,195 |

Two thirds of these places, 64.6%, are linked to neither. That is worth knowing
before treating agreement between gazetteers as evidence: this source is largely
not a restatement of either of the other two.

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
