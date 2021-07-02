# GeoPandas based STAC API for swisstopo Open Geo Data

This is the main repository of the geopandas based stac reader for swisstopo data

Retrieve the the catalog as GeoPandas dataframe:

``import geopandas_stac as stac``

``df_collections = stac.getCollections(cache=False)``

From collections you can retrieve all assets, for example:

``df = stac.getAssets("ch.swisstopo.pixelkarte-farbe-pk50.noscale")``

And filter them by certain attributes, for example:

``df_krel = df_assets.query('variant == "krel"')``

Because all extents are available as GeoPandas geomtry, it is quite easy to do spatial queries.

```python
import shapely.wkt


s = "POLYGON((7.45147705078125 46.95401192579361,7.84698486328125 46.677710064644344,8.35235595703125 47.00647991252098,7.915649414062499 47.336961408985005,7.45147705078125 46.95401192579361))"
polygon = shapely.wkt.loads(s)
poly_gpd = gpd.GeoDataFrame(geometry=gpd.GeoSeries(polygon, crs="epsg:4326"))

df_polygon = gpd.sjoin(df_krel, poly_gpd, op='intersects')
```

And then you can simply get the resulting URLS:


``urls = stac.getUrlList(df_polygon)``
