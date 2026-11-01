"""Well-known places from Wikipedia's 'List of ghost towns by country' that are not in the Wikidata extract (Wikidata
files them as villages, towns or cities rather than ghost towns), placed by hand so the map can show them.
Positions are approximate (to about 0.05 degrees, a few kilometres), set from general knowledge of where each place is.
They are shown on the map as a separate layer and are NOT counted in any Wikidata total.
Key: (list section, name as parsed from the list) -> (lat, lon)."""
HAND = {
    ("Ukraine", "Pripyat"): (51.405, 30.054), ("Ukraine", "Chernobyl"): (51.276, 30.222),
    ("Japan", "Ōkuma"): (37.404, 141.000),
    ("France", "Oradour-sur-Glane"): (45.929, 1.032), ("Turkey", "Kayaköy"): (36.575, 29.090),
    ("Spain", "Belchite"): (41.305, -0.752), ("Syria", "Quneitra"): (33.125, 35.824),
    ("United Kingdom", "Tyneham"): (50.622, -2.168), ("United Kingdom", "Imber"): (51.236, -2.051),
    ("Austria", "Döllersheim"): (48.618, 15.307), ("Thailand", "Old Ayutthaya"): (14.355, 100.560),
    ("Ukraine", "Soledar"): (48.683, 38.088), ("Ukraine", "Popasna"): (48.633, 38.383), ("Ukraine", "Marinka"): (47.942, 37.503),
    ("Colombia", "Armero"): (4.965, -74.905), ("Argentina", "Villa Epecuén"): (-37.130, -62.800),
    ("United Kingdom", "Dunwich"): (52.277, 1.630), ("United Kingdom", "Hallsands"): (50.236, -3.661),
    ("New Zealand", "Te Wairoa"): (-38.205, 176.360), ("Chile", "Chaitén"): (-42.915, -72.710),
    ("Italy", "Bussana Vecchia"): (43.833, 7.830), ("Italy", "Poggioreale"): (37.760, 13.030),
    ("India", "Dhanushkodi"): (9.180, 79.420),
    ("United Kingdom", "Capel Celyn"): (52.940, -3.700), ("United Kingdom", "Mardale"): (54.495, -2.795),
    ("United Kingdom", "Derwent"): (53.405, -1.725), ("Russian Federation", "Mologa"): (58.200, 38.430),
    ("Italy", "Curon in South Tyrol"): (46.810, 10.540), ("Portugal", "Vilarinho da Furna"): (41.770, -8.200),
    ("Japan", "Hashima Island"): (32.628, 129.738), ("Norway", "Pyramiden"): (78.656, 16.330),
    ("Russian Federation", "Kadykchan"): (63.080, 146.980), ("Australia", "Wittenoom"): (-22.240, 118.330),
    ("Australia", "Gwalia"): (-28.920, 121.330), ("Australia", "Silverton"): (-31.885, 141.226),
    ("Chile", "Sewell"): (-34.080, -70.380), ("Mexico", "Real de Catorce"): (23.690, -100.890),
    ("Brazil", "Fordlândia"): (-3.830, -55.500), ("Republic of Ireland", "Great Blasket Island"): (52.100, -10.530),
    ("United Kingdom", "Mingulay"): (56.810, -7.640), ("Belgium", "Doel"): (51.310, 4.260),
    ("Italy", "Civita di Bagnoregio"): (42.627, 12.114), ("Greece", "Spinalonga"): (35.297, 25.738),
    ("United Kingdom", "Tide Mills"): (50.785, 0.070),
}
