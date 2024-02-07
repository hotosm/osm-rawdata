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

import geojson

import osm_rawdata as rw
from osm_rawdata.postgres import PostgresClient

rootdir = rw.__path__[0]
if os.path.basename(rootdir) == "osm_rawdata":
    rootdir = "./tests/"


def test_data_extract():
    pg = PostgresClient("underpass", f"{rootdir}/buildings.yaml")
    aoi_file = open(f"{rootdir}/AOI_small.geojson", "r")
    boundary = geojson.load(aoi_file)
    data_extract = pg.execQuery(boundary)
    assert len(data_extract.get("features")) == 16


def test_data_extract_flatgeobuf():
    pg = PostgresClient("underpass", f"{rootdir}/buildings.yaml")
    aoi_file = open(f"{rootdir}/AOI_small.geojson", "r")
    boundary = geojson.load(aoi_file)
    data_extract = pg.execQuery(boundary)
    assert len(data_extract.get("features")) == 16
