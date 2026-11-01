## Title

[OC] Ghost towns of the world: 5,448 abandoned settlements coloured by why they were abandoned. 80% of Wikidata's ghost towns are in the US, England's deserted medieval villages are 38% of the map, and only 5% of Wikidata's ghost towns say why they died

## Body

I mapped every ghost town, abandoned village and deserted medieval village with a position in Wikidata (3,374, after dropping 2,456 living Mexican municipalities that reach the class through a faulty link), plus England's 2,074 deserted medieval villages from Beresford's gazetteer, and gave each a reason with simple, published keyword rules on Wikidata descriptions and Wikipedia text. The map turns out to show who has catalogued abandonment: 2,700 of Wikidata's ghost towns are American and all of Africa has 8. Only 165 Wikidata ghost towns yield a reason, 61 of them just from a mining word in the name. Wikipedia's 'List of ghost towns by country' is more talkative: 300 of 492 places give a reason, led by mining (81), then war (55) and disasters (54), decline (50), reservoirs (27) and Chernobyl and Fukushima (24). In the American West, 65 of 1,053 ghost towns are tied to mining, mostly by name; Bodie and Rhyolite have no reason recorded at all. 44 famous places missing from Wikidata's ghost town class (Pripyat, Hashima, Oradour-sur-Glane...) are placed by hand and ringed. Interactive map with filters: https://maps.tristanhotham.com/ghost-towns/

## Source comment

Sources: Wikidata (CC0), items classed as ghost town (Q74047), abandoned village (Q15661340) or deserted medieval village (Q1952852), via QLever; Beresford's Lost Villages, University of Hull (CC BY-NC-SA 4.0); English Wikipedia, 'List of ghost towns by country' and 'Ghost town' (CC BY-SA 4.0); Natural Earth. Reasons from keyword rules, in a fixed order when several match, with high, medium or low confidence; full rules in the repo.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/ghost-towns/
Paper: https://doi.org/{10.5281/zenodo.23857616}
Blog post: {https://blog.tristanhotham.com/2026/10/31/ghost-towns/}
