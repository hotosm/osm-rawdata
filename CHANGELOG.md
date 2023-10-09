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
