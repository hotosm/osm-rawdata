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
"""Test JSON functionality."""

import os

# Find the other files for this project
import osm_rawdata as rw
from osm_rawdata.config import QueryConfig

rootdir = rw.__path__[0]
if os.path.basename(rootdir) == "osm_rawdata":
    rootdir = "./tests/"
# print(f"\t{rootdir}")


def test_levels():
    # this query contains only the geometry and the output file name and type
    qc = QueryConfig()
    qc.parseJson(f"{rootdir}/levels.json")
    qc.dump()
    assert qc.filename == "Example export with all features" and qc.outputtype == "geojson"


def test_filters():
    # this query contains only the geometry and the output file name and type
    qc = QueryConfig()
    qc.parseJson(f"{rootdir}/filters.json")
    qc.dump()
    hits = 0
    if "name" in qc.config["select"][0]:
        hits += 1
    if "addr" in qc.config["select"][1]:
        hits += 1
    if "building" in qc.config["select"][2]:
        hits += 1
    if "cafe" in qc.config["select"][3]["amenity"]:
        hits += 1
    if "restaurant" in qc.config["select"][3]["amenity"]:
        hits += 1
    if "pub" in qc.config["select"][3]["amenity"]:
        hits += 1

    assert hits == 6


def test_formats():
    # this query contains only the geometry and the output file name and type
    qc = QueryConfig()
    qc.parseJson(f"{rootdir}/formats.json")
    assert qc.outputtype == "shp" and qc.filename == "Pokhara_all_features"


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
