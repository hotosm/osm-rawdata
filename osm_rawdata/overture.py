#!/usr/bin/python3

# Copyright (c) 2023 Humanitarian OpenStreetMap Team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
    
import argparse
import logging
import sys
import os
from sys import argv
from geojson import Point, Feature, FeatureCollection, dump, Polygon
import geojson
from shapely.geometry import shape, Polygon, mapping
import shapely
from shapely import wkt, wkb
import pyarrow.parquet as pq
# import pyarrow as pa
from pandas import Series
import pandas as pd
import math
from numpy import ndarray
from progress.spinner import PixelSpinner
from codetiming import Timer

# Instantiate logger
log = logging.getLogger(__name__)

class Overture(object):
    def __init__(self,
                 filespec: str,
        ):
        """A class for parsing Overture V2 files.

        Args:
            data (list): The list of features
        """
        #pfile = pq.ParquetFile(filespec)
        # self.data = pfile.read()
        self.data = pd.read_parquet(filespec)
        self.filespec = filespec
        log.debug(f"Read {len(self.data)} entries from {filespec}")

    # def parsePlace(self,
    #                data: Series,
    #                 ):
    #     entry = dict()
    #     log.debug(data)

    # def parseHighway(self,
    #                data: Series,
    #                 ):
    #     entry = dict()
    #     log.debug(data)

    # def parseLocality(self,
    #                data: Series,
    #                 ):
    #     entry = dict()
    #     log.debug(data)

    def parse(self,
                    data: Series,
                    ):
        # log.debug(data)
        entry = dict()
        # timer = Timer(text="importParquet() took {seconds:.0f}s")
        # timer.start()
        for key,value in data.to_dict().items():
            if value is None:
                continue
            if type(value) == float and math.isnan(value):
                continue
            if key == 'geometry':
                geom = wkb.loads(value)
            if type(value) == ndarray:
                # the sources column is the only list
                # print(f"LIST: {key} = {value}")
                entry['source'] = value[0]['dataset']
                if value[0]['recordId'] is not None:
                    entry['record'] = value[0]['recordId']
                if value[0]['confidence'] is not None:
                    entry['confidence'] = value[0]['confidence']
            if type(value) == dict:
                if key == 'bbox':
                    continue
                # print(f"DICT: {key} = {value}")
                # the names column is the only dictionary we care about
                for k1, v1 in value.items():
                    if type(v1) == ndarray and len(v1) == 0:
                        continue
                    # FIXME: we should use the language to adjust the name tag
                    lang = v1[0]['language']
                    if k1 == 'common':
                        entry['loc_name'] = v1[0]['value']
                    if k1 == 'official':
                        entry['name'] = v1[0]['value']
                    if k1 == 'alternate':
                        entry['alt_name'] = v1[0]['value']
                    # print(f"ROW: {k1} = {v1}")
        #timer.stop()
        return Feature(geometry=geom, properties=entry)

def main():
    """This main function lets this class be run standalone by a bash script, primarily
    to assist in code development or debugging. This should really be a test case.

    """
    categories = ('buildings', 'places', 'highways', 'admin', 'localities')
    parser = argparse.ArgumentParser(
        prog="conflateDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This program contains common support used by the other programs",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="Input file")
    parser.add_argument("-o", "--outfile", default='overture.geojson', help="Output file")
    parser.add_argument("-c", "--category", choices=categories, required=True, help="Data category")

    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(threadName)10s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        log.addHandler(ch)

    overture = Overture(args.infile)

    features = list()
    spin = PixelSpinner(f"Processing {args.infile}...")
    timer = Timer(text="Parsing Overture data file took {seconds:.0f}s")
    timer.start()
    for index in overture.data.index:
        spin.next()
        feature = overture.data.loc[index]
        if args.category == 'buildings':
            entry = overture.parse(feature)
        # elif args.category == 'places':
        #     entry = overture.parsePlace(feature)
        # elif args.category == 'highway':
        #     entry = overture.parseHighway(feature)
        # elif args.category == 'locality':
        #     entry = overture.parseLocality(feature)
        features.append(entry)

    file = open(args.outfile, 'w')
    geojson.dump(FeatureCollection(features), file)
    timer.stop()

    log.info(f"Wrote {args.outfile}")

if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
