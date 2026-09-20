import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

base = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
city = gpd.read_file(base + r"\bolzano_heat_index.gpkg")

labels = ["lower", "moderate", "high", "highest"]
city["heat_class"] = pd.qcut(city["heat_index"], q=4, labels=labels)

print(city["heat_index"].quantile([0.25, 0.5, 0.75]).round(2))
print(city["heat_class"].value_counts().reindex(labels))

city.to_file(base + r"\bolzano_heat_index.gpkg", driver="GPKG")

fig, ax = plt.subplots(figsize=(9, 8))
city.plot(ax=ax, column="heat_class", cmap="YlOrRd", legend=True, categorical=True)
ax.set_title("Relative heat exposure index (quartiles, proxy)")
plt.savefig(base + r"\heat_index_map_v2.png", dpi=150)
plt.show()