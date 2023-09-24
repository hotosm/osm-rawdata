#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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
import logging
import sys
import subprocess
import psycopg2
from sys import argv
import requests
import math
from osm_fieldwork.make_data_extract import uriParser
import pandas as pd
import pyarrow.parquet as pq
from shapely import wkb
from sqlalchemy import create_engine, MetaData
from sqlmodel import create_engine, Field, Session, SQLModel, select
from osm_rawdata.db_models import Nodes, Ways, Lines, Base
from osm_rawdata.db_schemas import WayBase
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.dialects.postgresql import insert, HSTORE, JSONB
from sqlalchemy import column, inspect, table, func, cast

# Find the other files for this project
import osm_rawdata as rw
rootdir = rw.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

class MapImporter(object):
    def __init__(self,
                 dburi: str,
                 ):
        """
        This is a class to setup a local database for OSM data.
        
        Args:
            dburi (str): The URI string for the database connection

        Returns:
            (OsmImporter): An instance of this class
        """
        self.dburi = dburi
        self.dbshell = None
        self.dbcursor = None
        if dburi:
            self.uri = uriParser(dburi)
            self.session = requests.Session()
            # create the database if it doesn't exist
            postgres = self.uri.copy()
            postgres['dbname'] = 'postgres'
            self.connect(postgres)
            try:
                self.dbcursor.execute(f"CREATE DATABASE {self.uri['dbname']}")
            except:
                log.warning(f"Database {self.uri['dbname']} already exists")

            # Now connect to the database we just created
            self.connect(self.uri)
            sql = "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS hstore;"
            self.dbcursor.execute(sql)

            # Create indexes to improve peformance
            # self.dbcursor.execute(f"CREATE TABLE ways_poly(); ")
            # self.dbcursor.execute("cluster ways_poly using ways_poly_geom_idx;")
            # self.dbcursor.execute("create index on ways_poly using gin(tags)")

            
    def connect(self,
                 dburi: dict,
                 ):
        """
        This is a class to setup a local database for OSM data.
        
        Args:
            dburi (dict): The URI string for the database connection

        Returns:
            (OsmImporter): An instance of this class
        """
        log.info("Opening database connection to: %s" % self.uri['dbhost'])
        connect = "PG: dbname=" + self.uri['dbname']
        if 'dbname' in self.uri and self.uri['dbname'] is not None:
            connect = f"dbname={self.uri['dbname']}"
        elif 'dbhost'in self.uri and self.uri['dbhost'] == "localhost" and self.uri['dbhost'] is not None:
            connect = f"host={self.uri['dbhost']} dbname={self.uri['dbname']}"
        if 'dbuser' in self.uri and self.uri['dbuser'] is not None:
            connect += f" user={self.uri['dbuser']}"
        if 'dbpass' in self.uri and self.uri['dbpass'] is not None:
            connect += f" password={self.uri['dbpass']}"
        log.debug(f"Connecting with: {connect}")
        try:
            self.dbshell = psycopg2.connect(connect)
            self.dbshell.autocommit = True
            self.dbcursor = self.dbshell.cursor()
            if self.dbcursor.closed == 0:
                log.info(f"Opened cursor in {self.uri['dbname']}")
        except Exception as e:
            log.error(f"Couldn't connect to database: {e}")

    def importOSM(self,
               infile: str,
               ):
        """
        Import an OSM data file into a postgres database.
        
        Args:
            infile (str): The file to import

        Returns:
            (bool): Whether the import finished sucessfully
         """
        # osm2pgsql --create -d nigeria --extra-attributes --output=flex --style raw.lua nigeria-latest-internal.osm.pbf
        result = subprocess.run(['osm2pgsql', '--create', '-d',
                                 f"{self.uri['dbname']}",
                                 '--extra-attributes',
                                 '--output=flex',
                                 '--style', f'{rootdir}/raw.lua',
                                 f'{infile}']
                                )
        result.check_returncode()

    def importParquet(self,
               infile: str,
               ):
        """
        Import an OSM data file into a postgres database.
        
        Args:
            infile (str): The file to import

        Returns:
            (bool): Whether the import finished sucessfully
         """
        engine = create_engine(f"postgresql://{self.dburi}", echo=True)
        if not database_exists(engine.url):
            create_database(engine.url)
        else:
            conn = engine.connect()
            
        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        meta = MetaData()
        meta.create_all(engine)

        try:
            ways = table(
                "ways_poly",
                column("osm_id"),
                column("user"),
                column("geom"),
                column("tags"),
            )
            pfile = pq.ParquetFile(infile)
            data = pfile.read()
            index = -1
            for i in range(0, len(data) - 1):
                entry = dict()
                entry['fixme'] = data[0][i].as_py()
                # entry['names']  = data[3][i].as_py()
                # entry['level']  = data[4][i].as_py()
                if data[5][i].as_py() is not None:
                    entry['height'] = int(data[5][i].as_py())
                else:
                    entry['height'] = 0                    
                if data[6][i].as_py() is not None:
                    entry['levels'] = int(data[6][i].as_py())
                else:
                    entry['levels'] = 0
                entry['source'] = data[8][i][0][0][1].as_py()
                try:
                    osm = data[8][i][0][2][1].as_py().split('@')
                    if len(osm) > 1:
                        entry['id'] = int(osm[0][1:])
                        entry['version'] = int(osm[1])
                    else:
                        entry['id'] = int(osm[0])
                except:
                    entry['id'] = 0
                entry['geometry'] = data[10][i].as_py()
                entry['building'] = 'yes'     
                geom = entry['geometry']
                type = wkb.loads(entry['geometry']).geom_type
                if type != 'Polygon':
                    log.warning("Got Multipolygon")
                    continue
                # FIXME: This is a hack, for some weird reason the
                # entry dict doesn't convert to jsonb, it just
                # becomes bytes
                tags = {'building': 'yes',
                        'source': entry['source'],
                        'levels': entry['levels'],
                        'height': entry['height']
                        }
                scalar = select(cast(tags, JSONB))
                sql = insert(ways).values(
                    osm_id = entry['id'],
                    geom = geom,
                    tags = scalar,
                )
                # index -= 1
                conn.execute(sql)
                conn.commit()
                print(f"FIXME2: {entry}")
        except Exception as e:
            log.error(e)

def main():
    """This main function lets this class be run standalone by a bash script"""
    parser = argparse.ArgumentParser(
        prog="config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Parse YAML or JSON SQL config file",
        epilog="""
        This should only be run standalone for debugging purposes.
        """
    )
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="Input data file")
    parser.add_argument("-u", "--uri", required=True, help="Database URI")
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

    mi = MapImporter(args.uri)
    #if mi.importOSM(args.infile):
    if mi.importParquet(args.infile):
        log.info(f'Imported {args.infile} into {args.uri}')

if __name__ == "__main__":
    """This is just a hook so this file can be run standalone during development."""
    main()
