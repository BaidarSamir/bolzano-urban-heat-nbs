import os

import branca.colormap as bcm
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Bolzano urban heat and NbS explorer", layout="wide")

LABELS = ["lower", "moderate", "high", "highest"]
COLORS = {"lower": "#ffffb2", "moderate": "#fecc5c", "high": "#fd8d3c", "highest": "#bd0026"}
DEFAULT_W = 0.6
MODE_CLASS = "Heat exposure class"
MODE_LST = "Landsat surface temperature"


@st.cache_data
def load():
    path = "data/bolzano_with_lst.gpkg"
    if not os.path.exists(path):
        path = "data/bolzano_recommendations.gpkg"
    cells = gpd.read_file(path).to_crs(4326)
    cat = pd.read_csv("data/nbs_catalogue.csv")
    if "near_green" not in cells.columns:
        cells["near_green"] = False
    if "lst_c" not in cells.columns:
        cells["lst_c"] = np.nan
        cells["clear_share"] = 0.0
    # Only keep temperatures for cells with enough clear pixels (same rule as the validation script)
    cells["lst_show"] = cells["lst_c"].where(cells["clear_share"] >= 0.5)
    # Airport land (Urban Atlas 12400) is its own type: runways and aprons are not covered by the rules
    cells.loc[cells["dominant_code"].astype(str) == "12400", "cell_type"] = "airport"
    return cells, cat


def score(cells, w):
    """Heat exposure index and relative class (quartiles) for a given weight on sealed surface."""
    veg = (cells["tree_share"] + cells["ugreen_share"]).clip(upper=1)
    idx = w * cells["sealed_share"] + (1 - w) * (1 - veg)
    cls = pd.qcut(idx.rank(method="first"), 4, labels=LABELS).astype(str)
    return idx, cls


def recommend(cell_type, sealed, near_green, heat_class):
    if heat_class not in ("high", "highest"):
        return []
    if cell_type == "airport":
        return []
    if cell_type == "industrial_commercial":
        recs = ["cool_roof", "unseal_paving", "street_trees"]
    elif cell_type == "transport":
        recs = ["street_trees", "cool_pavement"]
    elif cell_type == "residential":
        recs = (["street_trees", "green_wall", "pocket_park"] if sealed >= 0.6
                else ["street_trees", "green_corridor"])
        if near_green and "green_corridor" not in recs:
            recs.insert(1, "green_corridor")
    else:
        recs = ["street_trees", "cool_pavement"]
    return recs[:3]


cells, cat = load()
names = dict(zip(cat["id"], cat["name"]))
has_lst = bool(cells["lst_show"].notna().sum() > 30)

st.title("Bolzano urban heat and Nature-Based Solutions explorer")
st.caption("Prototype. Heat exposure is a proxy computed from Urban Atlas 2021 land cover and street trees "
           "(100 m cells). It is not measured temperature. Cost levels in the catalogue are assumptions.")

with st.sidebar:
    st.header("Index settings")
    w = st.slider("Weight on sealed surface", 0.3, 0.9, DEFAULT_W, 0.05,
                  help="Index = w x sealed share + (1 - w) x (1 - vegetation share). "
                       "Vegetation = street trees + urban green.")
    st.caption(f"Weight on missing vegetation: {1 - w:.2f}")

    st.header("Map")
    modes = [MODE_CLASS] + ([MODE_LST] if has_lst else [])
    mode = st.radio("Color map by", modes)

    st.header("Filters")
    classes = st.multiselect("Heat class", LABELS, default=LABELS)
    types = st.multiselect("Cell type", sorted(cells["cell_type"].unique()),
                           default=sorted(cells["cell_type"].unique()))

    st.header("Legend")
    for lab in LABELS:
        st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{COLORS[lab]};"
                    f"border:1px solid #888;margin-right:8px'></span>{lab}", unsafe_allow_html=True)
    st.caption("Classes are quartiles of the index: a relative ranking of the built-up cells, "
               "not a temperature.")

# Recompute index, classes and recommendations for the chosen weight
idx, cls = score(cells, w)
_, cls_default = score(cells, DEFAULT_W)
cells["heat_index"] = idx
cells["heat_class"] = cls
cells["rec_ids"] = [recommend(t, s, g, c) for t, s, g, c in
                    zip(cells["cell_type"], cells["sealed_share"], cells["near_green"], cells["heat_class"])]
cells["rec_names"] = cells["rec_ids"].apply(lambda ids: ", ".join(names[i] for i in ids))

top_now = set(cells.index[cells["heat_class"] == "highest"])
top_default = set(cells.index[cls_default == "highest"])
stay = len(top_now & top_default) / max(len(top_default), 1)

rho, n_lst = None, 0
if has_lst:
    ok = cells["lst_show"].notna()
    n_lst = int(ok.sum())
    rho = cells.loc[ok, "heat_index"].rank().corr(cells.loc[ok, "lst_show"].rank())

view = cells[cells["heat_class"].isin(classes) & cells["cell_type"].isin(types)]
disp = view[["cell_id", "heat_class", "heat_index", "cell_type", "sealed_share",
             "tree_share", "ugreen_share", "rec_names", "lst_show", "geometry"]].copy()
for c in ["heat_index", "sealed_share", "tree_share", "ugreen_share"]:
    disp[c] = disp[c].round(3)
disp["lst_show"] = disp["lst_show"].round(1)

m = folium.Map(location=[46.4983, 11.3548], zoom_start=13, tiles="OpenStreetMap")

