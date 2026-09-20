import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

base = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
city = gpd.read_file(base + r"\bolzano_city_grid.gpkg")

# Vegetation cover: trees and urban green can overlap, so cap at 1
city["veg_share"] = (city["tree_share"] + city["ugreen_share"]).clip(upper=1)

# Transparent heat exposure index (0 = low, 1 = high)
city["heat_index"] = 0.6 * city["sealed_share"] + 0.4 * (1 - city["veg_share"])

bins = [0, 0.3, 0.5, 0.7, 1.0]
labels = ["low", "moderate", "high", "very high"]
city["heat_class"] = pd.cut(city["heat_index"], bins=bins, labels=labels, include_lowest=True)

print(city["heat_class"].value_counts().reindex(labels))
print(city["heat_index"].describe().round(2))

city.to_file(base + r"\bolzano_heat_index.gpkg", driver="GPKG")

fig, ax = plt.subplots(figsize=(9, 8))
city.plot(ax=ax, column="heat_class", cmap="YlOrRd", legend=True, categorical=True)
ax.set_title("Heat exposure index per 100 m cell (proxy, no temperature data yet)")
plt.savefig(base + r"\heat_index_map.png", dpi=150)
plt.show()