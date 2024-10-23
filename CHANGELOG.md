## 0.4.0 (2024-10-24)

## 0.3.3 (2024-10-14)

### Fix

- geofabrik hyphenated region path (#33)

### Refactor

- move raw-data import related scripts to subdir

## 0.3.2 (2024-08-12)

### Fix

- raw-data-api changed Export.geojson --> RawExport.geojson (#30)
- allow raw-data-api call to return if FAILURE response
- param spelling mistake PostgresClient.url --> .uri

## 0.3.1 (2024-08-05)

### Fix

- do not continue to poll raw-data-api on failure (#28)
- Add AS geometry to make parsing the results cleaner, fix duplicate columns in SELECT (#25)
- Fix typo, args.uri, not args.url (#22)
- Process the refs for ways when using a local database (#20)

### Refactor

- revert default line length 132 --> 88 char

## 0.3.0 (2024-05-20)

### Feat

- update env var UNDERPASS_API_URL --> RAW_DATA_API_URL

## 0.2.4 (2024-04-07)

### Fix

- return None if raw-data-api error dict response (log error)
- improve check for raw-data-api success

## 0.2.3 (2024-02-15)

### Fix

- improve yaml config parsing edge cases

### Refactor

- better index handling for postgres get geom types

## 0.2.2 (2024-02-14)

### Fix

- handle both yaml and json BytesIO PostgresClient config
- handle empty tags in yaml format (not null)
- reading of bytesio config file seeking
- case when geometry is not set during init
- Move GetRecordCount() and getPage() here as they're now asyncpg specific
- allow parsing geojson string for execQuery

### Refactor

- fix linting errors for config.py
- remove clip_to_aoi option (default in raw-data-api)

## 0.2.1 (2024-02-09)

### Fix

- improve robustness of raw data api polling checks

### Refactor

- formatting for pre-commit
- cleanup http basic auth reference in DatabaseAccess

## 0.2.0 (2024-02-09)

### Feat

- allow passing extra param to execQuery (for direct URL access) (#14)
- allow passing bytesio object as json/yaml config (#13)
- update queryRemote polling interval logic
- allow passing of BytesIO config to PostgresClient
- allow parsing of bytesio json/yaml config

### Fix

- Add execute() method
- Drop debug statement
- return bytesio data if not geojson and zipped
- only clip_to_aoi for Polygons, retail other geoms
- New version of the PostgresClient to use asyncpg iinstead of psycopg2
- improve handling for queryExec + reduce poll to 2s
- update underpass default url
- incorrect handling of dbshell.close() if not exists
- allow parsing of bytesio json/yaml config
- json parsing if index out of range
- Add destructor to close postgres connection, handle list of tag values insted of just "not null"
- Make less verbose
- reverse logic when testing for a closed connection

### Refactor

- add error log if max polling duration reached

## 0.1.7 (2023-12-05)

### Fix

- Add method to create tables in the database

## 0.1.6 (2023-11-18)

### Fix

- Use style that preserves refs for ways
- Add link to overture doc
- Add lua file that preserves refs
- Add method for creating a table in a database

## 0.1.5 (2023-11-10)

### Fix

- Add .scalar_subquery to get rid of the warning message
- Add the two new utilities
- Add more details on the data files
- Add support for importing multipolygons
- Depending on the version of dependant libraries, we need to set the SRID as it's not always set
- Don't try to process data if the list is empty
- Wrap reading parquet file with try/except since sometimes pyarrow core dumps
- Remove commented out code blocks, don't add OSM or MS buildings when importing Overture data as it's already out of date
- Oope, reenable mutli-threading
- Use new Overture class, which handles all the schema variations for Overture V2 data formatted files
- Add more content on Overture data files
- Support parsing all the different Overture data files

## 0.1.4 (2023-10-23)

### Fix

- Parser for Overture data files V2
- Add importer script
- Fix spelling of parquet
- Remove extraneous timer.stop()
- Make importing parquet files from Overture multi-threaded
- Add timer for import GeoJson
- Import MS Footprints into underpass schema
- Import uriParse from rawdata instead of the local copy
- If no config file is used, return the raw results
- Add content on importing Overture data into a database
- Add simple pages for all the utilities, add doc on the Overture data files

### Refactor

- rename LICENSE.md --> LICENSE
- update version in Makefile & track

## 0.1.3 (2023-10-09)

### Fix

- add required psycopg2 dep prior to version bump

## 0.1.2 (2023-10-09)

### Fix

- config.py handle yaml with join\_ and without
- checking for 'not null' in where items
- Add missing double quote
- Fix help line about program
- Fix pedantic error
- Oops, delete apidocs, since they are auto generated
- Update docs
- Use the same version of sqlalchemy for all other dependencies
- make id column autoincrement, there is no OSM ID as we ignore the out of date OSM data, and the other data has a record field, which is put in tags
- Add SRID to geometry
- Add more dependencies
- clip to boundary
- Create the database and tables from scratch, modify importParquet to handle the changes
- Parse the array for source to get the data source and ID
- Use AGPLv3, not GPLv3
- Add building=yes to we can query them
- Ikport parquer files into postgres using the Underpass schema
- Import parquet file into postgres using the underpass schema
- Use the new db_models for the database
- Add sqlalchemy model for our raw database schema
- Rename models.py to db_models.py
- Sigh... use sqlalchemy to create the Underpass schema for external datasets
- Break big SQL dumop into tables
- Add SQL schema for external data files
- Add new program to import files from geofabrik into postgres
- Remove more trailing spaces
- Remove trailing spaces
- Move file to directory so it gets installed
- Add the custom Underpass database schema

### Refactor

- remove refs to sqlmodel (using sqlalchemy)
- minor typos, renaming, docstrings
- split parseYaml into separate methods for clarity

## 0.1.2rc0 (2023-09-11)

### Fix

- UNDERPASS_API --> UNDERPASS_API_URL

## 0.1.1 (2023-09-11)

### Fix

- add output file for testing
- Improve handling of 'not null' in the JSON format
- Fix pattern in test case for SQL
- store the uri so other code can get the components
- Improve test case to handle SQL and JSON outout
- Add AOI for testing, add test case for SQL and JOSN output
- minor cleanup, **init** shouldn't return anything
- move out of subdirectory so it gets installed by pip
- Rename test case to be more accurate
- Generating JSON for Underpass works
- now generates the filters for the JSON output
- Works with Underpass now with attributes, adding filters next
- Modify test case to wotj with recent changes to the data structure
- Improved JSON parser, producews queries that work with a local postgres
- Add simple target to lint code
- Improve parsing of JSON files for rwa-data-api backend
- add comment to keep pylint happy
- Add the op to each item when parsing JSON
- Parsing the enhanced YAML format, and generating working SQL queries
- Improve debug messages
- Add support for Doxygen and pyreverse
- Improve YAML parsing for enhanced schema
- Read custom SQL from a file and execute it
- Add blank line to be consistent
- Improve JSON parsing with new test files, update test case
- Remoce extraneous spaces in the values list
- Improved parsing of JSON file with multiple levels and geometries
- more support for parsing the new json test data files
- Fix getting the path from the right project
- Add pyaml
- DOn't list \*~ for git status
- Don't use renamed module to find the root path for files
- Rename test case
- Fix bogus import
- Add useless minimal testcase to keep github workflows happy
- Fix print statement
- Add JSON queries for Underpass,
  pulled out of the raw-data-api backend for Export Tool
- Add mkdocstrings-python as a dependency
- Add mkdoc strings to the classes and methods
- Add a minimal set of pages to handle API docs using mkdocs
- Add config file for mkdocs
- Now produces an SQL query for a local data from either config source,
  or the remote raw database
- more doc updates and drop apt update from yml
- Try to get docs to publich to the wiki
- Hardcode the org name
- Update the github wiki for doc changes
- Add page on JSON format
- Add sidebar for wiki
- Add basic files for all projects
- Add doc on the YAML file format, and a home page for the wiki
- Add GPL license
- Intial config file so this installs
- Add code that actually does something
- Add some initial config files
- Add some content
