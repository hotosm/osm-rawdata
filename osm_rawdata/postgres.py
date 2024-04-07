#!/usr/bin/python3

# Copyright (c) 2022, 2023, 2024 Humanitarian OpenStreetMap Team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Humanitarian OpenStreetmap Team
# 1100 13th Street NW Suite 800 Washington, D.C. 20005
# <info@hotosm.org>

import argparse
import json
import logging
import os
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path
from sys import argv
from typing import Optional, Union

import geojson
import psycopg2
import requests
from geojson import Feature, FeatureCollection
from geojson import Polygon as GeojsonPolygon
from shapely import to_geojson, wkt
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

# Find the other files for this project
import osm_rawdata as rw
from osm_rawdata.config import QueryConfig

rootdir = rw.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


def uriParser(source):
    """Parse a URI into it's components.

    Args:
        source (str): The URI string for the database connection

    Returns:
        dict: The URI split into components

    """
    dbhost = None
    dbname = None
    dbuser = None
    dbpass = None
    dbport = None

    # if dbhost is 'localhost' then this tries to
    # connect to that hostname's tcp/ip port. If dbhost
    # is None, the datbase connection is done locally
    # through the named pipe.
    colon = source.find(":")
    rcolon = source.rfind(":")
    atsign = source.find("@")
    slash = source.find("/")
    # If nothing but a string, then it's a local postgres database
    # that doesn't require a user or password to login.
    if colon < 0 and atsign < 0 and slash < 0:
        dbname = source
    # Get the database name, which is always after the slash
    if slash > 0:
        dbname = source[slash + 1 :]
    # The user field is either between the beginning of the string,
    # and either a colon or atsign as the end.
    if colon > 0:
        dbuser = source[:colon]
    if colon < 0 and atsign > 0:
        dbuser = source[:atsign]
    # The password field is between a colon and the atsign
    if colon > 0 and atsign > 0:
        dbpass = source[colon + 1 : atsign]
    # The hostname for the database is after an atsign, and ends
    # either with the end of the string or a slash.
    if atsign > 0:
        if rcolon > 0 and rcolon > atsign:
            dbhost = source[atsign + 1 : rcolon]
        elif slash > 0:
            dbhost = source[atsign + 1 : slash]
        else:
            dbhost = source[atsign + 1 :]
    # rcolon is only above zero if there is a port number
    if rcolon > 0 and rcolon > atsign:
        if slash > 0:
            dbport = source[rcolon + 1 : slash]
        else:
            dbport = source[rcolon + 1 :]
            # import epdb; epdb.st()
    if colon > 0 and atsign < 0 and slash > 0:
        dbpass = source[colon + 1 : slash]

    if not dbhost:
        dbhost = "localhost"

        # print(f"{source}\n\tcolon={colon} rcolon={rcolon} atsign={atsign} slash={slash}")
    return {"dbname": dbname, "dbhost": dbhost, "dbuser": dbuser, "dbpass": dbpass, "dbport": dbport}


