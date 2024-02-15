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

"""YAML and JSON config parsing to a standardised config format."""

import argparse
import json
import logging
import sys
from io import BytesIO

# import time
from pathlib import Path
from sys import argv
from typing import Union

import flatdict
import yaml
from geojson import Polygon
from shapely.geometry import shape

# Find the other files for this project
import osm_rawdata as rw

rootdir = rw.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)


class QueryConfig(object):
    """Parse a config file into a data structure."""

    def __init__(self, boundary: Polygon = None):
        """Init the QueryConfig object.

        Args:
            boundary (Polygon): The project boundary.
        """
        self.config = {
            "select": {
                "nodes": [],
                "ways_poly": [],
                "ways_line": [],
            },
            "tables": [],
            "where": {
                "nodes": [],
                "ways_poly": [],
                "ways_line": [],
            },
            "keep": [],
        }
        self.geometry = boundary
        # for polygon extracts, sometimes we just want the center point
        self.centroid = False

    def parseYaml(self, config: Union[str, BytesIO]):  # noqa N802
        """Parse the YAML config file format into the internal data structure.

        Args:
            config (str, BytesIO): the file or BytesIO object to read.

        Returns:
            config (dict): The config data.
        """
        yaml_data = self.load_yaml(config)

        self._yaml_parse_tables(yaml_data)
        self._yaml_parse_where(yaml_data)
        self._yaml_parse_select_and_keep(yaml_data)
        self.config["keep"] = yaml_data.get("keep", [])

        return self.config

    @staticmethod
    def load_yaml(config: Union[str, BytesIO]):
        """Private method to load YAML data from a file.

        Args:
            config (str, BytesIO): The disk or memory file to read.

        Returns:
            data (dict): The loaded YAML data.
        """
        if isinstance(config, str):
            with open(config, "r") as file:
                return yaml.safe_load(file)
        elif isinstance(config, BytesIO):
            return yaml.safe_load(config.getvalue())
        else:
            log.error(f"Unsupported config format: {config}")
            raise ValueError(f"Invalid config {config}")

    def _yaml_parse_tables(self, data):
        """Private method to parse 'from' data.

        The table names are based on the Underpass schema:
        nodes, ways_poly, ways_line, relations.

        Args:
            data (dict): The YAML data.

        Returns:
            None
        """
        self.config["tables"] = data.get("from", [])

    def _yaml_parse_where(self, data):
        """Private method to parse 'where' data.

        Args:
            data (dict): The YAML data.

        Returns:
            None
        """
        tables = self.config.get("tables", [])
        # No tables specified, extract all tables
        if not tables:
            tables = ["nodes", "ways_line", "ways_poly"]

        for table in tables:
            self.config["where"][table] = []
            where_entries = data.get("where", {}).get("tags", [])

            for entry in where_entries:
                if entry == "op":
                    # Skip if already in correct {'op': 'or'} format
                    # Necessary?
                    continue

                # If no join passed, default to join_or
                if not any(key.startswith("join_") for key in entry.keys()):
                    entry = {"join_or": [entry]}

                # Extract key / values
                [[key, value]] = entry.items()

                # Get the operation type after join_
                op = key.split("_")[1]

                for tags in value:
                    for tag, selector in tags.items():
                        if selector is True:
                            # yes is required in osm tag query instead of true
                            selector = "yes"
                        if selector is None:
                            # empty instead of None (equivalent to not null)
                            newtag = {tag: [], "op": op}
                        else:
                            newtag = {tag: [selector], "op": op}
                        self.config["where"][table].append(newtag)

    def _yaml_parse_select_and_keep(self, data):
        """Private method to parse 'select' and 'keep' data.

        Args:
            data (dict): The YAML data.

        Returns:
            None
        """
        for table in self.config.get("tables", []):
            # 'select' not tags specified, use 'where' tags instead
            if data.get("select") is None:
                tags = [key for entry in self.config["where"][table] for key in entry.keys() if key != "op"]
                self.config["select"][table] = [{tag: {}} for tag in tags]

            # 'select' tags specified, process
            else:
                for tag in data.get("select", []):
                    if isinstance(tag, dict):
                        self.config["select"][table].append(tag)
                    else:
                        self.config["select"][table].append({tag: []})

                for tag in data.get("keep", []):
                    self.config["select"][table].append({tag: []})

    def parseJson(self, config: Union[str, BytesIO]):  # noqa N802
        """Parse the JSON format config file using the Underpass schema.

        Args:
            config (str, BytesIO): the file or BytesIO object to read.

        Returns:
            config (dict): the config data
        """
        # Check the type of config and load data accordingly
        if isinstance(config, str):
            with open(config, "r") as config_file:
                data = json.load(config_file)
        elif isinstance(config, BytesIO):
            config.seek(0)  # Reset the file pointer to the beginning
            data = json.load(config)
        else:
            log.error(f"Unsupported config format: {config}")
            raise ValueError(f"Invalid config {config}")

        # Helper function to convert geometry names
        def convert_geometry(geom_type):
            if geom_type == "point":
                return "nodes"
            elif geom_type == "line":
                return "ways_line"
            elif geom_type == "polygon":
                return "ways_poly"
            return geom_type

        # Extract geometry
        if geom_dict := data.get("geometry"):
            self.geometry = shape(geom_dict)

        # Iterate through each key-value pair in the flattened dictionary
        for key, value in flatdict.FlatDict(data).items():
            keys = key.split(":")
            # Skip the keys related to geometry
            if key.startswith("geometry"):
                continue
            # If it's a top-level key, directly update self.config
            if len(keys) == 1:
                self.config[key] = value
                continue

            # Extract meaningful parts from the key
            section, subsection = keys[:2]
            geom_type = keys[2] if len(keys) > 2 else None
            tag_type = keys[3] if len(keys) > 3 else None
            tag_name = keys[4] if len(keys) > 4 else None

            # Convert geometry type to meaningful names
            geom_type = convert_geometry(geom_type)

            if subsection == "attributes":
                # For attributes, update select fields and tables
                for attribute_name in value:
                    # FIXME needs a refactor to handle all_geometry correctly
                    if geom_type == "all_geometry":
                        for geometry_type in ["nodes", "ways_line", "ways_poly"]:
                            self.config["select"][geometry_type].append({attribute_name: {}})
                            self.config["tables"].append(geometry_type)
                    else:
                        self.config["select"][geom_type].append({attribute_name: {}})
                        self.config["tables"].append(geom_type)
            elif subsection == "tags":
                # For tags, update where fields
                option = tag_type[5:] if tag_type else None
                new_tag = {tag_name: value, "op": option}
                if geom_type == "all_geometry":
                    for geometry_type in ["nodes", "ways_line", "ways_poly"]:
                        self.config["where"][geometry_type].append(new_tag)
                else:
                    self.config["where"][geom_type].append(new_tag)

        return self.config

    def dump(self):
        """Dump the contents of the internal data strucute for debugging purposes."""
        print("Dumping QueryConfig class")

        # These two data items are only used by Export Tool for output files
        # for k, v in self.config.items():
        #     if k == 'nodes' or k == 'ways_poly' or k == 'ways_line' or k == 'keep' or k == 'tables' k ==:
        #         continue
        #     print(f"Other {k} is \'{v}\'")

        keys = list()
        for key, value in self.config["select"].items():
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, str):
                        print(f"\tSelecting table '{key}' has value '{v}'")
                        keys.append(v)
                        continue
                    for k1, v1 in v.items():
                        keys.append(v1)
                        print(f"\tSelecting table '{key}' tag '{k1}'")
            else:
                print(f"\tSelecting tag '{key}'")
        # print(f"\tSelecting tag \'{key}\' \'{k1}\' has values \'{keys}\'")
        print("Where: ")
        for key, value in self.config["where"].items():
            if isinstance(value, list):
                for v in value:
                    op = v["op"].upper()
                    # del v['op']
                    if isinstance(v, str):
                        print(f"\tWhere table '{key}' has value '{v}'")
                        keys.append(v)
                        continue
                    for k1, v1 in v.items():
                        keys.append(v1)
                        if k1 == "op":
                            continue
                        print(f"\tWhere table '{key}', tag '{k1}' has values '{v1}' {op}")
            else:
                print(f"\tSelecting tag '{key}'")
        # print("Tables")
        # for table in self.config['tables']:
        #    print(f"\t{table}")
        if self.geometry:
            print(self.geometry)


def main():
    """This main function lets this class be run standalone by a bash script."""
    parser = argparse.ArgumentParser(
        prog="config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Parse YAML or JSON SQL config file",
        epilog="""
        This should only be run standalone for debugging purposes.
        """,
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
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)

    path = Path(args.infile)
    config = QueryConfig()
    if path.suffix == ".json":
        config.parseJson(args.infile)
    elif path.suffix == ".yaml":
        config.parseYaml(args.infile)
    else:
        log.error(f"{args.infile} is an unsupported file format!")
        quit()

    # print(result)
    config.dump()


if __name__ == "__main__":
    """This is just a hook so this file can be run standalone during development."""
    main()
