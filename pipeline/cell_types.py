import geopandas as gpd
import pandas as pd

base = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
city = gpd.read_file(base + r"\bolzano_heat_index.gpkg")
lc = gpd.read_file(base + r"\CLMS_UA_LCU_S2021_V025ha_IT034L1_BOLZANO_03035_V01_R00_20241025.fgb")
lc["geometry"] = lc.buffer(0)
lc["code_2021"] = lc["code_2021"].astype(str)

inter = gpd.overlay(city[["cell_id", "geometry"]], lc[["code_2021", "geometry"]], how="intersection")
inter["a"] = inter.area
dom = (inter.sort_values("a", ascending=False)
            .drop_duplicates("cell_id")
            .set_index("cell_id")["code_2021"])
city["dominant_code"] = city["cell_id"].map(dom).fillna("none")

def group(c):
    if c == "12100":
        return "industrial_commercial"
    if c in ("12210", "12220", "12230"):
        return "transport"
    if c.startswith("14"):
        return "green"
    if c.startswith("11"):
        return "residential"
    return "other"

city["cell_type"] = city["dominant_code"].apply(group)
print(city["cell_type"].value_counts())
print(pd.crosstab(city["cell_type"], city["heat_class"]))

city.to_file(base + r"\bolzano_cells_typed.gpkg", driver="GPKG")