class DatabaseAccess(object):
    def __init__(
        self,
        dburi: str,
    ):
        """This is a class to setup a database connection.

        Args:
            dburi (str): The URI string for the database connection
        """
        self.dbshell = None
        self.dbcursor = None
        self.uri = uriParser(dburi)
        if self.uri["dbname"] == "underpass":
            # Use a persistant connect, better for multiple requests
            self.session = requests.Session()
            self.url = os.getenv("UNDERPASS_API_URL", "https://api-prod.raw-data.hotosm.org/v1")
            self.headers = {"accept": "application/json", "Content-Type": "application/json"}
        else:
            log.info(f"Opening database connection to: {self.uri['dbname']}")
            connect = "PG: dbname=" + self.uri["dbname"]
            if "dbname" in self.uri and self.uri["dbname"] is not None:
                connect = f"dbname={self.uri['dbname']}"
            elif "dbhost" in self.uri and self.uri["dbhost"] == "localhost" and self.uri["dbhost"] is not None:
                connect = f"host={self.uri['dbhost']} dbname={self.uri['dbname']}"
            if "dbuser" in self.uri and self.uri["dbuser"] is not None:
                connect += f" user={self.uri['dbuser']}"
            if "dbpass" in self.uri and self.uri["dbpass"] is not None:
                connect += f" password={self.uri['dbpass']}"
            # log.debug(f"Connecting with: {connect}")
            try:
                self.dbshell = psycopg2.connect(connect)
                self.dbshell.autocommit = True
                self.dbcursor = self.dbshell.cursor()
                if self.dbcursor.closed != 0:
                    log.error(f"Couldn't open cursor in {self.uri['dbname']}")
            except Exception as e:
                log.error(f"Couldn't connect to database: {e}")

    def __del__(self):
        """Close any open connections to Postgres."""
        if self.dbshell:
            self.dbshell.close()

    def createJson(
        self,
        config: QueryConfig,
        boundary: GeojsonPolygon,
        allgeom: bool = False,
        extra_params: dict = {},
    ) -> str:
        """Generate a JSON file used for remote access to raw-data-api.

        Uses the Underpass schema.

        Args:
            config (QueryConfig): The config data from the query config file
            boundary (GeojsonPolygon): The boundary polygon
            allgeom (bool): Whether to return centroids or all the full geometry
                TODO this is not implemented.
            extra_params (dict): Extra parameters to include in JSON config root.
                These params override existing values if set.

        Returns:
            str: The stringified JSON data.
        """
        json_data = {
            "geometry": boundary,
            "geometryType": self._get_geometry_types(config),
            "filters": self._get_filters(config),
            "centroid": config.config.get("centroid", False),
            "attributes": self._get_attributes(config),
            **extra_params,
        }

        return json.dumps(json_data)

    def _get_geometry_types(self, config: QueryConfig) -> Union[list, None]:
        """Get the geometry types based on the QueryConfig.

        Args:
            config (QueryConfig): The query configuration.

        Returns:
            Union[list, None]: A list of geometry types or None if empty.
        """
        geometry_types = []
        for table, geometry_type in {"nodes": "point", "ways_line": "line", "ways_poly": "polygon"}.items():
            if config.config.get("select", {}).get(table) or config.config.get("where", {}).get(table):
                geometry_types.append(geometry_type)
        return geometry_types or None

    def _get_filters(self, config: QueryConfig) -> dict:
        """Get the filters based on the QueryConfig.

        Args:
            config (QueryConfig): The query configuration.

        Returns:
            dict: The filters.
        """
        # Initialize the filters dictionary
        filters = {
            "tags": {},
        }

        # FIXME handle all_geometry key
        # FIXME requires updates to parseJson logic
        # # Check if all geometry types are present
        # all_geometry_types = all(geom_type in self._get_geometry_types(config) for geom_type in ['point', 'line', 'polygon'])

        # if all_geometry_types:
        #     # All geometries
        #     all_geometry_filters = {"join_or": {}}
        #     # Extract filters from config["where"]
        #     for table, conditions in config.config["where"].items():
        #         for condition in conditions:
        #             key, _ = list(condition.items())[0]  # Extract the filter key
        #             all_geometry_filters["join_or"][key] = []
        #     filters["tags"]["all_geometry"] = all_geometry_filters
        # else:

        # Specific geometry types
        filters["tags"]["point"] = {"join_or": {}, "join_and": {}}
        filters["tags"]["line"] = {"join_or": {}, "join_and": {}}
        filters["tags"]["polygon"] = {"join_or": {}, "join_and": {}}

        # Mapping between database table names and geometry types
        tables = {"nodes": "point", "ways_poly": "polygon", "ways_line": "line"}

        # Iterate through the conditions in the 'where' clause of the query configuration
        for table, conditions in config.config["where"].items():
            for condition in conditions:
                # Access the 'op' field in the condition
                key, option = list(condition.items())[0]
                if option == "or" or option == "and":
                    # If the option is 'or' or 'and', add the condition to the respective join dictionary
                    filters["tags"][tables[table]][f"join_{option}"][key] = []
                elif "not null" in option:
                    # If the condition indicates 'not null', add it to both join_or and join_and with empty values
                    filters["tags"][tables[table]]["join_or"][key] = []
                    filters["tags"][tables[table]]["join_and"][key] = []
                else:
                    # Otherwise, set the condition value in both join_or and join_and dictionaries
                    filters["tags"][tables[table]]["join_or"][key] = option
                    filters["tags"][tables[table]]["join_and"][key] = option

        return filters

    def _get_attributes(self, config: QueryConfig) -> list:
        """Get the attributes based on the QueryConfig.

        Args:
            config (QueryConfig): The query configuration.

        Returns:
            list: The list of attributes.
        """
        attributes = []
        for table, data in config.config["select"].items():
            for value in data:
                [[k, v]] = value.items()
                if k not in attributes:
                    attributes.append(k)
        return attributes

    def createSQL(
        self,
        config: QueryConfig,
        allgeom: bool = True,
    ):
        """This class generates the SQL to query a local postgres database.

        Args:
            config (QueryConfig): The config data from the query config file
            allgeom (bool): Whether to return centroids or all the full geometry

        Returns:
            (FeatureCollection): the json
        """
        sql = list()
        query = ""
        for table in config.config["tables"]:
            select = "SELECT "
            if allgeom:
                select += "ST_AsText(geom)"
            else:
                select += "ST_AsText(ST_Centroid(geom))"
            select += ", osm_id, version, "
            for entry in config.config["select"][table]:
                for k1, v1 in entry.items():
                    select += f"tags->>'{k1}', "
            select = select[:-2]

            join_or = list()
            join_and = list()
            for entry in config.config["where"][table]:
                # print(entry)
                if "op" not in entry:
                    pass
                op = entry["op"]
                for k, v in entry.items():
                    if k == "op":
                        continue
                    if op == "or":
                        # print(f"1: {k}=\'{v}\' OR ")
                        join_or.append(entry)
                    elif op == "and":
                        # print(f"2: {k}=\'{v}\' AND ")
                        join_and.append(entry)
            # jor = '('
            jor = ""
            for entry in join_or:
                for k, v in entry.items():
                    # Check if v is a non-empty list
                    if isinstance(v, list) and v:
                        if isinstance(v[0], list):
                            # It's an array of values
                            value = str(v[0])
                            any = f"ANY(ARRAY{value})"
                            jor += f"tags->>'{k}'={any} OR "
                            continue
                    if k == "op":
                        continue
                    if len(v) == 1:
                        if v[0] == "not null":
                            v1 = "IS NOT NULL"
                        else:
                            v1 = f"='{v[0]}'"
                    elif len(v) > 0:
                        v1 = f" IN {str(tuple(v))}"
                    else:
                        v1 = "IS NOT NULL"
                    jor += f"tags->>'{k}' {v1} OR "
            # print(f"JOR: {jor}")

            jand = ""
            for entry in join_and:
                for k, v in entry.items():
                    if k == "op":
                        continue
                    if len(v) == 1:
                        if v[0] == "not null":
                            v1 = "IS NOT NULL"
                        else:
                            v1 = f"='{v[0]}'"
                    elif len(v) > 0:
                        v1 = f" IN {str(tuple(v))}"
                    else:
                        v1 = "IS NOT NULL AND"
                    jand += f"tags->>'{k}' {v1} AND "
            # print(f"JAND: {jand}")
            query = f"{select} FROM {table} WHERE {jor} {jand}".rstrip()
            # if query[len(query)-5:] == ' OR  ':
            # print(query[:query.rfind(' ')])
            sql.append(query[: query.rfind(" ")])

        return sql

    def createTable(
        self,
        sql: str,
    ):
        """Create a table in the database

        Args:
            sqlfile (str): The SQL

        Returns:
            (bool): The table creation status
        """
        log.info("Creating table schema")
        result = self.dbcursor.execute(sql)

        # path = Path(sqlfile)
        # sql = f"INSERT INTO schemas(schema, version) VALUES('{sqlfile.stem}', 1.0)"
        # result = self.pg.dbcursor.execute(sql)

        return True

    def execute(
        self,
        sql: str,
    ):
        """Execute a raw SQL query and return the results.

        Args:
            sql (str): The SQL to execute

        Returns:
            (list): The results of the query
        """
        # print(sql)
        try:
            result = self.dbcursor.execute(sql)
            return self.dbcursor.fetchall()
        except:
            log.error(f"Couldn't execute query! {sql}")
            return list()

    def queryLocal(
        self,
        query: str,
        allgeom: bool = True,
        boundary: Polygon = None,
    ):
        """This query a local postgres database.

        Args:
            query (str): The SQL query to execute
            allgeom (bool): Whether to return centroids or all the full geometry
            boundary (Polygon): The boundary polygon

        Returns:
                query (FeatureCollection): the results of the query
        """
        features = list()
        # if no boundary, it's already been setup
        if boundary:
            sql = f"DROP VIEW IF EXISTS ways_view;CREATE VIEW ways_view AS SELECT * FROM ways_poly WHERE ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{boundary.wkt}'), geom)"
            self.dbcursor.execute(sql)
            sql = f"DROP VIEW IF EXISTS nodes_view;CREATE VIEW nodes_view AS SELECT * FROM nodes WHERE ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{boundary.wkt}'), geom)"
            self.dbcursor.execute(sql)
            sql = f"DROP VIEW IF EXISTS lines_view;CREATE VIEW lines_view AS SELECT * FROM ways_line WHERE ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{boundary.wkt}'), geom)"
            self.dbcursor.execute(sql)
            sql = f"DROP VIEW IF EXISTS relations_view;CREATE TEMP VIEW relations_view AS SELECT * FROM nodes WHERE ST_CONTAINS(ST_GeomFromEWKT('SRID=4326;{boundary.wkt}'), geom)"
            self.dbcursor.execute(sql)

            if query.find(" ways_poly ") > 0:
                query = query.replace("ways_poly", "ways_view")
            elif query.find(" ways_line ") > 0:
                query = query.replace("ways_line", "lines_view")
            elif query.find(" nodes ") > 0:
                query = query.replace("nodes", "nodes_view")
            elif query.find(" relations ") > 0:
                query = query.replace("relations", "relations_view")

        # log.debug(query)
        self.dbcursor.execute(query)
        try:
            result = self.dbcursor.fetchall()
            # log.debug("SQL Query returned %d records" % len(result))
        except:
            return FeatureCollection(features)

        # If there is no config file, don't modify the results
        if len(self.qc.config["where"]["ways_poly"]) == 0 and len(self.qc.config["where"]["nodes"]) == 0:
            return result

        for item in result:
            if len(item) <= 1 and len(result) == 1:
                return result
                # break
            geom = wkt.loads(item[0])
            tags = dict()
            tags["id"] = item[1]
            tags["version"] = item[2]
            i = 3
            # If there are no tables, we're using a custom SQL query
            if len(self.qc.config["tables"]) > 0:
                # map the value in the select to the values returns for them.
                for _table, values in self.qc.config["select"].items():
                    for entry in values:
                        if i == len(item):
                            break
                        [[k, v]] = entry.items()
                        if item[i] is not None:
                            tags[k] = item[i]
                        i += 1
            else:
                # Figure out the tags from the custom SELECT
                end = query.find("FROM")
                res = query[:end].split(" ")
                # This should be the geometry
                geom = wkt.loads(item[0])
                # This should be the OSM ID
                tags[res[2][:-1]] = item[1]
                # This should be the version
                tags[res[3][:-1]] = item[2]
            features.append(Feature(geometry=geom, properties=tags))
        return FeatureCollection(features)
        # return features

    def queryRemote(
        self,
        query: str,
    ) -> Optional[Union[str, dict, BytesIO]]:
        """This queries a remote postgres database using the FastAPI
        backend to the HOT Export Tool.

        Args:
            query (str): The JSON query to execute.

        Returns:
            (str, FeatureCollection, BytesIO): either the data URL if bind_zip=False,
                extracted geojson, else BytesIO file. Returns None on failure.
        """
        # Send the request to raw data api
        result = None

        url = f"{self.url}/snapshot/"
        try:
            log.debug(f"Raw Data API snapshot JSON config: {query}")
            result = self.session.post(url, data=query, headers=self.headers)
            result.raise_for_status()
        except requests.exceptions.HTTPError:
            if result is not None:
                error_dict = result.json()
                error_dict["status_code"] = result.status_code
                log.error(f"Failed to get extract from Raw Data API: {error_dict}")
                return None
            else:
                log.error("Failed to make request to raw data API")

        if result is None:
            log.error("Raw Data API did not return a response. Skipping.")
            return None

        if result.status_code != 200:
            error_message = result.json().get("detail")[0].get("msg")
            log.error(f"{error_message}")
            return None

        task_id = result.json().get("task_id")
        task_query_url = f"{self.url}/tasks/status/{task_id}"
        log.debug(f"Raw Data API Query URL: {task_query_url}")

        polling_interval = 2  # Initial polling interval in seconds
        max_polling_duration = 600  # Maximum duration for polling in seconds (10 minutes)
        elapsed_time = 0

        while elapsed_time < max_polling_duration:
            response = self.session.get(task_query_url, headers=self.headers)
            response_json = response.json()
            response_status = response_json.get("status")
            task_info = response_json.get("result", {})

            log.debug(f"Current status: {response_status}")

            # response_status options: STARTED, PENDING, SUCCESS
            if response_status != "SUCCESS" or not isinstance(task_info, dict) or not task_info.get("download_url"):
                # Adjust polling frequency after the first minute
                if elapsed_time > 60:
                    polling_interval = 10  # Poll every 10 seconds after the first minute

                # Wait before polling again
                log.debug(f"Waiting {polling_interval} seconds before polling API again...")
                time.sleep(polling_interval)
                elapsed_time += polling_interval

            else:
                # response_status="SUCCESS" and download_url present
                break

        else:
            # Maximum polling duration reached
            log.error(f"{max_polling_duration} second elapsed. Aborting data extract.")
            return None

        log.debug(f"Raw Data API Response: {task_info}")
        data_url = task_info.get("download_url")

        if not data_url:
            log.error("Raw data api no download_url returned. Skipping.")
            return None

        if not data_url.endswith(".zip"):
            return data_url

        # Extract filename is set, else use Export.geojson
        query_dict = json.loads(query)
        file_type = query_dict.get("outputType", "geojson")
        filename = f"{query_dict.get('fileName', 'Export')}.{file_type}"
        # Get zip file and extract
        with self.session.get(data_url, headers=self.headers) as response:
            buffer = BytesIO(response.content)
            with zipfile.ZipFile(buffer, "r") as zipped_file:
                with zipped_file.open(filename) as extracted_data:
                    if file_type == "geojson":
                        return json.load(extracted_data)
                    else:
                        return BytesIO(extracted_data.read())


