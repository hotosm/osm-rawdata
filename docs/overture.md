# Overture Map Data

The Overture Foundation (https://www.overturemaps.org) has been
recently formed to build a competitor to Google Maps. The plan is to
use OpenStreetMap (OSM) data as a baselayer, and layer other datasets
on top. The currently available data (July 2023) has 13 different
datasets in addition to the OSM data. It is [available
here](https://overturemaps.org/download/). It also includes a snapshot
of OSM data from the same time frame. Other than the OSM data and [MS
Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints),
all the current additional data is US specific, and often contains
multiple copies of the same dataset, but from different organization.

The Overture files are in [Parquet](https://parquet.apache.org/)
format, which uses [Arrow](https://arrow.apache.org/) to store the
data in a tabular fashion. The files are large, about 1.2G most of the
time. Each file has features spread across the planet, instead of a
subset in a geographical region. If you wish to get all the data for a
region, you have to load all 120 files into a database.

## Schema

The schema used in the Overture data files is [documented here](
https://docs.overturemaps.org/reference). This document is just a
summary with some implementation details.

### Buildings

* id: tmp_[Giant HEX number]
* updatetime: The last time a feature was updated
* version: The version of the feature
* names: The names of the buiding
* height: The heigth of the feature in meters
* numfloors: The numbers of floors in the building
* class: The type of building, residential, commericial, etc...
* geometry: The feature geometry
* sources: A list of dataset sources with optional recordId
* level: This appears to be unused
* bbox: A bounding box of the feature

The current list of buildings datasets is:

* Austin Building Footprints Year 2013 2D Buildings
* Boston BPDA 3D Buildings
* City of Cambridge, MA Open Data 3D Buildings
* Denver Regional Council of Governments 2D Buildings
* Esri Buildings | Austin Building Footprints Year 2013 2D Buildings
* Esri Buildings | Denver Regional Council of Governments 2D Buildings
* Esri Community Maps
* Miami-Dade County Open Data 3D Buildings
* OpenStreetMap
* Microsoft ML Buildings
* NYC Open Data 3D Buildings
* Portland Building Footprint 2D Buildings
* USGS Lidar
* Washington DC Open Data 3D Buildings

# Special Columns

## names

The names column can have 4 variations on the name. Each may also have
a language value as well.

* common
* official
* alternate
* ahort

## sources

The sources column is an array of with two entries. The first entry is
the name of the dataset, and where it exists, a *recordID* to
reference the source dataset. For OSM data, the recordID has 3
sub-fields. The first character is the type, *w* (way), *n* (node), or
*l* (line). The second is the OSM ID, and the third with a *v* is the
version of the feature in OSM.

For example: *w***123456**v2 is a way with ID 123456 and is version 2.
