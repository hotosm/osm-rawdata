# JSON Config Syntax

This syntax is used by the [HOT Export
Tool](https://export.hotosm.org/en/v3/), and it's FastAPI backend,
[Raw Data API](https://github.com/hotosm/raw-data-api). The YAML
format was considered to be too simple for complex queries, so this
JSON format was created to replace it. This is identical the the
format used by those tools.

## Geometry

This is a GeoJson geometry that defines the project boundary. Since
the database is huge, this limits the area the query is performed in.

## Filters

The filters do the real work of this format. The _tags_ keyword is
followed by the desired geometry, which determine which database
tables get searched. If _all_geometry_ is supplied, then all the
tables are queried. It can also be _centroid_, which then returns onl
points.

The syntax is the same for the **join_or** keyword, or the
**join_and** keyword. It's a list of keyword/value pairs. If it's an
empty list, this is the equivalant of using _IS NOT NULL_ in SQL. If
it has a value instead, then only features with that value are
returned.

## Centroid

This is true or false on whether the result should only be centroids
of all the geometries. The default is false if this is not present.

# Example

Unlike the [YAML](https://hotosm.github.io/osm-rawdata/yaml/) format
that generates an SQL query, the raw data API wants this JSON file.
This can be generated however from the YAML config file. If used as
a config file, an identical version is generated from the parsed
config data. This way it can be used for both input and output.

This config file is for highway extracts.

    {
     "geometry": {
      "type": "Polygon",
      "coordinates": [
       [
        [
         [
          -105.390892,
          39.743926
         ],
         # More coordinates remove
        ]
       ]
      ]
     },
     "filters": {
      "tags": {
       "all_geometry": {
        "join_or": {
         "highway": [],
         "waterway": []
        },
        "join_and": {
         "bridge": []
        }
       }
      }
     },
    }
