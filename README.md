# Côte d'Or in volo

Sorvolo 3D dei climats della Côte d'Or, da Marsannay alle Maranges.

- Confini e superfici: delimitazione parcellare delle AOC viticole, INAO (data.gouv.fr), versione del 19 ottobre 2026
- Foto aeree: IGN BD ORTHO (Géoplateforme)
- Cantine: registro SIRENE (INSEE, Licence Ouverte), imprese attive con codice 01.21Z, 11.02A/B o 46.34Z, più le cantine segnate su OpenStreetMap. Sono esclusi i viticoltori individuali senza nome commerciale e le società solo fondiarie (GFA, SCI). Lo script è in `tools/fetch_producers.py` e si rilancia dalla scheda Actions.
- Mappa: OpenStreetMap tramite OpenFreeMap
- Rilievo: AWS Terrain Tiles
- Motore della mappa: [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js)

Le note personali e i preferiti restano salvati solo nel browser di chi li scrive.
