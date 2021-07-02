###############################################################################
#### Collection of useful functions for the swisstopo STAC API
####
#### Licensed under MIT License
###############################################################################
#
# Copyright (c) 2021 Martin Christen, martin.christen@fhnw.ch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

###############################################################################
# Note: if you looking for better STAC support, use pystac instead 
# https://pystac.readthedocs.io/en/latest/ )
#
# This module swisstopogeodata is a **simplification** to quickly access and 
# process data. Main focus is pandas/geopandas support.
###############################################################################

# Version 0.4
#
# New: proper json handling
#
#
# Todo:
#    * Vector data -> geopandas
#    * Caching all queries
#    * Raster Utilities



import requests
import os
import hashlib
import pandas as pd
import geopandas as gpd
from urllib.request import urlopen
from shapely.geometry import shape
import json


baseurl = "https://data.geo.admin.ch/api/stac/v0.9"

#------------------------------------------------------------------------------

def do_download(url, verbose=True, cache=True):
    cachedir = "_geodatacache"
    urlhash = hashlib.md5(bytearray(url, encoding="utf-8"))
    filename = urlhash.hexdigest()
    if not os.path.exists(cachedir):
        os.mkdir(cachedir)
    if os.path.exists(cachedir + "/" + filename) and cache:
        if verbose:
            print("cache hit", urlhash.hexdigest(), end="\r")
        file = open(cachedir + "/" + filename)
        result = json.loads(file.read())
        file.close()
        return result

    if verbose:
        if cache:
            print("Downloading and caching", url, end="\r")
        else:
            print("Downloading", url, end="\r")
    response = requests.get(url)
    if cache:
        file = open(cachedir + "/" + filename, "w")
        file.write(response.text)
        file.close()
    result = json.loads(response.text)
    
    return result
    
#------------------------------------------------------------------------------

def getCollections(cache=True):
    collections = baseurl + "/collections"

    result = do_download(collections,verbose=False,cache=cache)

    return pd.DataFrame.from_dict(result["collections"])

#------------------------------------------------------------------------------

def getCollectionList(cache=True):
    lst = []
    def gencoll_lst(row):
        uid = row['id']
        lst.append(uid)
    
    df = getCollections(cache)
    r = df.apply(gencoll_lst, axis=1)
    return lst

#------------------------------------------------------------------------------

def getFeatures(collectionname, verbose=True, limit=0, cache=True):
    features = [] # Start with an empty list of features
    url = baseurl + f"/collections/{collectionname}/items"

    done = False
    cnt = 0
    while not done:
        result = do_download(url, verbose)
        cnt += 1

        features = features + result['features']

        url = ""
        for link in result['links']:
            if link['rel'] == 'next':
                url = link['href']

        if url == "":
            done = True
            
        if limit>=cnt:
            done = True
            
    result = pd.DataFrame.from_dict(features)
    result.rename(columns={'geometry':'raw_geometry'}, inplace=True)
    
    geom = []
    def convert_geometry(data):
        geom.append(shape(data['raw_geometry']))
    
    result.apply(convert_geometry, axis=1)
    result.drop('raw_geometry', inplace=True, axis=1)
    
    result_gdf = gpd.GeoDataFrame(result, geometry=geom, crs="epsg:4326")
    
    return result_gdf

#------------------------------------------------------------------------------

def genAssets(features_df):
    assetdata = {'name': [],
              'type': [],
              'bbox': [],
              'created': [],
              'updated': [],
              'href': [],
              'proj': [],
              'gsd': [],
              'variant': [],
              'checksum': [],
              'geometry': [],
               }

    def iterateAssets(data):
        asset = data["assets"]
        geometry = data['geometry']
        bbox = data['bbox']
        for key in asset:
            name = asset[key]
            
            assetdata['name'].append(key)
            
            etype = name['type']
            assetdata['type'].append(etype)
            
            assetdata['bbox'].append(bbox)
            
            created = name['created']
            updated = name['updated']
            assetdata['created'].append(created)
            assetdata['updated'].append(updated)
            
            href = name['href']
            assetdata['href'].append(href)
            proj = name['proj:epsg']
            assetdata['proj'].append(proj)
            
            
            if "geoadmin:variant" in name: # some features have variants, some don't
                variant = name['geoadmin:variant']
            else:
                variant = "base"   # let's call single variants "base"
                
            assetdata['variant'].append(variant)
                
            if "eo:gsd" in name:
                gsd = name['eo:gsd']
                assetdata['gsd'].append(gsd)
            else:
                assetdata['gsd'].append(0)
                
            checksum = name['checksum:multihash']
            assetdata['checksum'].append(checksum)
            assetdata['geometry'].append(geometry)
            
    features_df.apply(iterateAssets,axis=1) 
    df_assets = gpd.GeoDataFrame(assetdata, crs="epsg:4326")
    
    return df_assets

