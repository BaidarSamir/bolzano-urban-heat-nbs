import numpy as np
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
from rasterstats import zonal_stats
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LS = r"C:\Users\Lenovo\Desktop\project_bolzano\landsat"
RES = r"C:\Users\Lenovo\Desktop\project_bolzano\Results"
PID = "LC08_L2SP_193028_20210613_20210622_02_T1"

MULT, ADD = 0.00341802, 149.0          # from the scene's MTL file (ST_B10 -> Kelvin)
MIN_VALID = 0.5                          # keep cells with at least 50% clear pixels

grid = gpd.read_file(RES + r"\bolzano_recommendations.gpkg")

with rasterio.open(f"{LS}\\{PID}_ST_B10.TIF") as st, rasterio.open(f"{LS}\\{PID}_QA_PIXEL.TIF") as qa:
    g = grid.to_crs(st.crs)
    minx, miny, maxx, maxy = g.total_bounds
    win = from_bounds(minx - 300, miny - 300, maxx + 300, maxy + 300, st.transform).round_offsets().round_lengths()
    dn = st.read(1, window=win).astype("float64")
    qpx = qa.read(1, window=win)
    transform = st.window_transform(win)

# QA_PIXEL bits: 0 fill, 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow, 5 snow
bad = np.zeros(qpx.shape, dtype=bool)
for bit in (0, 1, 2, 3, 4, 5):
    bad |= ((qpx >> bit) & 1).astype(bool)
bad |= (dn == 0)

temp_c = dn * MULT + ADD - 273.15
temp_c[bad] = np.nan
print(f"raster window {temp_c.shape}, masked pixels: {bad.mean():.1%}")

geoms = list(g.geometry)
zt = zonal_stats(geoms, temp_c, affine=transform, nodata=np.nan, stats=["mean", "count"])
zv = zonal_stats(geoms, (~bad).astype("float32"), affine=transform, nodata=-999, stats=["mean"])
grid["lst_c"] = [z["mean"] for z in zt]
grid["clear_share"] = [z["mean"] for z in zv]

ok = grid[(grid["clear_share"] >= MIN_VALID) & grid["lst_c"].notna()].copy()
print(f"cells: {len(grid)} | usable (>= {MIN_VALID:.0%} clear): {len(ok)}")
print(f"LST range in usable cells: {ok['lst_c'].min():.1f} to {ok['lst_c'].max():.1f} C, mean {ok['lst_c'].mean():.1f}")

rho, p = spearmanr(ok["heat_index"], ok["lst_c"])
print(f"\nSpearman correlation, heat index vs surface temperature: rho = {rho:.2f} (p = {p:.3g}, n = {len(ok)})")

order = ["lower", "moderate", "high", "highest"]
print("\nMean surface temperature by heat class (C):")
print(ok.groupby("heat_class")["lst_c"].mean().reindex(order).round(1).to_string())
print("\nMean surface temperature by cell type (C):")
print(ok.groupby("cell_type")["lst_c"].mean().round(1).sort_values().to_string())

grid.to_file(RES + r"\bolzano_with_lst.gpkg", driver="GPKG")

fig, ax = plt.subplots(1, 2, figsize=(13, 5))
ax[0].scatter(ok["heat_index"], ok["lst_c"], s=6, alpha=0.4)
ax[0].set_xlabel("Heat exposure index"); ax[0].set_ylabel("Landsat surface temperature (C)")
ax[0].set_title(f"Spearman rho = {rho:.2f}")
data = [ok.loc[ok["heat_class"] == c, "lst_c"] for c in order]
ax[1].boxplot(data)
ax[1].set_xticklabels(order)
ax[1].set_title("Surface temperature by heat class")
ax[1].set_ylabel("Landsat surface temperature (C)")
plt.savefig(RES + r"\landsat_validation.png", dpi=150)
print("\nsaved bolzano_with_lst.gpkg and landsat_validation.png")