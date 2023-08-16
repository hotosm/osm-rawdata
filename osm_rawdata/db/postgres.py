#!/usr/bin/python3

# Copyright (c) 2022 Humanitarian OpenStreetMap Team
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
import os
import logging
import sys
import re
import yaml
import json
from sys import argv
from geojson import Point, Feature, FeatureCollection, dump, Polygon
import geojson
import requests
import time
import psycopg2
from shapely.geometry import shape, Polygon
import shapely
import subprocess
from pathlib import Path
from hot_exports.config import QueryConfig
from shapely import wkt
from io import BytesIO
import zipfile


# Find the other files for this project
import hot_exports as he
rootdir = he.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

def uriParser(source):
    """Parse a URI into it's components"""
    dbhost = None
    dbname = None
    dbuser = None
    dbpass = None
    dbport = None

    # if dbhost is 'localhost' then this tries to
    # connect to that hostname's tcp/ip port. If dbhost
    # is None, the datbase connection is done locally
    # through the named pipe.
    colon = source.find(':')
    rcolon = source.rfind(':')
    atsign = source.find('@')
    slash = source.find('/')
    # If nothing but a string, then it's a local postgres database
    # that doesn't require a user or password to login.
    if colon < 0 and atsign < 0 and slash < 0:
        dbname = source
    # Get the database name, which is always after the slash
    if slash > 0:
        dbname = source[slash+1:]
    # The user field is either between the beginning of the string,
    # and either a colon or atsign as the end.
    if colon > 0:
        dbuser = source[:colon]
    if colon < 0 and atsign > 0:
        dbuser = source[:atsign]
    # The password field is between a colon and the atsign
    if colon > 0 and atsign > 0:
        dbpass = source[colon+1:atsign]
    # The hostname for the database is after an atsign, and ends
    # either with the end of the string or a slash.
    if atsign > 0:
        if rcolon > 0 and rcolon > atsign:
            dbhost = source[atsign+1:rcolon]
        elif slash > 0:
            dbhost = source[atsign+1:slash]
        else:
            dbhost = source[atsign+1:]
    # rcolon is only above zero if there is a port number
    if rcolon > 0 and rcolon > atsign:
        if slash > 0:
            dbport = source[rcolon+1:slash]
        else:
            dbport = source[rcolon+1:]
            # import epdb; epdb.st()
    if colon > 0 and atsign < 0 and slash > 0:
        dbpass = source[colon+1:slash]

    if not dbhost:
        dbhost = 'localhost'

        # print(f"{source}\n\tcolon={colon} rcolon={rcolon} atsign={atsign} slash={slash}")
    db = {'dbname': dbname, 'dbhost': dbhost, 'dbuser': dbuser, 'dbpass': dbpass, 'dbport': dbport}

    return db

