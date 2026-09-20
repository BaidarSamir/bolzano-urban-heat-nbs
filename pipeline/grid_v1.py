import geopandas as gpd
import numpy as np
import osmnx as ox
import matplotlib.pyplot as plt
from shapely.geometry import box

base = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
lc = gpd.read_file(base + r"\CLMS_UA_LCU_S2021_V025ha_IT034L1_BOLZANO_03035_V01_R00_20241025.fgb")
trees = gpd.read_file(base + r"\CLMS_UA_STL_S2021_V005ha_IT034L1_BOLZANO_03035_V01_R02_20251121.fgb")

# 1. Municipality boundary from OpenStreetMap, in the same CRS as the data
boundary = ox.geocode_to_gdf("Bolzano, South Tyrol, Italy").to_crs(3035)
print("boundary type:", boundary.geometry.iloc[0].geom_type,
      "| area km2:", round(boundary.area.iloc[0] / 1e6, 1))

# 2. Clip the layers to the municipality
lc["geometry"] = lc.buffer(0)
trees["geometry"] = trees.buffer(0)
lc = gpd.clip(lc, boundary)
trees = gpd.clip(trees, boundary)
lc["code_2021"] = lc["code_2021"].astype(str)

# 3. Land cover class table (check what is in the data)
lc["area_m2"] = lc.area
table = (lc.groupby(["code_2021", "class_2021"])["area_m2"].sum() / 1e6).round(2)
print("\nLand cover classes (km2):")
print(table.to_string())

# 4. 100 m grid over the municipality
minx, miny, maxx, maxy = boundary.total_bounds
cells = [box(x, y, x + 100, y + 100)
         for x in np.arange(minx, maxx, 100) for y in np.arange(miny, maxy, 100)]
grid = gpd.GeoDataFrame({"cell_id": range(len(cells))}, geometry=cells, crs=3035)
grid = gpd.overlay(grid, boundary[["geometry"]], how="intersection")
grid["cell_area"] = grid.area

def share(layer):
    inter = gpd.overlay(grid[["cell_id", "geometry"]], layer[["geometry"]], how="intersection")
    inter["a"] = inter.area
    s = inter.groupby("cell_id")["a"].sum()
    return (grid["cell_id"].map(s).fillna(0) / grid["cell_area"]).clip(upper=1)

# 5. Tree share and green share per cell
green_codes = ("14100", "2", "31000", "32000", "40000")
green = lc[lc["code_2021"].str.startswith(green_codes)]
grid["tree_share"] = share(trees)
grid["green_share"] = share(green)

grid.to_file(base + r"\bolzano_grid.gpkg", driver="GPKG")
print("\ncells:", len(grid))
print(grid[["tree_share", "green_share"]].describe().round(2))

fig, axes = plt.subplots(1, 2, figsize=(14, 7))
grid.plot(ax=axes[0], column="tree_share", cmap="Greens", legend=True)
axes[0].set_title("Street tree share per 100 m cell")
grid.plot(ax=axes[1], column="green_share", cmap="Greens", legend=True)
axes[1].set_title("Green share per 100 m cell")
plt.savefig(base + r"\grid_map.png", dpi=150)
plt.show()