if mode == MODE_LST:
    lo, hi = np.nanpercentile(cells["lst_show"], [2, 98])
    cmap = bcm.LinearColormap(["#ffffb2", "#fecc5c", "#fd8d3c", "#bd0026"], vmin=lo, vmax=hi,
                              caption="Landsat surface temperature (C), 13 June 2021")

    def style(f):
        t = f["properties"].get("lst_show")
        if t is None or (isinstance(t, float) and np.isnan(t)):
            return {"fillColor": "#bbbbbb", "color": "none", "fillOpacity": 0.35}
        return {"fillColor": cmap(min(max(t, lo), hi)), "color": "none", "fillOpacity": 0.7}

    tip = folium.GeoJsonTooltip(fields=["heat_class", "lst_show", "cell_type"],
                                aliases=["Heat class", "Surface temp (C)", "Cell type"])
    cmap.add_to(m)
else:
    def style(f):
        return {"fillColor": COLORS[f["properties"]["heat_class"]], "color": "none", "fillOpacity": 0.65}

    tip = folium.GeoJsonTooltip(fields=["heat_class", "cell_type", "rec_names"],
                                aliases=["Heat class", "Cell type", "Suggested"])

folium.GeoJson(disp, style_function=style, tooltip=tip).add_to(m)

left, right = st.columns([3, 2])
with left:
    out = st_folium(m, height=620, use_container_width=True,
                    returned_objects=["last_active_drawing"])
with right:
    st.metric("Highest-class cells unchanged vs default weights (0.6)", f"{stay:.0%}",
              help="Sensitivity check: how many of the cells in the top quartile under the default "
                   "weights are still in the top quartile with your chosen weight.")
    if has_lst:
        st.metric(f"Rank correlation with Landsat surface temperature (n = {n_lst} clear cells)",
                  f"{rho:.2f}",
                  help="Spearman correlation between the index and Landsat 8 surface temperature "
                       "(13 June 2021, about 10:05 UTC). Choosing a weight to maximise this number "
                       "would fit the index to one scene, so use it as a check, not a target.")

    st.subheader("Selected cell")
    sel = (out or {}).get("last_active_drawing")
    if sel and sel.get("properties"):
        p = sel["properties"]
        veg = min(p["tree_share"] + p["ugreen_share"], 1)
        c_sealed = w * p["sealed_share"]
        c_veg = (1 - w) * (1 - veg)
        st.write(f"**Heat class:** {p['heat_class']} (index {p['heat_index']:.2f})")
        st.write(f"**Type:** {p['cell_type']}")
        st.write(f"Sealed share {p['sealed_share']:.2f}, street trees {p['tree_share']:.2f}, "
                 f"urban green {p['ugreen_share']:.2f}")
        if has_lst:
            t = p.get("lst_show")
            if t is None:
                st.write("**Landsat surface temperature:** no clear data for this cell")
            else:
                st.write(f"**Landsat surface temperature:** {t:.1f} C (13 June 2021)")
        st.caption("What drives this cell's index")
        med = cells[["sealed_share", "tree_share", "ugreen_share"]].median()

        st.markdown("**1. Contribution to the index**")
        st.bar_chart(pd.DataFrame({"Contribution": [c_sealed, c_veg]},
                                  index=["Sealed surface", "Missing vegetation"]),
                     horizontal=True, height=150)

        st.markdown("**2. Difference from the median built-up cell**")
        st.bar_chart(pd.DataFrame({"Difference": [p["sealed_share"] - med["sealed_share"],
                                                  p["tree_share"] - med["tree_share"],
                                                  p["ugreen_share"] - med["ugreen_share"]]},
                                  index=["Sealed surface", "Street trees", "Urban green"]),
                     horizontal=True, height=180)
        st.caption("Bars to the right: more than the typical cell. Bars to the left: less.")
        if p["rec_names"]:
            st.write("**Suggested solutions:** " + p["rec_names"])
            wanted = p["rec_names"].split(", ")
            st.dataframe(cat[cat["name"].isin(wanted)][["name", "cooling_evidence", "source",
                                                       "space_need", "cost_level"]],
                         hide_index=True)
        elif p["cell_type"] == "airport":
            st.write("No suggestion: the rule set does not cover airport land (runways, aprons).")
        else:
            st.write("No recommendation, since this cell is not in the high or highest classes.")
    else:
        st.write("Click a cell on the map.")

    st.subheader("Cells in current view")
    st.write(view["heat_class"].value_counts().reindex(LABELS).fillna(0).astype(int))

with st.expander("Method and limitations"):
    st.markdown(
        "- **Cells:** 100 m grid over the built-up part of Bolzano (at least 30% artificial surfaces).\n"
        "- **Sealed share:** approximate, from Urban Atlas 2021 class names (assumed midpoints of the sealing ranges).\n"
        "- **Vegetation:** street trees (Street Tree Layer) plus urban green areas. Private gardens are not mapped.\n"
        "- **Index:** weighted sum of sealed share and missing vegetation, ranked into quartiles.\n"
        "- **Validation:** one Landsat 8 Level-2 scene (13 June 2021, about 10:05 UTC), cloud, shadow and snow "
        "masked, cells with at least 50% clear pixels. Surface temperature is not air temperature.\n"
        "- **Recommendations:** simple rules based on land use type and cell context, not a validated model. "
        "Airport cells are shown but get no suggestion.\n"
        "- **Not yet done:** population data, building footprints, more than one satellite scene."
    )

with st.expander("NbS catalogue and sources"):
    st.dataframe(cat, hide_index=True)

st.caption("Prototype. Heat exposure is a proxy computed from Urban Atlas 2021 land cover and street trees "
           "(100 m cells). Only the built-up part of Bolzano is shown (cells with at least 30% artificial "
           "surface), so forests and farmland on the slopes are outside the study area. "
           "It is not measured temperature. Cost levels in the catalogue are assumptions.")