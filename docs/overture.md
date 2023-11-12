# Overture Map Data

The Overture Foundation (<https://www.overturemaps.org>) has been
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

While Overture recommends using [Amazon
Athena](https://aws.amazon.com/athena/) or [Microsoft
Synapse](https://learn.microsoft.com/en-us/azure/synapse-analytics/get-started-create-workspace),
you can also use a database.

Thee two primary databases are [DuckDB](https://duckdb.org/), and
[Postgres](https://www.postgresql.org/about/news/parquet-s3-fdw-021-released-2379/),
both of which have Parquet support. You can now also use [ogr2ogr](https://gdal.org/drivers/vector/parquet.html) to
import a parquet file into postgres. In these cases the database
schema will resemble the Overture schema. Since HOT maintains it's own
database schema that is also optimized for query performance, you can
use the [importer](https://hotosm.github.io/osm-rawdata/importer/)
program to import into the Underpass schema. The importer utility can
parse any of the data files that are using the V2 schema into GeoJson.

## Schema

There are two versions of the file schema. The original schemas had
less columns in it, and each data type had a schema oriented towards
that data type. The new schema (Oct 2023) is larger, but all the data
types are supported in the same schema.

The schema used in the Overture data files is [documented here](https://docs.overturemaps.org/reference). This document is just a
summary with some implementation details.

### Buildings

The current coverage area is primarily the US, with New Zealand, and
some random citites in Europe like Berlin. This is excluding the
OpenStreetMap and Microsoft ML Buildings, which do have global
coverage. But as those are available from other sources, which will
often be more up to data than the Overture anyway. Conflation reguires
fresh data.

The data appears to not be processed for duplicates or bad geometries,
but that is what the [Conflator](https://github.com/hotosm/conflator)
and [Underpass](https://github.com/hotosm/underpass/wiki) projects
are for, to clean the data for possible imports. The license is Odbl,
so suitable for OSM.

### The current list of buildings datasets in V1 (July 2023) is

- Austin Building Footprints Year 2013 2D Buildings
- Boston BPDA 3D Buildings
- City of Cambridge, MA Open Data 3D Buildings
- Denver Regional Council of Governments 2D Buildings
- Esri Buildings | Austin Building Footprints Year 2013 2D Buildings
- Esri Buildings | Denver Regional Council of Governments 2D Buildings
- Esri Community Maps
- Miami-Dade County Open Data 3D Buildings
- OpenStreetMap
- Microsoft ML Buildings
- NYC Open Data 3D Buildings
- Portland Building Footprint 2D Buildings
- USGS Lidar
- Washington DC Open Data 3D Buildings

### The current list of buildings datasets in V2 (Oct 2023) is

- Portland Building Footprint 2D Buildings
- Esri Community Maps
- USGS Lidar
- Esri Buildings | Austin Building Footprints Year 2013 2D Buildings
- Esri Buildings | Denver Regional Council of Governments 2D Buildings
- City of Cambridge, MA Open Data 3D Buildings
- Miami-Dade County Open Data 3D Buildings
- Washington DC Open Data 3D Buildings
- Denver Regional Council of Governments 2D Buildings
- Boston BPDA 3D Buildings
- NYC Open Data 3D Buildings
- Austin Building Footprints Year 2013 2D Buildings
- OpenStreetMap
- Microsoft ML Buildings

The primary columns of interest to OSM are the number of building
floors, the height in meters, and the name if it has one. These
columns are not set in all of the datasets, but where they exist, they
can be added to OSM during conflation.

As a warning, the USGS Lidar dataset has many really bad building
geometries, so it's only the height column that is useful, if
accurate. This dataset does appear to have many buildings not in the
other datasets, but the geometries are barely usable. Conflation does
add these as new buildings though, but will often require manual
tracing to fix the geometries. This dataset is useful for finding many
missing buildings, but is US only.

### Places

The _places_ data are POIs of places. This appears to be for
amenities, and contains tags related to that OSM category. It has
global coverage and is multi-lingual. This dataset is from Meta and
the Microsoft. This dataset is licensed
[CDLA](https://osmfoundation.org/wiki/CDLA_permissive_compatibility),
which is a new license, but has been approved for imports into OSM.

The columns that are of interest in the data to OSM are:

- freeform - The address of the amenity, although the format is not
  consistent
- socials - An array of social media links for this amenity.
- phone - The phone number if it has one
- websites - The website URL if it has one
- value - The name of the amenity if known
- locality - The location on the planet, usually a city

A quick scan seems to show personal data and not just amenities. There
doesn't appear to be sufficient metadata to filter this automatically
without following the link to their facebook page. There are many
amenities though, but has the same problem.

### Highways

In the current highway _segment_ data files, the only source currently
is OSM. In that cases it's better to use up to date OSM data. It'll be
interesting to see if Overture imports the publically available
highway datasets from the USGS, or some state governments. That would
be very useful. But otherwise the highway data is useless to improve
map data.

The Overture _segments_ data files are equivalent to an OSM way, with
tags specific to that highway linestring. There are separate data
files for _connections_, that are equivalant to an OSM relation. Once
again though, since all the data is currently from OSM, it's better to
just use OSM data.

### Admin Boundaries And Base Data

Currently all the data in these datsets is from OSM, so there is no
reason to care about these files.

# Special Columns

## names

The names column can have 4 variations on the name. Each may also have
a language value as well.

- common
- official
- alternate
- short

Each of these can have multiple values, each of which consists of a
value and the language.

## sources

The sources column is an array of with two entries. The first entry is
the name of the dataset, and where it exists, a _recordID_ to
reference the source dataset. For OSM data, the recordID has 3
sub-fields. The first character is the type, _w_ (way), _n_ (node), or
_l_ (line). The second is the OSM ID, and the third with a _v_ is the
version of the feature in OSM.

For example: \*w**\*123456**v2 is a way with ID 123456 and is version 2.
