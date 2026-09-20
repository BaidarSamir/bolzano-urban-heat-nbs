import geopandas as gpd
import matplotlib.pyplot as plt

base = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
files = {
    "landcover": "CLMS_UA_LCU_S2021_V025ha_IT034L1_BOLZANO_03035_V01_R00_20241025.fgb",
    "trees": "CLMS_UA_STL_S2021_V005ha_IT034L1_BOLZANO_03035_V01_R02_20251121.fgb",
    "mask": "CLMS_UA_UM_S2021_V005ha_IT034L1_BOLZANO_03035_V01_R02_20251121.fgb",
}

layers = {}
for name, f in files.items():
    gdf = gpd.read_file(f"{base}\\{f}")
    layers[name] = gdf
    print(f"\n== {name} ==")
    print("rows:", len(gdf), "| CRS:", gdf.crs)
    print("columns:", list(gdf.columns))
    print(gdf.head(3))

fig, ax = plt.subplots(figsize=(9, 9))
layers["landcover"].plot(ax=ax, color="lightgrey", edgecolor="none")
layers["trees"].plot(ax=ax, color="green")
layers["mask"].boundary.plot(ax=ax, color="red", linewidth=1)
plt.savefig("first_map.png", dpi=150)
plt.show()