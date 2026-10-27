"""Estrae dal registro SIRENE completo (INSEE, Licence Ouverte) le imprese vitivinicole
attive della Côte d'Or e delle Maranges, e scarica le cantine segnate su OpenStreetMap.
Scrive solo i dati filtrati in out/."""
import csv, io, json, os, sys, time, urllib.parse, urllib.request, zipfile

OUT = "out"; os.makedirs(OUT, exist_ok=True)
T0 = time.time(); LOG = []
def log(*a):
    line = " ".join(str(x) for x in a); print(line, flush=True)
    LOG.append(f"{time.time()-T0:7.1f}s {line}"); open(f"{OUT}/log.txt", "w").write("\n".join(LOG))
UA = {"User-Agent": "cote-dor-in-volo/1.0 (github.com/dottpisa/cote-dor-in-volo)"}
def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, headers=UA)
    return urllib.request.urlopen(req, timeout=300)
csv.field_size_limit(10**8)

ds = json.load(fetch("https://www.data.gouv.fr/api/1/datasets/5b7ffc618b4c4169d30727e0/"))
res = {r["title"]: r["url"] for r in ds["resources"]}
log("risorse:", list(res)[:30])
def pick(prefix):
    c = [t for t in res if t.lower().startswith(prefix.lower()) and "histor" not in t.lower() and "parquet" not in t.lower()]
    c.sort(key=len); return res[c[0]] if c else None
U_ET = pick("Sirene : Fichier StockEtablissement") or pick("StockEtablissement")
U_UL = pick("Sirene : Fichier StockUniteLegale") or pick("StockUniteLegale")
if not U_ET:
    U_ET = next(u for t, u in res.items() if "StockEtablissement_utf8" in u and "Histo" not in u and "Liens" not in u)
if not U_UL:
    U_UL = next(u for t, u in res.items() if "StockUniteLegale_utf8" in u and "Histo" not in u)
log("etab:", U_ET); log("ul:", U_UL)

def download(url, path):
    with fetch(url) as r, open(path, "wb") as f:
        while True:
            b = r.read(1 << 22)
            if not b: break
            f.write(b)
    log("scaricato", path, os.path.getsize(path) // 2**20, "MB")

def rows(path):
    z = zipfile.ZipFile(path); name = [n for n in z.namelist() if n.endswith(".csv")][0]
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline=""))

NAF = {"01.21Z", "11.02A", "11.02B", "46.34Z"}
download(U_ET, "et.zip")
etabs = []; sirens = set(); n = 0
for r in rows("et.zip"):
    n += 1
    cc = r.get("codeCommuneEtablissement", ""); cp = r.get("codePostalEtablissement", "")
    if not (cc.startswith("21") or cp == "71150"): continue
    if r.get("etatAdministratifEtablissement") != "A": continue
    if r.get("activitePrincipaleEtablissement") not in NAF: continue
    keep = {k: r.get(k, "") for k in ["siren", "siret", "statutDiffusionEtablissement", "etablissementSiege", "dateCreationEtablissement",
        "trancheEffectifsEtablissement", "numeroVoieEtablissement", "typeVoieEtablissement", "libelleVoieEtablissement",
        "complementAdresseEtablissement", "codePostalEtablissement", "libelleCommuneEtablissement", "codeCommuneEtablissement",
        "coordonneeLambertAbscisseEtablissement", "coordonneeLambertOrdonneeEtablissement", "enseigne1Etablissement",
        "enseigne2Etablissement", "denominationUsuelleEtablissement", "activitePrincipaleEtablissement"]}
    etabs.append(keep); sirens.add(keep["siren"])
log("righe etab lette", n, "tenute", len(etabs)); os.remove("et.zip")

download(U_UL, "ul.zip")
uls = {}
for r in rows("ul.zip"):
    if r.get("siren") in sirens:
        uls[r["siren"]] = {k: r.get(k, "") for k in ["siren", "statutDiffusionUniteLegale", "denominationUniteLegale", "denominationUsuelle1UniteLegale",
            "sigleUniteLegale", "nomUniteLegale", "nomUsageUniteLegale", "prenomUsuelUniteLegale", "prenom1UniteLegale",
            "categorieJuridiqueUniteLegale", "activitePrincipaleUniteLegale", "trancheEffectifsUniteLegale", "categorieEntreprise",
            "dateCreationUniteLegale", "etatAdministratifUniteLegale"]}
log("unita legali", len(uls)); os.remove("ul.zip")
json.dump({"etablissements": etabs, "unites": uls}, open(f"{OUT}/sirene.json", "w"), ensure_ascii=False)

q = """[out:json][timeout:120];
(nwr["craft"="winery"](46.86,4.60,47.33,5.08);
 nwr["shop"="wine"](46.86,4.60,47.33,5.08);
 nwr["tourism"="wine_cellar"](46.86,4.60,47.33,5.08););
out center tags;"""
osm = {"elements": []}
for ep in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    try:
        osm = json.load(fetch(ep, data=urllib.parse.urlencode({"data": q}).encode())); break
    except Exception as e:
        log("overpass fail", ep, repr(e))
json.dump(osm, open(f"{OUT}/osm.json", "w"), ensure_ascii=False)
log("osm elementi", len(osm.get("elements", [])), "fine")
