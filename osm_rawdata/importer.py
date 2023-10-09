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
import subprocess
import sys
from sys import argv

import pyarrow.parquet as pq
from codetiming import Timer
from osm_fieldwork.make_data_extract import uriParser
from progress.spinner import PixelSpinner
from shapely import wkb
from sqlalchemy import MetaData, cast, column, create_engine, select, table, text
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

# Find the other files for this project
import osm_rawdata as rw
import osm_rawdata.db_models
from osm_rawdata.db_models import Base

rootdir = rw.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class MapImporter(object):
    def __init__(
        self,
        dburi: str,
    ):
        """This is a class to setup a local database for OSM data.

        Args:
            dburi (str): The URI string for the database connection

        Returns:
            (OsmImporter): An instance of this class
        """
        self.dburi = dburi
        self.db = None
        if dburi:
            self.uri = uriParser(dburi)
            engine = create_engine(f"postgresql://{self.dburi}", echo=True)
            if not database_exists(engine.url):
                create_database(engine.url)
            self.db = engine.connect()

            # Add the extension we need to process the data
            sql = text(
                "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS hstore;CREATE EXTENSION IF NOT EXISTS dblink;"
            )
            self.db.execute(sql)
            self.db.commit()

            Base.metadata.create_all(bind=engine)

            sessionmaker(autocommit=False, autoflush=False, bind=engine)

            # Create indexes to improve peformance
            # sql = text("cluster ways_poly using ways_poly_geom_idx;")
            # self.db.execute(sql)
            # sql("create index on ways_poly using gin(tags)")
            # self.db.execute(sql)
            # self.db.commit()

    def importOSM(
        self,
        infile: str,
    ):
        """Import an OSM data file into a postgres database.

        Args:
            infile (str): The file to import

        Returns:
            (bool): Whether the import finished sucessfully
        """
        # osm2pgsql --create -d nigeria --extra-attributes --output=flex --style raw.lua nigeria-latest-internal.osm.pbf
        result = subprocess.run(
            [
                "osm2pgsql",
                "--create",
                "-d",
                f"{self.uri['dbname']}",
                "--extra-attributes",
                "--output=flex",
                "--style",
                f"{rootdir}/raw.lua",
                f"{infile}",
            ]
        )
        result.check_returncode()

    def importParquet(
        self,
        infile: str,
    ):
        """Import an Overture parquet data file into a postgres database.

        Args:
            infile (str): The file to import

        Returns:
            (bool): Whether the import finished sucessfully
        """
        # engine = create_engine(f"postgresql://{self.dburi}")
        # engine = create_engine(f"postgresql://{self.dburi}", echo=True)
        # if not database_exists(engine.url):
        #     create_database(engine.url)
        # else:
        #     conn = engine.connect()

        # session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # meta = MetaData()
        # meta.create_all(engine)

        spin = PixelSpinner(f"Processing {infile}...")
        timer = Timer(text="importParquet() took {seconds:.0f}s")
        timer.start()
        try:
            ways = table(
                "ways_poly",
                column("id"),
                column("user"),
                column("geom"),
                column("tags"),
            )
            pfile = pq.ParquetFile(infile)
            data = pfile.read()
            index = -1
            for i in range(0, len(data) - 1):
                spin.next()
                entry = dict()
                entry["fixme"] = data[0][i].as_py()
                # entry['names']  = data[3][i].as_py()
                # entry['level']  = data[4][i].as_py()
                if data[5][i].as_py() is not None:
                    entry["height"] = int(data[5][i].as_py())
                else:
                    entry["height"] = 0
                if data[6][i].as_py() is not None:
                    entry["levels"] = int(data[6][i].as_py())
                else:
                    entry["levels"] = 0
                entry["source"] = data[8][i][0][0][1].as_py()
                if entry["source"] == "OpenStreetMap":
                    # log.warning("Ignoring OpenStreetMap entries as they are out of date")
                    # osm = data[8][i][0][2][1].as_py().split('@')
                    continue
                entry["id"] = index
                # LIDAR has no record ID
                try:
                    entry["record"] = data[8][i][0][2][1].as_py()
                except:
                    entry["record"] = 0
                entry["geometry"] = data[10][i].as_py()
                entry["building"] = "yes"
                geom = entry["geometry"]
                type = wkb.loads(entry["geometry"]).geom_type
                if type != "Polygon":
                    # log.warning("Got Multipolygon")
                    continue
                # FIXME: This is a hack, for some weird reason the
                # entry dict doesn't convert to jsonb, it just
                # becomes bytes
                tags = {
                    "building": "yes",
                    "source": entry["source"],
                    "levels": entry["levels"],
                    "record": entry["record"],
                    "height": entry["height"],
                }
                scalar = select(cast(tags, JSONB))
                sql = insert(ways).values(
                    # osm_id = entry['osm_id'],
                    geom=geom,
                    tags=scalar,
                )
                index -= 1
                self.db.execute(sql)
                self.db.commit()
                # print(f"FIXME2: {entry}")
        except Exception as e:
            log.error(e)
        timer.stop()

    def importGeoJson(
        self,
        infile: str,
    ):
        """Import a GeoJson data file into a postgres database.

        Args:
            infile (str): The file to import

        Returns:
            (bool): Whether the import finished sucessfully
        """
        engine = create_engine(f"postgresql://{self.dburi}", echo=True)
        if not database_exists(engine.url):
            create_database(engine.url)
        else:
            engine.connect()

        sessionmaker(autocommit=False, autoflush=False, bind=engine)

        meta = MetaData()
        meta.create_all(engine)


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(
        prog="config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Import data into a postgres database",
        epilog="""
        This should only be run standalone for debugging purposes.
        """,
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
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    mi = MapImporter(args.uri)
    # if mi.importOSM(args.infile):
    if mi.importParquet(args.infile):
        log.info(f"Imported {args.infile} into {args.uri}")


if __name__ == "__main__":
    """This is just a hook so this file can be run standalone during development."""
    main()
