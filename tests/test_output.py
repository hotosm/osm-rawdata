#!/usr/bin/python3

# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
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
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#

import os
import sys
from osm_rawdata.postgres import DatabaseAccess
import geojson
from osm_rawdata.config import QueryConfig


# Find the other files for this project
import osm_rawdata as rw
rootdir = rw.__path__[0]
if os.path.basename(rootdir) == 'osm_rawdata':
    rootdir = f"./tests/"


def test_yaml():
    hits = 0
    db = DatabaseAccess('underpass')
    infile = open(f"{rootdir}/AOI.geojson", 'r')
    poly = geojson.load(infile)
    qc = QueryConfig()
    result = qc.parseYaml(f"{rootdir}/buildings.yaml")
    sql = db.createSQL(qc, True)
    out = "SELECT ST_AsText(geom), osm_id, version, tags->>'building', tags->>'amenity', tags->>'building:material', tags->>'roof:material' FROM nodes WHERE tags->>'building' ='yes' OR tags->>'amenity' ='not null' OR  tags->>'building:material' ='wood' AND tags->>'roof:material' ='metal'"
    if sql[0] == out:
        hits += 1

    json = db.createJson(qc, True)
    out = '{"geometry": true, "geometryType": ["point", "polygon"], "filters": {"tags": {"point": {"join_or": {"building": ["yes"], "amenity": ["not null"], "building:material": ["wood"], "roof:material": ["metal"]}, "join_and": {"building": ["yes"], "amenity": ["not null"], "building:material": ["wood"], "roof:material": ["metal"]}}, "polygon": {"join_or": {"building": ["yes"], "amenity": ["not null"], "building:material": ["wood"], "roof:material": ["metal"]}, "join_and": {"building": ["yes"], "amenity": ["not null"], "building:material": ["wood"], "roof:material": ["metal"]}}, "line": {"join_or": {}, "join_and": {}}}}}'
    if json == out:
        hits += 1

    assert hits == 2

if __name__ == "__main__":
    print("--- test_yaml() ---")
    test_yaml()

    