class DatabaseAccess(object):
    def __init__(self,
                 dburi: str,
                 ):
        self.dbshell = None
        self.dbcursor = None
        uri = uriParser(dburi)
        if uri['dbname'] == "underpass":
            # Authentication data
            # self.auth = HTTPBasicAuth(self.user, self.passwd)

            # Use a persistant connect, better for multiple requests
            self.session = requests.Session()
            self.url = "https://raw-data-api0.hotosm.org/v1"
            self.headers = {"accept": "application/json", "Content-Type": "application/json"}
        else:
            log.info("Opening database connection to: %s" % uri['dbhost'])
            connect = "PG: dbname=" + uri['dbname']
            if 'dbname' in uri and uri['dbname'] is not None:
                connect = f"dbname={uri['dbname']}"
            elif 'dbhost'in uri and uri['dbhost'] == "localhost" and uri['dbhost'] is not None:
                connect = f"host={uri['dbhost']} dbname={uri['dbname']}"
            if 'dbuser' in uri and uri['dbuser'] is not None:
                connect += f" user={uri['dbuser']}"
            if 'dbpass' in uri and uri['dbpass'] is not None:
                connect += f" password={uri['dbpass']}"
            log.debug(f"Connecting with: {connect}")
            try:
                self.dbshell = psycopg2.connect(connect)
                self.dbshell.autocommit = True
                self.dbcursor = self.dbshell.cursor()
                if self.dbcursor.closed == 0:
                    log.info(f"Opened cursor in {uri['dbname']}")
            except Exception as e:
                log.error(f"Couldn't connect to database: {e}")

    def createJson(self,
                   config: QueryConfig,
                   boundary: Polygon,
                   allgeom: bool = False
                   ):
        # path = xlsforms_path.replace("xlsforms", "data_models")
        # file = open(f"{path}/{category}.yaml", "r").read()
        # data = yaml.load(file, Loader=yaml.Loader)

        feature = dict()
        feature["geometry"] = boundary

        filters = dict()
        filters["tags"] = dict()
        filters["tags"]["all_geometry"] = dict()
        geometryType = list()
        for table in config.config['tables']:
            if table == 'nodes':
                geometryType.append('point')
            if table == 'way_line':
                geometryType.append('line')
            if table == 'way_poly':
                geometryType.append('polygon')
        # feature.update({"geometryType": geometryType})

        # The database tables to query
        # if tags exists, then only query those fields
        select = ""
        for entry in config.config['where']:
            for k, v in entry.items():
                valitem = list()
                if v == 'not null':
                    valitem = [v]
                select += f"\"{k}\": [],"
                if k == 'op':
                    continue
                if entry['op'] == 'or':
                    if 'join_or' not in filters["tags"]["all_geometry"]:
                        filters["tags"]["all_geometry"]["join_or"] = dict()
                    filters["tags"]["all_geometry"]["join_or"].update({k: valitem})
                elif entry['op'] == 'and':
                    if 'join_and' not in filters["tags"]["all_geometry"]:
                        filters["tags"]["all_geometry"]["join_and"] = dict()
                    filters["tags"]["all_geometry"]["join_and"].update({k: valitem})
        feature.update({"filters": filters})
        # FIXME: obviously for debugging
        # print(feature['filters'])
        xxx =  open('xxx.json', 'w')
        json.dump(feature, xxx, indent=2)
        return json.dumps(feature)
        # return feature

    def createSQL(self,
                  config: QueryConfig,
                  allgeom: bool = True,
                  ):
        sql = list()
        select = "SELECT "
        if allgeom:
            select += "ST_AsText(geom)"
        else:
            select += "ST_AsText(ST_Centroid(geom))"
        select += ", osm_id, version, "
        for entry in config.config['select']:
            for k, v in entry.items():
                    # print(f"{k} = {v}")
                if len(v) == 0:
                    select += f"tags->>\'{k}\', "
                else:
                    select += f"tags->>\'{k}\' AS {v}, "
        select = select[:-2]

        where = "WHERE ("
        previous = ""
        for entry in config.config['where']:
            for k, v in entry.items():
                if previous != f"{entry['op'].upper()}" and len(previous) > 0:
                    where += ") "
                    previous = f"{entry['op'].upper()}"
                if v == 'not null' and k != 'op':
                    where += f" {previous} tags->>\'{k}' IS NOT NULL"
                elif k != 'op':
                    where += f" {previous} tags->>\'{k}\'=\'{v}\'"
                    # where = f"{where[:-]})"
                if previous != f"{entry['op'].upper()}":
                    previous = f"{entry['op'].upper()}"
                
        # The database tables to query
        for table in config.config['tables']:
            query = f"{select} FROM {table} {where}"
            sql.append(query)
        return sql

    def queryLocal(self,
                   query: str,
                   allgeom: bool = True,
                   boundary: Polygon = None,
                   ):
        """Query a local postgres database"""
        features = list()
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
        if query.find(" ways_line ") > 0:
            query = query.replace("ways_line", "lines_view")
        elif query.find(" nodes ") > 0:
            query = query.replace("nodes", "nodes_view")
        elif query.find(" relations ") > 0:
            query = query.replace("relations", "relations_view")
        features = list()
        log.debug(query)
        self.dbcursor.execute(query)
        result = self.dbcursor.fetchall()
        log.info("Query returned %d records" % len(result))
        for item in result:
            if len(item) <= 1:
                break
            geom = wkt.loads(item[0])
            tags = dict()
            tags["id"] = item[1]
            tags['version'] = item[2]
            i = 3
            # map the value in the select to the values returns for them.
            for entry in self.qc.config['select']:
                [[k, v]] = entry.items()
                if item[i] is not None:
                    tags[k] = item[i]
                i += 1

            features.append(Feature(geometry=geom, properties=tags))
        return features

    def queryRemote(self,
                    query: str = None
                    ):
        url = f"{self.url}/snapshot/"
        result = self.session.post(url, data=query, headers=self.headers)
        if result.status_code != 200:
            log.error(f"{result.json()['detail'][0]['msg']}")
            return None
        task_id = result.json()['task_id']
        newurl = f"{self.url}/tasks/status/{task_id}"
        while True:
            result = self.session.get(newurl, headers=self.headers)
            if result.json()['status'] == "PENDING":
                log.debug("Retrying...")
                time.sleep(1)
            elif result.json()['status'] == "SUCCESS":
                break
        zip = result.json()['result']['download_url']
        result = self.session.get(zip, headers=self.headers)
        fp = BytesIO(result.content)
        zfp = zipfile.ZipFile(fp, "r")
        zfp.extract("Export.geojson", "/tmp/")
        # Now take that taskid and hit /tasks/status url with get
        data = zfp.read("Export.geojson")
        os.remove("/tmp/Export.geojson")
        return json.loads(data)
    #   return zfp.read("Export.geojson")

