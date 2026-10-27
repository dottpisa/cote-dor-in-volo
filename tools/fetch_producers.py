"""Scarica le imprese vitivinicole della Côte d'Or (SIRENE, API Recherche d'Entreprises)
e le cantine segnate su OpenStreetMap. Salva i dati grezzi in out/."""
import json, os, time, urllib.parse, urllib.request

OUT = "out"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "cote-dor-in-volo/1.0 (github.com/dottpisa/cote-dor-in-volo)"}

def get(url, data=None, tries=5):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("retry", k, url[:120], e, flush=True)
            time.sleep(2 + 3 * k)
    raise RuntimeError("failed " + url)

QUERIES = []
for naf in ["01.21Z", "11.02B", "46.34Z"]:
    QUERIES.append({"activite_principale": naf, "departement": "21"})
    QUERIES.append({"activite_principale": naf, "code_postal": "71150"})

results = {}
for q in QUERIES:
    page = 1
    while True:
        params = dict(q, page=page, per_page=25, etat_administratif="A")
        url = "https://recherche-entreprises.api.gouv.fr/search?" + urllib.parse.urlencode(params)
        d = get(url)
        for r in d.get("results", []):
            results[r["siren"]] = r
        tp = d.get("total_pages", 1)
        print(q, "page", page, "/", tp, "tot", d.get("total_results"), flush=True)
        if page >= tp or page >= 400:
            break
        page += 1
        time.sleep(0.2)

json.dump(list(results.values()), open(f"{OUT}/sirene.json", "w"), ensure_ascii=False)
print("sirene unità legali:", len(results), flush=True)

q = """[out:json][timeout:120];
(nwr["craft"="winery"](46.86,4.60,47.33,5.08);
 nwr["shop"="wine"](46.86,4.60,47.33,5.08);
 nwr["tourism"="wine_cellar"](46.86,4.60,47.33,5.08););
out center tags;"""
osm = None
for ep in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    try:
        osm = get(ep, data=urllib.parse.urlencode({"data": q}).encode())
        break
    except Exception as e:
        print("overpass fail", ep, e)
json.dump(osm or {"elements": []}, open(f"{OUT}/osm.json", "w"), ensure_ascii=False)
print("osm elementi:", len((osm or {}).get("elements", [])), flush=True)
