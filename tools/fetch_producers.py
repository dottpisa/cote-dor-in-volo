"""Scarica le imprese vitivinicole della Côte d'Or (SIRENE, API Recherche d'Entreprises)
e le cantine segnate su OpenStreetMap. Salva i dati grezzi in out/."""
import json, os, time, urllib.parse, urllib.request, sys
OUT = "out"
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
LOG = []
def log(*a):
    line = " ".join(str(x) for x in a)
    print(line, flush=True); LOG.append(f"{time.time()-T0:7.1f}s {line}")
    open("out/log.txt", "w").write("\n".join(LOG))

UA = {"User-Agent": "cote-dor-in-volo/1.0 (github.com/dottpisa/cote-dor-in-volo)"}

def get(url, data=None, tries=5):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            log("retry", k, url[:160], repr(e))
            time.sleep(2 + 3 * k)
    raise RuntimeError("failed " + url)

QUERIES = []
for naf in ["01.21Z", "11.02B", "46.34Z"]:
    QUERIES.append({"activite_principale": naf, "departement": "21"})
    QUERIES.append({"activite_principale": naf, "code_postal": "71150"})

results = {}
probe = get("https://recherche-entreprises.api.gouv.fr/search?" + urllib.parse.urlencode({"activite_principale": "01.21Z", "departement": "21", "per_page": 2, "page": 1}))
json.dump(probe, open(f"{OUT}/probe.json", "w"), ensure_ascii=False, indent=1)
log("probe total_results", probe.get("total_results"), "total_pages", probe.get("total_pages"))
for q in QUERIES:
    page = 1
    while True:
        params = dict(q, page=page, per_page=25, etat_administratif="A")
        if time.time() - T0 > 1200:
            log("tempo scaduto, mi fermo"); break
        url = "https://recherche-entreprises.api.gouv.fr/search?" + urllib.parse.urlencode(params)
        d = get(url)
        for r in d.get("results", []):
            results[r["siren"]] = r
        tp = d.get("total_pages", 1)
        log(q, "page", page, "/", tp, "tot", d.get("total_results"))
        if page >= tp or page >= 400:
            break
        page += 1
        time.sleep(0.2)

json.dump(list(results.values()), open(f"{OUT}/sirene.json", "w"), ensure_ascii=False)
log("sirene unita legali:", len(results))

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
        log("overpass fail", ep, repr(e))
json.dump(osm or {"elements": []}, open(f"{OUT}/osm.json", "w"), ensure_ascii=False)
log("osm elementi:", len((osm or {}).get("elements", [])))
