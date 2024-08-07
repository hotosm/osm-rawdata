#!/usr/bin/python3

# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_rawdata.
#
#     This is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_rawdata.  If not, see <https:#www.gnu.org/licenses/>.
#

import os
from io import BytesIO
from textwrap import dedent

#
# The JSON data files came from the raw-data-api project, and are currently
# used by that project for testing.
#
# Find the other files for this project
import osm_rawdata as rw
from osm_rawdata.config import QueryConfig

rootdir = rw.__path__[0]
if os.path.basename(rootdir) == "osm_rawdata":
    rootdir = "./tests/"


def test_levels():
    # this query contains many levels and geometries
    qc = QueryConfig()
    data = qc.parseJson(f"{rootdir}/levels.json")
    # qc.dump()
    hits = 0
    if data["where"]["nodes"][0]["amenity"][0] == "bank":
        hits += 1

    if "waterway" in data["where"]["ways_line"][3]:
        hits += 1

    if "admin_level" in data["select"]["ways_poly"][2]:
        hits += 1

    if (
        qc.config["fileName"] == "Example export with all features"
        and qc.config["outputType"] == "geojson"
    ):
        hits += 1

    assert hits == 4


def test_filters():
    # this query contains only the geometry and the output file name and type
    qc = QueryConfig()
    qc.parseJson(f"{rootdir}/filters.json")
    # qc.dump()
    hits = 0
    if "name" in qc.config["select"]["nodes"][0]:
        hits += 1
    if "addr" in qc.config["select"]["nodes"][1]:
        hits += 1
    if "building" in "building" in qc.config["where"]["nodes"][0]:
        hits += 1
    if "cafe" in qc.config["where"]["nodes"][1]["amenity"]:
        hits += 1
    if "restaurant" in qc.config["where"]["ways_poly"][1]["amenity"]:
        hits += 1

    assert hits == 5


def test_formats():
    # this query contains only the geometry and the output file name and type
    qc = QueryConfig()
    qc.parseJson(f"{rootdir}/formats.json")
    assert (
        qc.config["outputType"] == "shp"
        and qc.config["fileName"] == "Pokhara_all_features"
    )


def test_bytesio():
    qc = QueryConfig()
    with open(f"{rootdir}/formats.json", "rb") as file:
        json_obj = BytesIO(file.read())
    qc.parseJson(json_obj)
    assert (
        qc.config["outputType"] == "shp"
        and qc.config["fileName"] == "Pokhara_all_features"
    )


def test_yaml_no_joins():
    qc = QueryConfig()
    qc.parseYaml(f"{rootdir}/buildings_no_join.yaml")

    selected = qc.config["select"]
    # Keys: nodes, ways_poly, ways_line, relationships
    assert len(selected.keys()) == 4
    assert len(list(selected.values())[0]) == 4

    # Keys: nodes, ways_poly, ways_line, relationships
    where = qc.config["where"]
    assert len(where.keys()) == 4

    nodes = list(where.values())[0]
    assert len(nodes) == 4

    building = nodes[0]["building"]
    assert building == ["yes"]

    op = nodes[0]["op"]
    assert op == "or"


def test_yaml_no_joins_bytesio():
    """Read YAML file to BytesIO prior to config parse."""
    qc = QueryConfig()
    with open(f"{rootdir}/buildings_no_join.yaml", "rb") as file:
        yaml_obj = BytesIO(file.read())
    qc.parseYaml(yaml_obj)

    selected = qc.config["select"]
    assert len(selected.keys()) == 4
    assert len(list(selected.values())[0]) == 4

    where = qc.config["where"]
    assert len(where.keys()) == 4

    nodes = list(where.values())[0]
    assert len(nodes) == 4

    building = nodes[0]["building"]
    assert building == ["yes"]

    op = nodes[0]["op"]
    assert op == "or"


def test_yaml_bytesio_from_string():
    """Read YAML config directly from string input"""
    qc = QueryConfig()
    yaml_data = dedent(
        """
        select: null
        from:
          - nodes
          - ways_poly
          - ways_line
        where:
          tags:
            - building: not null
              highway: not null
              waterway: not null
    """
    )
    yaml_bytes = BytesIO(yaml_data.encode())
    config = qc.parseYaml(yaml_bytes)
    expected_config = {
        "select": {
            "nodes": [{"building": {}}, {"highway": {}}, {"waterway": {}}],
            "ways_poly": [{"building": {}}, {"highway": {}}, {"waterway": {}}],
            "ways_line": [{"building": {}}, {"highway": {}}, {"waterway": {}}],
            "relations": [],
        },
        "tables": ["nodes", "ways_poly", "ways_line"],
        "where": {
            "nodes": [
                {"building": ["not null"], "op": "or"},
                {"highway": ["not null"], "op": "or"},
                {"waterway": ["not null"], "op": "or"},
            ],
            "ways_poly": [
                {"building": ["not null"], "op": "or"},
                {"highway": ["not null"], "op": "or"},
                {"waterway": ["not null"], "op": "or"},
            ],
            "ways_line": [
                {"building": ["not null"], "op": "or"},
                {"highway": ["not null"], "op": "or"},
                {"waterway": ["not null"], "op": "or"},
            ],
            "relations": [],
        },
        "keep": [],
    }
    print(config)
    assert config == expected_config


def test_everything():
    # this query contains only the geometry, we want everything within this polygon
    qc = QueryConfig()
    qc.parseJson(f"{rootdir}/everything.json")
    data = "POLYGON ((83.96919250488281 28.194446860487773, 83.99751663208006 28.194446860487773, 83.99751663208006 28.214869548073377, 83.96919250488281 28.214869548073377, 83.96919250488281 28.194446860487773))"
    assert data == str(qc.geometry)


if __name__ == "__main__":
    print("--- test_everything() ---")
    test_everything()
    print("--- test_formats() ---")
    test_formats()
    print("--- test_levels() ---")
    test_levels()
    print("--- test_filters ---")
    test_filters()
    print("--- test_yaml_no_joins ---")
    test_yaml_no_joins()
    print("--- test_yaml_no_joins_bytesio ---")
    test_yaml_no_joins_bytesio()
    print("--- done() ---")