class PostgresClient(DatabaseAccess):
    """Class to handle SQL queries for the categories"""
    def __init__(self,
                 uri: str,
                 config: str,
                 #output: str = None
    ):
        """Initialize the database handler"""
        super().__init__(uri)
        # Load the config file for the SQL query
        path = Path(config)
        self.qc = QueryConfig()
        if path.suffix == '.json':
            result = self.qc.parseJson(config)
        elif path.suffix == '.yaml':
            result = self.qc.parseYaml(config)
        else:
            log.error(f"{args.infile} is an unsupported file format!")
            quit()        

    def createDB(self,
                 dburi: uriParser
                 ):
        sql = f"CREATE DATABASE IF NOT EXISTS {self.dbname}"
        self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()
        log.info("Query returned %d records" % len(result))
        #result = subprocess.call("createdb", uri.dbname)

        # Add the extensions needed
        sql = f"CREATE EXTENSION postgis; CREATE EXTENSION hstore;"
        self.dbcursor.execute(sql)
        result = self.dbcursor.fetchall()
        log.info("Query returned %d records" % len(result))

    def execQuery(self,
                    boundary: FeatureCollection,
                    customsql: str = None,
                    allgeom: bool = True,
                    ):
        """Extract buildings from Postgres"""
        log.info("Extracting features from Postgres...")

        if 'features' in boundary:
            # FIXME: ideally this shyould support multipolygons
            poly = boundary['features'][0]['geometry']
        else:
            poly = boundary["geometry"]
        wkt = shape(poly)

        config = 'buildings'    # FIXME
        if self.dbshell:
            if not customsql:
                sql = self.createSQL(self.qc, allgeom)
            alldata = list()
            for query in sql:
                result = self.queryLocal(query, allgeom, wkt)
                if len(result) > 0:
                    alldata.append(result)
            collection = FeatureCollection(alldata)
        else:
            request = self.createJson(self.qc, poly, allgeom)
            collection = self.queryRemote(request)
        return collection

# FIXME: it would be nice if this class would work
class FileClient(object):
    """Class to handle Overpass queries"""

    def __init__(self,
                 infile: str,
                 output: str
                 ):
        """Initialize Overpass handler"""
        OutputFile.__init__(self, output)
        self.infile = infile

    def getFeatures(self,
                    boundary,
                    infile: str,
                    outfile: str
                    ):
        """Extract buildings from a disk file"""
        log.info("Extracting buildings from %s..." % infile)
        if boundary:
            poly = ogr.Open(boundary)
            layer = poly.GetLayer()
            ogr.Layer.Clip(osm, layer, memlayer)
        else:
            layer = poly.GetLayer()

        tmp = ogr.Open(infile)
        layer = tmp.GetLayer()

        layer.SetAttributeFilter("tags->>'building' IS NOT NULL")


def main():
    
    parser = argparse.ArgumentParser(
        prog="postgres",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Make data extract from OSM",
        epilog="""
This program extracts data from a local postgres data, or the remote Underpass
one. A boundary polygon is used to define the are to be covered in the extract.
Optionally a data file can be used.

        """
    )
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-u", "--uri", default="underpass", help="Database URI")
    parser.add_argument("-b", "--boundary", required=True, help="Boundary polygon to limit the data size")
    parser.add_argument("-s", "--sql", help="Custom SQL query to execute against the database")
    parser.add_argument("-a", "--all", help="All the geometry or just centroids")
    parser.add_argument("-c", "--config", required=True, help="The config file for the query (json or yaml)")
    args = parser.parse_args()

    if len(argv) <= 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose is not None:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(threadName)10s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        log.addHandler(ch)

    infile = open(args.boundary, 'r')
    poly = geojson.load(infile)
    if args.uri is not None:
        log.info("Using a Postgres database for the data source")
        pg = PostgresClient(args.uri, args.config)
        if args.sql:
            sql = open(args.sql, 'r')
            result = pg.execQuery(poly, sql.read())
            log.info("Query returned %d records" % len(result))
        else:
            result = pg.execQuery(poly)
            log.info("Query returned %d records" % len(result))

        # pg.cleanup(outfile)

if __name__ == "__main__":
    main()
