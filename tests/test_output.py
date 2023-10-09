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

import geojson

# Find the other files for this project
import osm_rawdata as rw
from osm_rawdata.config import QueryConfig
from osm_rawdata.postgres import DatabaseAccess

rootdir = rw.__path__[0]
if os.path.basename(rootdir) == "osm_rawdata":
    rootdir = "./tests/"


def test_yaml():
    hits = 0
    db = DatabaseAccess("underpass")
    infile = open(f"{rootdir}/AOI.geojson", "r")
    poly = geojson.load(infile)
    qc = QueryConfig()
    qc.parseYaml(f"{rootdir}/buildings.yaml")
    sql = db.createSQL(qc, True)
    out = "SELECT ST_AsText(geom), osm_id, version, tags->>'building', tags->>'amenity', tags->>'building:material', tags->>'roof:material' FROM nodes WHERE tags->>'building' ='yes' OR tags->>'amenity' IS NOT NULL OR  tags->>'building:material' ='wood' AND tags->>'roof:material' ='metal'"
    if sql[0] == out:
        hits += 1

    qc = QueryConfig()
    json = db.createJson(qc, poly, True)
    geojson.loads(json)
    #    import epdb ; epdb.st()
    #    if json == out:
    #        hits += 1

    assert hits == 1


def test_json():
    hits = 0
    db = DatabaseAccess("underpass")
    infile = open(f"{rootdir}/AOI.geojson", "r")
    geojson.load(infile)
    qc = QueryConfig()
    qc.parseJson(f"{rootdir}/levels.json")
    sql = db.createSQL(qc, True)
    out = "SELECT ST_AsText(geom), osm_id, version, tags->>'building', tags->>'ground_floor:height', tags->>'capacity:persons', tags->>'building:structure', tags->>'building:condition', tags->>'name', tags->>'admin_level', tags->>'building:material', tags->>'office', tags->>'building:roof', tags->>'backup_generator', tags->>'access:roof', tags->>'building:levels', tags->>'building:floor', tags->>'addr:full', tags->>'addr:city', tags->>'source' FROM nodes WHERE tags->>'amenity'  IN ('bank', 'ferry_terminal', 'bus_station', 'fuel', 'kindergarten', 'school', 'college', 'university', 'place_of_worship', 'marketplace', 'clinic', 'hospital', 'police', 'fire_station') OR tags->>'building'  IN ('bank', 'aerodrome', 'ferry_terminal', 'train_station', 'bus_station', 'pumping_station', 'power_substation', 'kindergarten', 'school', 'college', 'university', 'mosque', 'church', 'temple', 'supermarket', 'marketplace', 'clinic', 'hospital', 'police', 'fire_station', 'stadium ', 'sports_centre', 'governor_office ', 'townhall ', 'subdistrict_office ', 'village_office ', 'community_group_office', 'government_office') OR tags->>'man_made'  IN ('tower', 'water_tower', 'pumping_station') OR tags->>'tower' ='communication' OR tags->>'aeroway' ='aerodrome' OR tags->>'railway' ='station' OR tags->>'emergency' ='fire_hydrant' OR tags->>'landuse'  IN ('reservoir', 'recreation_gound') OR tags->>'waterway' ='floodgate' OR tags->>'natural' ='spring' OR tags->>'power'  IN ('tower', 'substation') OR tags->>'shop' ='supermarket' OR tags->>'leisure'  IN ('stadium ', ' sports_centre ', ' pitch ', ' swimming_pool', 'park') OR tags->>'office' ='government'"
    if sql[0] == out:
        hits += 1

    qc.parseJson(f"{rootdir}/levels.json")
    json = db.createJson(qc, True)
    new = geojson.loads(json)
    item = [
        "bank",
        "ferry_terminal",
        "bus_station",
        "fuel",
        "kindergarten",
        "school",
        "college",
        "university",
        "place_of_worship",
        "marketplace",
        "clinic",
        "hospital",
        "police",
        "fire_station",
    ]
    if item == new["filters"]["tags"]["point"]["join_or"]["amenity"]:
        hits += 1

    assert hits == 2


if __name__ == "__main__":
    print("--- test_yaml() ---")
    test_yaml()
    print("--- test_json() ---")
    test_json()
