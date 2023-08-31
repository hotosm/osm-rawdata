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
from geojson import Feature, FeatureCollection, dump, Polygon
import geojson
# import time
from pathlib import Path
from shapely.geometry import shape


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
                       'keep': list()
                       }
        self.config['select'] = {'nodes': [], 'ways_poly': [], 'ways_line': []}
        self.config['where'] = {'nodes': [], 'ways_poly': [], 'ways_line': []}
        self.geometry = boundary
        # These are only in the JSON queries used for Export Tool
        self.outputtype = None
        self.filename = None
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

        # This is only used by Export Tool
        if 'outputType' in data:
            self.outputtype = data['outputType']

        # This is only used by Export Tool
        if 'fileName' in data:
            self.filename = data['fileName']

        # This is only used by Export Tool
        if 'geometryType' not in data:
            data['geometryType'] = 'all_geometry'

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

        if 'filters' not in data:
            data['filters'] = {}
        # The filter define the tags to be used.
        for k, v in data['filters'].items():
            if k == 'tags':
                if 'point' in v:
                    for k1, v1 in v['point'].items():
                        for k2, v2 in v1.items():
                            self.config['select']['nodes'].append({k2: v2})
                            self.config['where']['nodes'].append({k2: v2})
                            # print(f"POINT: {k2} == {v2}")
                elif 'line' in v:
                    for k1, v1 in v['line'].items():
                        # print(f"LINE: {k} = {v1}")
                        self.config['where']['ways_line'].append(v1)
                        self.config['select']['ways_line'].append(v1)
                elif 'polygon' in v:
                    for k1, v1 in v['polgon'].items():
                        # print(f"POLY: {k} = {v1}")
                        self.config['select']['ways_poly'].append(v1)
                        self.config['where']['ways_poly'].append(v1)
                elif 'all_geometry' in v:
                    # import epdb ; epdb.st()
                    for k1, v1 in v['all_geometry'].items():
                        # print(f"ALL_GEOMETRY: {k1} == {v1}")
                        if k1[:4] == 'join':
                            v1['op'] = k1[5:]
                        self.config['select']['nodes'].append(v1)
                        self.config['select']['ways_poly'].append(v1)
                        self.config['select']['ways_line'].append(v1)
                        # Where is the same tags, but has a or/and
                        self.config['where']['nodes'].append(v1)
                        self.config['where']['ways_poly'].append(v1)
                        self.config['where']['ways_line'].append(v1)
            # Anything under attributes scans the values that aren't
            # part of the data, Tags like osm_id, version, uid, user,
            # and timestamp.
            if k == 'attributes':
                # print(f"FIXME: {k} = {v}")
                if 'all_geometry' in v:
                    for i in v['all_geometry']:
                        self.config['select']['nodes'].append({i: []})
                        self.config['select']['ways_line'].append({i: []})
                        self.config['select']['ways_poly'].append({i: []})
                else:
                    if type(v) == dict:
                        if 'point' in v:
                            for v1 in v['point']:
                                # print(f"POINT2: {v1}")
                                self.config['select']['nodes'].append(v1)
                        # else:
                            # print(f"OOPS: {v1}")

                        if 'line' in v:
                            for v1 in v['line']:
                                # print(f"LINE2: {v1}")
                                self.config['select']['ways_line'].append(v1)
                        if 'polygon' in v:
                            for v1 in v['polygon']:
                                self.config['select']['ways_poly'].append(v1)
                                # print(f"POLY2: {v1}")
                    else:
                        self.config['select'].append({v: []})

        # for entry in self.config['where']:
        #     for k, v in entry.items():
        #         if k == 'op':
        #             continue
        #         print(f"bar: {k} = {v}")
        #         #for k1, v1 in v
        #         self.config['select'].append({k: v})

        return self.config

    def dump(self):
        """
        Dump the contents of the internal data strucute for debugging purposes
        """
        print("Dumping QueryConfig class")

        # These two data items are only used by Export Tool for output files
        if self.filename:
            print(f"The output filename is {self.filename}")
        if self.outputtype:
            print(f"The output type is {self.outputtype}")

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
                    del v['op']
                    if type(v) == str:
                        print(f"\tWhere table \'{key}\' has value \'{v}\'")
                        keys.append(v)
                        continue
                    for k1, v1 in v.items():
                        keys.append(v1)
                        print(f"\tWhere table \'{key}\', tag \'{k1}\' has values \'{v1}\' {op}")
            else:
                print(f"\tSelecting tag \'{key}\'")
        print("Tables")
        for table in self.config['tables']:
            print(f"\t{table}")
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
