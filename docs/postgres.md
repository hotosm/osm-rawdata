# Postgres

This is a simple command line interface that uses the contained
classes to make a data extract from OSM. This program extracts data
from a local postgres data, or the remote Underpass one. A boundary
polygon is used to define the area to be covered in the
extract. Optionally a data file can be used.

	options:
	--help(-h)               show this help message and exit
	--verbose(-v)            verbose output
	--uri(-u) URI            Database URI
	--boundary(-b) BOUNDARY  Boundary polygon to limit the data size
	--sql(-s) SQL            Custom SQL query to execute against the database
	--all(-a) ALL            All the geometry or just centroids
	--config(-c) CONFIG      The config file for the query (json or yaml)
	--outfile(-o) OUTFILE    The output file