#------------------------------------------------------------------------------

def getAssets(collectionname, verbose=False, cache=True):
    df = getFeatures(collectionname, verbose=verbose, cache=cache)
    df_assets = genAssets(df)
    return df_assets

#------------------------------------------------------------------------------

def getUrlList(df):
    lst = []
    def gen_dllist(row):
        filename = row['href']
        lst.append(filename)

    r = df.apply(gen_dllist, axis=1)
    return lst

#------------------------------------------------------------------------------

def download(url, destfile, overwrite=True):
    print("Downloading", destfile, "from", url)

    if os.path.exists(destfile) and not overwrite:
        #print("File already exists, not overwriting.")
        return
    
    response = urlopen(url) 
    info = response.info()
    cl = info["Content-Length"]
    
    if cl != None:
        filesize = int(cl)
        currentsize = 0
        
        with open(destfile, 'wb') as f:
            while True:
                chunk = response.read(16*1024)
                currentsize += len(chunk)
                
                if not chunk:
                    break
                f.write(chunk)
                percent = int(100*currentsize/filesize)
                
                bar = "*"*(percent)
                bar += "-"*((100-percent))
                print('\r{}% done \t[{}]'.format(percent, bar), end='')
        print("")
        
    else:
        print("Downloading please wait... (filesize unknown)")
        with open(destfile, 'wb') as f:
            while True:
                chunk = response.read(16*1024)
                if not chunk:
                    break
                f.write(chunk)
               
            
#------------------------------------------------------------------------------            
#------------------------------------------------------------------------------
# Hilfsfunktionen für swisstopo swissALTI3D und swissimage

# Zu einem PUNKT die entsprechende url des swissALTI3D Datensatzes zurückgeben.
# Format: TIFF, GSD 0.5m
# Das Resultat ist eine Liste mit 0 oder 1 URL-Zeichenetten.

def getSwissalti3d_50cm_pt(lng, lat):
    df = stac.getAssets("ch.swisstopo.swissalti3d")

    df_geotiff = df.query('type == "image/tiff; application=geotiff; profile=cloud-optimized"')
    df_geotiff = df_geotiff.query("gsd == 0.5")

    point = shapely.geometry.Point(lng, lat)
    dfpoint = gpd.GeoDataFrame(geometry=gpd.GeoSeries(point, crs="epsg:4326"))

    df_result = gpd.sjoin(df_geotiff, dfpoint, op='contains')

    return stac.getUrlList(df_result)

#------------------------------------------------------------------------------
# Eine Hilfsfunktion, welche zu einem POLYGON die entsprechenden swissALTI3D Bilder zurückgibt.
# Format: TIFF, GSD 0.5m
# Das Resultat ist eine Liste mit 0 oder n URL-Zeichenetten.

def getSwissalti3d_50cm_poly(wkt):
    df = stac.getAssets("ch.swisstopo.swissalti3d")

    df_geotiff = df.query('type == "image/tiff; application=geotiff; profile=cloud-optimized"')
    df_geotiff = df_geotiff.query("gsd == 0.5")

    
    polygon = shapely.wkt.loads(wkt)
    dfpoly = gpd.GeoDataFrame(geometry=gpd.GeoSeries(polygon, crs="epsg:4326"))
    df_result = gpd.sjoin(df_geotiff, dfpoly, op='intersects')
    
    return stac.getUrlList(df_result)

#------------------------------------------------------------------------------

# Zu einem PUNKT die entsprechende url des swissimage Datensatzes zurückgeben.
# Das Resultat ist eine Liste mit 0 oder 1 URL-Zeichenetten.

def getSwissimage_pt(lng, lat, gsd=0.1):
    df = stac.getAssets("ch.swisstopo.swissimage-dop10")

    df_geotiff = df_geotiff.query(f"gsd == {gsd}")

    point = shapely.geometry.Point(lng, lat)
    dfpoint = gpd.GeoDataFrame(geometry=gpd.GeoSeries(point, crs="epsg:4326"))

    df_result = gpd.sjoin(df_geotiff, dfpoint, op='contains')

    return stac.getUrlList(df_result)

#------------------------------------------------------------------------------

def getSwissimag_poly(wkt, gsd=0.1):
    df = stac.getAssets("ch.swisstopo.swissimage-dop10")

    df_geotiff = df_geotiff.query(f"gsd == {gsd}")

    polygon = shapely.wkt.loads(wkt)
    dfpoly = gpd.GeoDataFrame(geometry=gpd.GeoSeries(polygon, crs="epsg:4326"))
    df_result = gpd.sjoin(df_geotiff, dfpoly, op='intersects')
    
    return stac.getUrlList(df_result)


#------------------------------------------------------------------------------

