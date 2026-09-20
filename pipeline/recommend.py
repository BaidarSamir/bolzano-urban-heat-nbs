import geopandas as gpd
import pandas as pd

base = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
city = gpd.read_file(base + r"\bolzano_cells_typed.gpkg")

# The airport behaves like a large paved and roofed area
city.loc[city["dominant_code"] == "12400", "cell_type"] = "industrial_commercial"

GCARE = "GCARE (Univ. of Surrey) review of 200+ studies, reported by RIBAJ, Mar 2024"
BROUSSE = "Brousse et al. 2024, Geophysical Research Letters (London model)"
catalogue = pd.DataFrame([
 dict(id="cool_roof", name="Cool (reflective) roof", nature_based="no",
      cooling_evidence="About -1.2 C air temperature, city-scale model, 2 hot days",
      source=BROUSSE, space_need="existing large flat roofs", cost_level="low-medium (assumption)"),
 dict(id="street_trees", name="Street trees", nature_based="yes",
      cooling_evidence="Average -3.8 C at street level in reviewed studies; about -0.3 C in the city-scale London model",
      source=GCARE + "; " + BROUSSE, space_need="medium (planting strip or wide sidewalk)", cost_level="medium (assumption)"),
 dict(id="green_wall", name="Green wall", nature_based="yes",
      cooling_evidence="Average -4.1 C at street level in reviewed studies",
      source=GCARE, space_need="low (building facade)", cost_level="high (assumption)"),
 dict(id="green_roof", name="Green roof", nature_based="yes",
      cooling_evidence="About 0 C at city scale in London model; no street-level effect in an Arnhem simulation; value is mainly at building level",
      source=BROUSSE + "; Climate Change Post summary, 2015", space_need="flat roof with load capacity", cost_level="high (assumption)"),
 dict(id="cool_pavement", name="Reflective pavement", nature_based="no",
      cooling_evidence="Better thermal comfort and applicability than trees, lower overall multi-criteria score (3.50 trees vs 2.45)",
      source="Sustainability assessment of street trees and cool pavements, doi:10.3846/mla.2026.27186",
      space_need="existing paved surfaces", cost_level="low-medium (assumption)"),
 dict(id="unseal_paving", name="Unsealing paved surfaces", nature_based="yes",
      cooling_evidence="Tested as a scenario in a Vienna modeling study; no figures taken from the abstract",
      source="EMS Annual Meeting 2023, abstract EMS2023-316", space_need="car parks, yards", cost_level="medium (assumption)"),
 dict(id="pocket_park", name="Pocket park", nature_based="yes",
      cooling_evidence="Parks: average -3.2 C in reviewed studies",
      source=GCARE, space_need="high (vacant plot)", cost_level="high (assumption)"),
 dict(id="green_corridor", name="Green corridor", nature_based="yes",
      cooling_evidence="Extends park and river cooling; park average -3.2 C in reviewed studies",
      source=GCARE, space_need="medium (linear strip)", cost_level="medium (assumption)"),
])
catalogue.to_csv(base + r"\nbs_catalogue.csv", index=False, encoding="utf-8-sig")

# Cells within 150 m of an existing green cell
green_union = city.loc[city["cell_type"] == "green", "geometry"].unary_union
city["near_green"] = city.geometry.centroid.distance(green_union) < 150

def recommend(row):
    if row["heat_class"] not in ("high", "highest"):
        return ""
    t = row["cell_type"]
    if t == "industrial_commercial":
        recs = ["cool_roof", "unseal_paving", "street_trees"]
    elif t == "transport":
        recs = ["street_trees", "cool_pavement"]
    elif t == "residential":
        recs = ["street_trees", "green_wall", "pocket_park"] if row["sealed_share"] >= 0.6 \
               else ["street_trees", "green_corridor"]
        if row["near_green"] and "green_corridor" not in recs:
            recs.insert(1, "green_corridor")
    else:
        recs = ["street_trees", "cool_pavement"]
    return " | ".join(recs[:3])

city["recommendation"] = city.apply(recommend, axis=1)
print(city.loc[city["recommendation"] != "", "recommendation"].value_counts())
print("cells with a recommendation:", (city["recommendation"] != "").sum())

city.to_file(base + r"\bolzano_recommendations.gpkg", driver="GPKG")