class PostgresClient(DatabaseAccess):
    """Class to handle SQL queries for the categories."""

    def __init__(
        self,
        uri: str,
        config: Optional[Union[str, BytesIO]] = None,
        auth_token: Optional[str] = None,
        # output: str = None
    ):
        """This is a client for a postgres database.

        Args:
            uri (str): The URI string for the database connection.
            config (str, BytesIO): The query config file path or BytesIO object.
                Currently only YAML format is accepted if BytesIO is passed.

        Returns:
            (bool): Whether the data base connection was sucessful
        """
        super().__init__(uri)
        self.qc = QueryConfig()

        # Optional authentication
        if auth_token:
            self.headers["access-token"] = auth_token

        if config:
            # filespec string passed
            if isinstance(config, str):
                path = Path(config)
                if not path.exists():
                    raise FileNotFoundError(f"Config file does not exist {config}")
                with open(config, "rb") as config_file:
                    config_data = BytesIO(config_file.read())
                if path.suffix == ".json":
                    config_type = "json"
                elif path.suffix == ".yaml":
                    config_type = "yaml"
                else:
                    log.error(f"Unsupported file format: {config}")
                    raise ValueError(f"Invalid config {config}")

            # BytesIO object passed
            elif isinstance(config, BytesIO):
                config.seek(0)  # Reset the file pointer to the beginning
                config_data = config
                try:
                    # Is JSON
                    json.load(config_data)
                    log.debug("Parsed config is JSON format")
                    config_type = "json"
                except json.JSONDecodeError as e:
                    log.error(e)
                    # Is YAML
                    log.debug("Parsed config is YAML format")
                    config_type = "yaml"

            else:
                log.warning(f"Config input is invalid for PostgresClient: {config}")
                raise ValueError(f"Invalid config {config}")

            # Parse the config
            if config_type == "json":
                self.qc.parseJson(config_data)
            elif config_type == "yaml":
                self.qc.parseYaml(config_data)

    def createDB(self, dburi: uriParser):
        """Setup the postgres database connection.

        Args:
            dburi (str): The URI string for the database connection

        Returns:
            status (bool): Whether the data base connection was sucessful
        """
        sql = f"CREATE DATABASE IF NOT EXISTS {self.dbname}"
        self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()
        log.info("Query returned %d records" % len(result))
        # result = subprocess.call("createdb", uri.dbname)

        # Add the extensions needed
        sql = "CREATE EXTENSION postgis; CREATE EXTENSION hstore;"
        self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()
        log.info("Query returned %d records" % len(result))
        return True

    def execQuery(
        self,
        boundary: Union[FeatureCollection, Feature, dict, str],
        customsql: str = None,
        allgeom: bool = True,
        extra_params: dict = {},
    ):
        """This class generates executes the query using a local postgres
        database, or a remote one that uses the Underpass schema.

        Args:
            boundary (FeatureCollection, Feature, dict, str): The boundary polygon.
            customsql (str): Don't create the SQL, use the one supplied.
            allgeom (bool): Whether to return centroids or all the full geometry.

        Returns:
                query (FeatureCollection): the json
        """
        log.info("Parsing AOI geojson for data extract")

        # Parse JSON string type
        if isinstance(boundary, str):
            boundary = json.loads(boundary)

        if (geom_type := boundary.get("type")) == "FeatureCollection":
            # Convert each feature into a Shapely geometry
            geometries = [shape(feature.get("geometry")) for feature in boundary.get("features", [])]
            merged_geom = unary_union(geometries)
        elif geom_type == "Feature":
            merged_geom = shape(boundary.get("geometry"))
        else:
            merged_geom = shape(boundary)

        # Convert the merged geoms to a single Polygon GeoJSON using convex hull
        aoi_polygon = json.loads(to_geojson(merged_geom.convex_hull))
        aoi_shape = shape(aoi_polygon)

        if self.dbshell:
            log.info("Extracting features from Postgres...")
            if not customsql:
                sql = self.createSQL(self.qc, allgeom)
            else:
                sql = [customsql]
            alldata = list()
            for query in sql:
                # print(query)
                result = self.queryLocal(query, allgeom, aoi_shape)
                if len(result) > 0:
                    alldata += result["features"]
            collection = FeatureCollection(alldata)
        else:
            log.info("Extracting features via remote call...")
            json_config = self.createJson(self.qc, aoi_polygon, allgeom, extra_params)
            collection = self.queryRemote(json_config)
            # bind_zip=False, data is not zipped, return URL directly
            if not json.loads(json_config).get("bind_zip", True):
                return collection

        if not collection:
            log.warning("No data returned for data extract")

        return collection


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(
        prog="postgres",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Make data extract from OSM",
        epilog="""
This program extracts data from a local postgres data, or the remote Underpass
one. A boundary polygon is used to define the are to be covered in the extract.
Optionally a data file can be used.

        """,
    )
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-u", "--uri", default="underpass", help="Database URI")
    parser.add_argument("-b", "--boundary", required=True, help="Boundary polygon to limit the data size")
    parser.add_argument("-s", "--sql", help="Custom SQL query to execute against the database")
    parser.add_argument("-a", "--all", help="All the geometry or just centroids")
    parser.add_argument("-c", "--config", help="The config file for the query (json or yaml)")
    parser.add_argument("-o", "--outfile", default="extract.geojson", help="The output file")
    args = parser.parse_args()

    if len(argv) <= 1 or (args.sql is None and args.config is None):
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    infile = open(args.boundary, "r")
    poly = geojson.load(infile)
    if args.uri is not None:
        log.info("Using a Postgres database for the data source")
        if args.sql:
            pg = PostgresClient(args.uri)
            sql = open(args.sql, "r")
            result = pg.execQuery(poly, sql.read())
            log.info(f"Custom Query returned {len(result['features'])} records")
        else:
            pg = PostgresClient(args.uri, args.config)
            result = pg.execQuery(poly)
            log.info(f"Canned Query returned {len(result['features'])} records")

        outfile = open(args.outfile, "w")
        geojson.dump(result, outfile)

        log.debug(f"Wrote {args.outfile}")


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
