# Bolzano urban heat and Nature-Based Solutions explorer

A small prototype of a decision-support tool for urban heat adaptation. It ranks the built-up part of Bolzano (Italy) in 100 m cells by heat exposure, checks that ranking against satellite-measured surface temperature, and links each high-exposure cell to a referenced catalogue of cooling measures.

**Live demo:** [ADD STREAMLIT LINK HERE]

![Dashboard screenshot](docs/screenshot.png)

Independent personal project by Samir Baidar, MSc student in Computing for Data Science (Machine Learning track) at the Free University of Bozen-Bolzano. It is a prototype for learning and demonstration, not an operational planning tool.

## Contents

1. [The question](#the-question)
2. [What the app does](#what-the-app-does)
3. [Main results](#main-results)
4. [Data](#data)
5. [Method](#method)
6. [Validation against Landsat](#validation-against-landsat)
7. [NbS catalogue](#nbs-catalogue)
8. [Limitations](#limitations)
9. [Possible next steps](#possible-next-steps)
10. [Run it locally](#run-it-locally)
11. [Reproducing the data](#reproducing-the-data)
12. [Attribution and licence](#attribution-and-licence)

## The question

Which parts of Bolzano are most exposed to urban heat, and which cooling measures (Nature-Based Solutions or other) could fit each area?

## What the app does

- Shows 1,842 built-up 100 m cells on a map, coloured either by heat exposure class or by measured Landsat surface temperature.
- Lets you change the weight given to sealed surface versus missing vegetation. The index, classes and recommendations update live.
- Reports a sensitivity check: how many of the highest-class cells stay in the highest class when the weight changes.
- Reports the rank correlation between the index and Landsat surface temperature, recomputed for the chosen weight.
- For a clicked cell, shows its class, its land use type, the contribution of sealed surface and missing vegetation, its measured temperature, and the suggested measures with their evidence and sources.
- Includes the full NbS catalogue with references.

## Main results

- The heat exposure index follows measured surface temperature: Spearman rho = 0.68 on 1,180 cells with clear Landsat data (one scene, 13 June 2021).
- The relationship also holds inside land use types, so it is not only a contrast between industrial and residential areas. Within residential cells rho is 0.58, within industrial and commercial cells 0.66, and within transport cells 0.75.
- The index separates the hottest cells well (mean surface temperature 44.7 C in the highest class against 35.8 C in the lowest), but it separates the two cooler classes poorly (about 1 C apart).
- The top-class ranking is stable: between 92% and 100% of the highest-class cells stay in that class when the sealed-surface weight moves from 0.3 to 0.9.
- Limits that matter most: one scene, 64% of cells covered, assumed sealing values, and no population data. See [Limitations](#limitations).

## Data

| Data | Source | Use |
|---|---|---|
| Land Cover / Land Use 2021, Bolzano | Copernicus Land Monitoring Service, Urban Atlas | Land use classes, sealed-surface estimate, cell types |
| Street Tree Layer 2021, Bolzano | Copernicus Land Monitoring Service, Urban Atlas | Tree cover inside built-up areas |
| Municipality boundary | OpenStreetMap contributors (via OSMnx) | Study area |
| Surface temperature | Landsat 8 Collection 2 Level-2, scene LC08_L2SP_193028_20210613_20210622_02_T1 (13 June 2021), USGS | Validation |

Landsat data citation: Earth Resources Observation and Science (EROS) Center (2020), Landsat 8-9 OLI/TIRS Level-2, Collection 2, U.S. Geological Survey, https://doi.org/10.5066/P9OGBGM6.

## Method

1. **Study area and grid.** A 100 m grid is laid over the Bolzano municipality. Cells with at least 30% artificial surfaces (Urban Atlas class 1xxxx) are kept, which gives 1,842 cells. Cells at the municipal edge are clipped, so 27 of them cover less than 2,500 m2.
2. **Sealed share.** The Urban Atlas urban fabric classes state sealing ranges in their names, and I used the midpoints: continuous 0.90, dense 0.65, medium 0.40, low 0.20, very low 0.05. For other artificial classes I assumed values: isolated structures 0.50, industrial/commercial/public units 0.80, fast roads 0.90, other roads 0.90, railways 0.60, airports 0.80. These assumptions are not measurements.
3. **Vegetation share.** Street trees (Street Tree Layer) plus urban green areas (Urban Atlas class 14xxx), capped at 1.
4. **Heat exposure index.** `index = w * sealed + (1 - w) * (1 - vegetation)`, with a default w of 0.6. The default was set from assumptions before any comparison with satellite data and was not tuned afterwards. Cells are ranked and split into quartiles: lower, moderate, high, highest. The classes are a relative ranking, not a temperature.
5. **Cell types.** Each cell is given the group of its dominant land use:

   | Cell type | Cells | Dominant land use |
   |---|---|---|
   | residential | 646 | Urban fabric classes |
   | industrial_commercial | 577 | Class 12100 |
   | other | 340 | Agricultural, forest, water and similar classes; these cells still have at least 30% artificial surface (45% on average) |
   | green | 117 | Class 14xxx (urban green, sports and leisure) |
   | transport | 111 | Roads and railways |
   | airport | 51 | Class 12400 |

6. **Recommendation rules.** Only for cells in the high and highest classes:
   - industrial/commercial: cool roof, unsealing paving, street trees
   - transport: street trees, reflective pavement
   - residential: street trees, plus green walls and pocket parks where sealing is at least 0.6, or a green corridor otherwise (and next to existing green cells)
   - other: street trees, reflective pavement
   - airport: no suggestion, because runways and aprons are outside what these rules cover

   These rules are my own design and are not validated.
7. **Validation against Landsat.** Surface temperature is computed from the ST_B10 band using the scale factors in the scene metadata (multiplier 0.00341802, offset 149.0, converted to Celsius). Cloud, cloud shadow, cirrus, snow and fill pixels are masked using QA_PIXEL. Cells with at least 50% clear pixels are kept (1,180 of 1,842) and their mean temperature is compared with the index using Spearman rank correlation.

## Validation against Landsat

The index was built from land cover only and was not fitted to the satellite data, so this is an independent check.

**Overall.** Spearman rho = 0.68 between the index and Landsat surface temperature (n = 1,180 cells).

**By heat class.** Mean surface temperature rises with the index class:

| Heat class | Cells | Mean surface temperature (C) |
|---|---|---|
| lower | 260 | 35.8 |
| moderate | 315 | 36.8 |
| high | 270 | 40.1 |
| highest | 335 | 44.7 |

**By land use type.** Land use alone explains part of the pattern, since industrial areas are both hot and scored high. To check that the index adds information beyond land use, the correlation is repeated inside each type:

| Cell type | Cells | Rho | Mean surface temperature (C) |
|---|---|---|---|
| residential | 339 | 0.58 | 38.9 |
| industrial_commercial | 408 | 0.66 | 43.0 |
| transport | 64 | 0.75 | 37.4 |
| airport | 50 | 0.63 | 44.9 |
| green | 57 | 0.32 | 38.1 |
| other | 262 | 0.06 | 34.9 |

Without the "other" group the overall rho is 0.65. The index does not rank cells inside the "other" group, which is mostly agricultural, forest and water land that only partly meets the built-up filter. Within residential cells the two hottest classes are almost the same (40.5 C for high, 41.1 C for highest, with only 37 cells in the highest).

**Sensitivity to the weight.** The weight on sealed surface was varied from 0.3 to 0.9:

| Weight on sealed surface | Highest-class cells kept | Rho |
|---|---|---|
| 0.3 | 93% | 0.61 |
| 0.4 | 96% | 0.64 |
| 0.5 | 98% | 0.66 |
| 0.6 (default) | 100% | 0.68 |
| 0.7 | 98% | 0.69 |
| 0.8 | 95% | 0.69 |
| 0.9 | 92% | 0.70 |

The ranking of the hottest cells is stable. Rho rises slightly as more weight goes to sealed surface, so the satellite data do not single out 0.6. I kept 0.6 because it was set beforehand, and choosing the weight that maximises rho on one scene would fit the index to that scene. The weak contribution of the vegetation term may partly reflect missing private gardens, which I have not tested.

**Which cells have clear data.** Cloud and shadow masking removed 662 cells (36%). The excluded cells are not a random sample:

| Cell type | Share with clear data |
|---|---|
| airport | 98% |
| other | 77% |
| industrial_commercial | 71% |
| transport | 58% |
| residential | 52% |
| green | 49% |

Excluded cells have a lower mean index (0.63 against 0.68 for included cells) and more mapped vegetation, so the validation leans toward sealed and industrial areas. The highest class is the best covered (73% of its cells).

**Green cells.** Green cells average 38.1 C, warmer than expected. Splitting them by Urban Atlas class shows why: class 14110 (green urban areas) averages 36.6 C (39 cells) and class 14200 (sports and leisure facilities) averages 41.3 C (18 cells). [CHECK CLASS NAMES AGAINST THE URBAN ATLAS LEGEND BEFORE PUBLISHING]

## NbS catalogue

The catalogue (`data/nbs_catalogue.csv`) holds eight measures with cooling evidence, source, space needed and a cost level. Sources include a review of more than 200 studies by the University of Surrey (GCARE, The Innovation 2024), a London modelling study (Brousse et al. 2024, Geophysical Research Letters), Vienna modelling studies (Zuvela-Aloise et al. 2018; a later Urban Climate study), and a multi-criteria street trees versus reflective pavements study. Reported cooling effects vary widely between studies and between local and city-wide scales, and none of the sources are about an Alpine valley city. Cost levels are my own assumptions and are labelled as such.

## Limitations

**Index and data**
- The index is a proxy from land cover, not measured temperature. Landsat gives surface temperature, which is not air temperature or what people feel.
- Sealed shares are assumed values, and the weights are assumptions. Sealed and vegetation shares are correlated (about -0.5), so the weights are not physical quantities.
- Many cells share nearly the same index (215 cells round to 0.88, almost all industrial-type or airport cells with no mapped vegetation), so the index cannot rank within that group.
- 43% of cells have no mapped vegetation. Private gardens and trees outside the Street Tree Layer are missing, so the vegetation term partly reflects missing data.
- Class 12100 (industrial, commercial, public and private units) includes non-factory buildings, so cool roof suggestions need on-site checks.
- The index picks out the hottest cells much better than it separates the cooler ones: the two lowest classes differ by only about 1 C.
- 27 cells at the municipal edge are clipped slivers under 2,500 m2, and their shares rest on very little area.

**Validation**
- One scene (13 June 2021, about 10:05 UTC, roughly midday local time), covering 64% of cells. Results on other dates or seasons may differ.
- Coverage is uneven: about half of residential and green cells have clear data, against 71% of industrial ones. Cloud was not mapped, so I cannot say where the excluded cells lie.
- Cell-level values are spatially autocorrelated, so the rank correlation should be read as descriptive and not as a formal significance test.
- The index does not rank cells inside the "other" group (rho = 0.06).

**Recommendations**
- The matching rules are a simple rule set and not a validated model. The tool does not estimate the effect of any intervention.
- Cost levels are assumptions, not estimates.

**Scope**
- No population data, so this shows exposure, not vulnerability.

## Possible next steps

- Add more Landsat scenes and dates, and map which cells are excluded by cloud.
- Use building footprints to identify large flat roofs for cool roof suggestions.
- Add population data to move from exposure to vulnerability and to prioritise areas.
- Replace assumed sealing values with an imperviousness dataset.
- Add a mock survey and a short user guide for municipal planners.

## Run it locally

```
pip install -r requirements.txt
streamlit run app.py
```

Data files needed in `data/`: `bolzano_with_lst.gpkg` (cells with index, classes, recommendations and Landsat temperature), `bolzano_recommendations.gpkg` (fallback without temperature) and `nbs_catalogue.csv`.

## Reproducing the data

The pipeline scripts are in `pipeline/`. Run them in this order after downloading the Copernicus and Landsat files:

1. `grid_v1.py`
2. `grid_v2.py`
3. `heat_index.py`
4. `heat_index_v2.py`
5. `cell_types.py`
6. `recommend.py`
7. `landsat_validation.py`

`validation_checks.py` reproduces the tables in the validation section from `bolzano_with_lst.gpkg`:

```
python pipeline/validation_checks.py data/bolzano_with_lst.gpkg
```

Paths inside the scripts point to a local Windows folder and need adjusting.

## Attribution and licence

Contains data from the Copernicus Land Monitoring Service (Urban Atlas 2021), Landsat 8 Collection 2 Level-2 data courtesy of the U.S. Geological Survey, and OpenStreetMap contributors (municipality boundary and basemap, ODbL).

Code licence: [ADD, for example MIT].