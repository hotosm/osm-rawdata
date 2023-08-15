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
import subprocess
from pathlib import Path
from shapely.geometry import shape


# Find the other files for this project
import hot_exports as he
rootdir = he.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class QueryConfig(object):
    def __init__(self,
                 boundary: Polygon = None
                 ):
        self.config = {'select': list(),
                        'tables': list(),
                        'where': list(),
                        'keep': list()
                       }
        self.geometry = boundary
        # for polygon extracts, sometimes we just want the center point
        self.centroid = False

    def parseYaml(self,
                    filespec: str
                    ):
        file = open(filespec, 'r')
        path = Path(filespec)
        data = yaml.load(file, Loader=yaml.Loader)

        if data['select']:
            for entry in data['select']:
                if type(entry) == dict:
                    self.config['select'].append(entry)
                else:
                    self.config['select'].append({entry: list()})

        for entry in data['keep']:
            self.config['select'].append({entry: list()})

        op = None
        for tag in data['where']['tags']:
            [[k, v]] = tag.items()
            if k == 'join_or':
                op = 'or'
            elif k == 'join_and':
                op = 'and'
            for entry in v:
                for k1, v1 in entry.items():
                    if v1 == True:
                        v1 = 'yes'
                    newtag = {k1: v1}
                    newtag['op'] = op
                    self.config['where'].append(newtag)
            for k2, v2 in entry.items():
                newtag = {k2: dict()}
                newtag['op'] = op
                self.config['select'].append({k2: dict()})

        self.config['keep'] = data['keep']
        self.config['tables'] = data['from']
        
        # The table names are based on the Underpass schema, nodes, ways_poly,
        # ways_line, relations
        return self.config

    def parseJson(self,
                  filespec: str
                  ):
        """Parse the JSON format config file used by the raw-data-api
        and export tool."""
        file = open(filespec, 'r')
        data = json.load(file)
        # Get the geometry
        self.geometry = shape(data['geometry'])

        # Get the list of tables to query
        for table in data['geometryType']:
            if table.lower() == 'all_geometry':
                self.config['tables'].append('ways_poly')
                self.config['tables'].append('ways_line')
                self.config['tables'].append('nodes')
                # self.config['tables'].append('relations')
            elif table.lower() == 'line':
                self.config['tables'].append('ways_line')
            elif table.lower() == 'polygon':
                self.config['tables'].append('ways_poly')
            elif table.lower() == 'point':
                self.config['tables'].append('nodes')

        # The filter define the tags to be used.
        for k, v in data['filters'].items():
            if k == 'tags' and 'all_geometry' in v:
                for k1, v1 in v['all_geometry'].items():
                    if k1 == 'join_or':
                        for k2, v2 in v1.items():
                            if type(v2) == list and len(v2) == 0:
                                tag = {k2: v2, 'op': 'or'}
                                self.config['where'].append(tag)
                            else:
                                v2['op'] = 'or'
                                self.config['where'].append(v2)
                    elif k1 == 'join_and':
                        v1['op'] = 'and'
                        self.config['where'].append(v1)
                # Anything under attributes scans the values that aren't
                # part of the data, Tags like osm_id, version, uid, user,
                # and timestamp.
                if k == 'attributes':
                    if 'all_geometry' in v:
                        attrs = v['all_geometry']
                    else:
                        attrs = v

        for entry in self.config['where']:
            for k, v in entry.items():
                if k == 'op':
                    continue
                # print(f"bar: {k} = {v}")
                self.config['select'].append({k: v})

        return self.config

    def dump(self):
        print("Dumping QueryConfig class")
        print("Select: ")
        for entry in self.config['select']:
            if type(entry) == dict:
                [[k, v]] = entry.items()
                if len(v) > 0:
                    print(f"\tConverting tag \'{k}\' to \'{v}\'")
                else:
                    print(f"\tSelecting tag \'{k}\'")
        print("Where: ")
        for entry in self.config['where']:
            if type(entry) == dict:
                # op = entry['op']
                for k, v in entry.items():
                    if k != 'op':
                        if type(v) == list and len(v) == 0:
                            print(f"\twhere tag \'{k}\' is \'not null\'")
                        else:
                            print(f"\twhere tag \'{k}\' is \'{v}\'")
                    else:
                        if entry['op'] is not None:
                            print(f"\t{entry['op']}")
            elif type(entry) == list:
                for item in entry:
                    print(f"{item}")
            else:
                print(f"\tReturn tag \'{entry}\'")
        print("Tables")
        for table in self.config['tables']:
            print(f"\t{table}")
        if self.geometry:
            print(self.geometry)
    
def main():    
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

    path = Path(args.infile)
    config = QueryConfig()
    result = None
    if path.suffix == '.json':
        result = config.parseJson(args.infile)
    elif path.suffix == '.yaml':
        result = config.parseYaml(args.infile)
    else:
        log.error(f"{args.infile} is an unsupported file format!")
        quit()

    # print(result)
    config.dump()

if __name__ == "__main__":
    main()
