# osm-rawdata

🕮 [Documentation](https://hotosm.github.io/osm-rawdata/)

These is a module to work with
[OpenStreetMap](https://www.openstreetmap.org) data using postgres and
a custom database schema. This code is derived from the [HOT Export
Tool](https://export.hotosm.org/en/v3/),
[osm-fieldwork](https://pypi.org/project/osm-fieldwork/), and
[Underpass](https://github.com/hotosm/underpass), and the [Raw Data
API](https://github.com/hotosm/raw-data-api), which is the new FastAPI
backend for the HOT Export Tool.

Since multiple projects need to do data extracts from OpenStreetMap in
a flexible way, this was designed to have a single body of code to
maintain.

## Installation

To install osm-rawdata, you can use pip. Here are two options:

- Directly from the main branch:
  `pip install git+https://github.com/hotosm/osm-rawdata.git`

- Latest on PyPi:
  `pip install osm-rawdata`

## Using the Container Image

- osm-rawdata scripts can be used via the pre-built container images.
- These images come with all dependencies bundled, so are simple to run.

Run a specific command:

```bash
docker run --rm -v $PWD:/data ghcr.io/hotosm/osm-rawdata:latest geofabrik <flags>
```

Run interactively (to use multiple commands):

```bash
docker run --rm -it -v $PWD:/data ghcr.io/hotosm/osm-rawdata:latest
```

> Note: the output directory should always be /data/... to persist data.

## The Database Schema

This project is heavily dependant on postgres and postgis. This schema
was optimized for data anaylsis more than display purposes. The
traditional schema use for OSM shows how it has evolved over the
years. Some tags are columns (usually empty), and others get put into
an **hstore** _tag_ column where they have to be accessed
directly. One big change in this datbase schema is all the tags are in
a single column, reducing the data size considerably, while also being
easier to query in a consistent manner. In the past a developer had to
keep track of what was a column, and what was in the _tags_ column,
which was inefficient.

This schema has 4 tables, similar to the traditional ones. OSM data is
imported using [osm2pgsql](https://osm2pgsql.org/) but uses a
[lua](http://www.lua.org/) script to create the custom
schema. This module's usage is all read-only, as Underpass can keep
the raw data updated every minute, and we just want to access that
data.

Things get more interesting as this module supports both a local
database and a remote one. They use different query languages. To
simplify this, a configuration file is used, which then generates the
proper query syntax.

## The Config File

This reads in two different formats that describe the eventualy SQL
query. The YAML format was originally used by Export Tool, but later
abandoned for a JSON format. The YAML format was adopted by the
osm-fieldwork project before this transistion happened, so uses an
enhanced version to define the queries.

The JSON format is also supported, both parsing the config file and
also generating that query from a YAML config file.

# The files

## geofabrik.py

This is a simple utility to download a file from GeoGFabrik.

## config.py

This class parses either then JSON or YAML config file formatted
files, and creates a data structure used later to generater the
database query.

## postgres.py

This class handles working with the postgres database. It sets up the
connections, and handles processing the results from the queries.
