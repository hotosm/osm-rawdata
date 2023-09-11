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
import yaml
import json
from sys import argv
from geojson import Feature, FeatureCollection, dump, Polygon
import geojson
# import time
from pathlib import Path
from shapely.geometry import shape
import flatdict


# Find the other files for this project
import osm_rawdata as rw
rootdir = rw.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class QueryConfig(object):
    def __init__(self,
                 boundary: Polygon = None
                 ):
        """This class parses a config file that defines the Query
        into data structure.
        
        Args:
                boundary (Polygon): The project boundary
        """
        self.config = {'select': dict(),
                       'tables': list(),
                       'where': dict(),
                       'keep': list(),
                       }
        self.config['select'] = {'nodes': [],
                                 'ways_poly': [],
                                 'ways_line': [],
                                 }
        self.config['where'] = {'nodes': [],
                                'ways_poly': [],
                                'ways_line': [],
                                }
        self.geometry = boundary
        # for polygon extracts, sometimes we just want the center point
        self.centroid = False

    def parseYaml(self,
                    filespec: str
                    ):
        """
        This method parses the YAML config file format into our internal
        data structure.

        Args:
                filespec (str): the file to read

        Returns:
                config (dict): the config data
        """
        file = open(filespec, 'r')
        path = Path(filespec)
        data = yaml.load(file, Loader=yaml.Loader)

        self.config['tables'] = data['from']
        for table in self.config['tables']:
            if data['select']:
                for entry in data['select']:
                    if type(entry) == dict:
                        self.config['select'][table].append(entry)
                    else:
                        self.config['select'][table].append({entry: list()})

                for entry in data['keep']:
                    self.config['select'][table].append({entry: list()})

                op = None
            for tag in data['where']['tags']:
                [[k, v]] = tag.items()
                if k[:4] == 'join':
                    op = k[5:]
                if tag == 'op':
                    continue
                for entry in v:
                    for k1, v1 in entry.items():
                        if v1 == True:
                            v1 = 'yes'
                        newtag = {k1: [v1]}
                        newtag['op'] = op
                        self.config['where'][table].append(newtag)
                for k2, v2 in entry.items():
                    newtag = {k2: dict()}
                    newtag['op'] = op
                    self.config['select'][table].append({k2: dict()})

        self.config['keep'] = data['keep']
        # The table names are based on the Underpass schema, nodes, ways_poly,
        # ways_line, relations
        return self.config

    def parseJson(self,
                  filespec: str
                  ):
        """
        Parse the JSON format config file used by the raw-data-api
        and export tool.

        Args:
                filespec (str): the file to read

        Returns:
                config (dict): the config data
        """

        file = open(filespec, 'r')
        data = json.load(file)
        # Get the geometry
        self.geometry = shape(data['geometry'])
        for key, value in flatdict.FlatDict(data).items():
            keys = key.split(':')
            # print(keys)
            # print(f"\t{value}")
            # We already have the geometry
            if key[:8] == 'geometry':
                continue
            if len(keys) == 1:
                self.config.update({key: value})
                continue
            # keys[0] is currently always 'filters'
            # keys[1] is currently 'tags' for the WHERE clause,
            # of attributes for the SELECT
            geom = keys[2]
            # tag = keys[4]
            # Get the geometry
            if geom == 'point':
                geom = 'nodes'
            elif geom == 'line':
                geom = 'ways_line'
            elif geom == 'polygon':
                geom = 'ways_poly'
            if keys[1] == 'attributes':
                for v1 in value:
                    if geom == 'all_geometry':
                        self.config['select']['nodes'].append({v1: {}})
                        self.config['select']['ways_line'].append({v1: {}})
                        self.config['select']['ways_poly'].append({v1: {}})
                        self.config['tables'].append('nodes')
                        self.config['tables'].append('ways_poly')
                        self.config['tables'].append('ways_line')
                    else:
                        self.config['tables'].append(geom)
                        self.config['select'][geom].append({v1: {}})
            if keys[1] == 'tags':
                newtag = {keys[4]: value}
                newtag['op'] = keys[3][5:]
                if geom == 'all_geometry':
                    self.config['where']['nodes'].append(newtag)
                    self.config['where']['ways_poly'].append(newtag)
                    self.config['where']['ways_line'].append(newtag)
                else:
                    self.config['where'][geom].append(newtag)

        return self.config

    def dump(self):
        """
        Dump the contents of the internal data strucute for debugging purposes
        """
        print("Dumping QueryConfig class")

        # These two data items are only used by Export Tool for output files
        # for k, v in self.config.items():
        #     if k == 'nodes' or k == 'ways_poly' or k == 'ways_line' or k == 'keep' or k == 'tables' k ==:
        #         continue
        #     print(f"Other {k} is \'{v}\'")

        keys = list()
        for key, value in self.config['select'].items():
            if type(value) == list:
                for v in value:
                    if type(v) == str:
                        print(f"\tSelecting table \'{key}\' has value \'{v}\'")
                        keys.append(v)
                        continue
                    for k1, v1 in v.items():
                        keys.append(v1)
                        print(f"\tSelecting table \'{key}\' tag \'{k1}\'")
            else:
                print(f"\tSelecting tag \'{key}\'")
        #print(f"\tSelecting tag \'{key}\' \'{k1}\' has values \'{keys}\'")
        print("Where: ")
        for key, value in self.config['where'].items():
            if type(value) == list:
                for v in value:
                    op = v['op'].upper()
                    # del v['op']
                    if type(v) == str:
                        print(f"\tWhere table \'{key}\' has value \'{v}\'")
                        keys.append(v)
                        continue
                    for k1, v1 in v.items():
                        keys.append(v1)
                        if k1 == 'op':
                            continue
                        print(f"\tWhere table \'{key}\', tag \'{k1}\' has values \'{v1}\' {op}")
            else:
                print(f"\tSelecting tag \'{key}\'")
        #print("Tables")
        #for table in self.config['tables']:
        #    print(f"\t{table}")
        if self.geometry:
            print(self.geometry)
    
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
    """This is just a hook so this file can be run standalone during development."""
    main()
