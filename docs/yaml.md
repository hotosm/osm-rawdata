# YAML Config Syntax

The YAML format is simpler than the JSON one, and is the format used
by the [osm-fieldwork](https://pypi.org/project/osm-fieldwork/)
project and [the FMTM](https://github.com/hotosm/fmtm) project for use
in field data collection. This is used for canned datbase queires that
are used to make data extracts for ODK Collect.

## select

If let blank, the tags in the keep section and where sections are used
to return a subset of tags & values, instead of all the tags.

## from

This is a list of the database tables. By default these are the tables
used in the custom database schema created with the included raw.lua
script for osm2pgsql.

The tables are:

* nodes
* relations
* ways_line
* ways_poly

## where

The where section is a bit more complicated because we need to support
a mix of OR and AND arguments. The is a limit to how complicated this
can get, but sometimes it's easier to just do a little manual cleanup
with the results.

The syntax is the same for the **join_or** keyword, or the
**join_and** keyword. If you want to query for any value of the
keyword, ass *not_null*, which later gets turned into *IS NOT NULL* in
SQL. It has a value associated with the keyword, then that is the only
value searechihng for.

## keep

The tags in the keep field are the ones we want returned in the SQL
query, but aren't part of the where section. Othwise they fail to
appear in the results.

# Example

This config file is for building extracts.


	select:
	  - name: title
	from:
		- nodes
		- ways_poly
	where:
	  tags:
		- join_or:
			- { building: yes, amenity: not null }
		- join_and:
			- { building:material: wood }
	keep:
		- building:levels
		- building:material
		- roof:material
		- roof:shape
		- roof:levels
		- cusine
		- convenience
		- diesel
		- version

That then generates this SQL query:

	SELECT ST_AsText(geom), osm_id, version, tags->>'building:levels',
		tags->>'building:material', tags->>'roof:material',
		tags->>'roof:shape', tags->>'roof:levels', tags->>'cusine',
		tags->>'convenience', tags->>'diesel', tags->>'version',
		tags->>'building', tags->>'amenity',
		tags->>'building:material' FROM ways_view WHERE (
		tags->>'building'='yes' OR tags->>'amenity' IS NOT NULL)  AND
		tags->>'building:material'='wood'
