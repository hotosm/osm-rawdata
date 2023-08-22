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

import argparse
import os
import sys

# find the path to the test data files
parser = argparse.ArgumentParser(description="Test parsing JSON")
parser.add_argument("-d", "--database", default=f"PG:colorado", help="The database name")
parser.add_argument("-b", "--boundary", help="The project AOI")
args = parser.parse_args()

def test_file():
    assert True

if __name__ == "__main__":
    print("--- test_file() ---")
    test_file()
