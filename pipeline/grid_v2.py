import geopandas as gpd
import matplotlib.pyplot as plt

base = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
grid = gpd.read_file(base + r"\bolzano_grid.gpkg")
lc = gpd.read_file(base + r"\CLMS_UA_LCU_S2021_V025ha_IT034L1_BOLZANO_03035_V01_R00_20241025.fgb")
lc["geometry"] = lc.buffer(0)
lc["code_2021"] = lc["code_2021"].astype(str)

# Approximate sealed share per class (assumption based on the S.L. ranges in class names)
sealed = {"11100": 0.9, "11210": 0.65, "11220": 0.4, "11230": 0.2, "11240": 0.05,
          "11300": 0.5, "12100": 0.8, "12210": 0.9, "12220": 0.9, "12230": 0.6, "12400": 0.8}
lc["sealed"] = lc["code_2021"].map(sealed).fillna(0.0)

inter = gpd.overlay(grid[["cell_id", "geometry"]],
                    lc[["code_2021", "sealed", "geometry"]], how="intersection")
inter["a"] = inter.area
inter["urban_a"] = inter["a"].where(inter["code_2021"].str.startswith("1"), 0)
inter["ugreen_a"] = inter["a"].where(inter["code_2021"].str.startswith("14"), 0)
inter["sealed_a"] = inter["a"] * inter["sealed"]
sums = inter.groupby("cell_id")[["urban_a", "ugreen_a", "sealed_a"]].sum()

grid["urban_share"] = grid["cell_id"].map(sums["urban_a"]).fillna(0) / grid["cell_area"]
grid["ugreen_share"] = grid["cell_id"].map(sums["ugreen_a"]).fillna(0) / grid["cell_area"]
grid["sealed_share"] = grid["cell_id"].map(sums["sealed_a"]).fillna(0) / grid["cell_area"]

city = grid[grid["urban_share"] >= 0.3].copy()
print("built-up cells:", len(city), "of", len(grid))
print(city[["tree_share", "ugreen_share", "sealed_share"]].describe().round(2))
city.to_file(base + r"\bolzano_city_grid.gpkg", driver="GPKG")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for ax, col, cmap in zip(axes, ["sealed_share", "ugreen_share", "tree_share"],
                         ["Reds", "Greens", "Greens"]):
    city.plot(ax=ax, column=col, cmap=cmap, legend=True)
    ax.set_title(col)
plt.savefig(base + r"\city_maps.png", dpi=150)
plt.show()