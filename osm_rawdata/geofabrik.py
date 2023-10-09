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
import logging
import sys
from sys import argv

import yaml
from pySmartDL import SmartDL

# Find the other files for this project
import osm_rawdata as rw

rootdir = rw.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class GeoFabrik(object):
    def __init__(self):
        # find the path to the test data files
        filespec = f"{rootdir}/geofabrik.yaml"
        try:
            file = open(filespec, "rb").read()
        except:
            print(argv)
            log.error(f"Couldn't open {filespec}")
            quit()
        self.regions = yaml.load(file, Loader=yaml.Loader)

    def dump(self):
        for entry in self.regions:
            [[k, v]] = entry.items()
            print(f"Region: {k}")
            if type(v) == list:
                for i in v:
                    print(f"\t{i}")
            print("")

    def getRegion(self, region: str):
        for entry in self.regions:
            [[k, v]] = entry.items()
            if type(v) == list:
                for i in v:
                    if i == region:
                        return k
        return None


def main():
    # Command Line options
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-f", "--file", help="The country or US state to download")
    parser.add_argument("-l", "--list", action="store_true", help="List all files on GeoFabrik")
    args = parser.parse_args()

    if len(argv) <= 1:
        parser.print_help()
        quit()

    # if verbose, dump to the terminal.
    if args.verbose:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    geof = GeoFabrik()
    if args.list:
        geof.dump()
        quit()

    # Download a file from GeoFabrik
    if args.file:
        region = geof.getRegion(args.file)
        if not region:
            log.error(f"{args.file} not found on GeoFabrik! Use the -l option to list all the regions")
            quit()

        uri = f"http://download.geofabrik.de/{region.lower()}/{args.file.lower()}-latest.osm.pbf"
        outfile = f"./{args.file}-latest.osm.pbf"
        try:
            dl = SmartDL(uri, dest=outfile, connect_default_logger=False)
            dl.start()
        except:
            logging.error(f"Couldn't download from {outfile}: {dl.get_errors()}")


if __name__ == "__main__":
    main()
