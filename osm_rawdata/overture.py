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
import math
import sys

import geojson
import pandas as pd
from codetiming import Timer
from geojson import Feature, FeatureCollection
from numpy import ndarray

# import pyarrow as pa
from pandas import Series
from progress.spinner import PixelSpinner
from shapely import wkb

# Instantiate logger
log = logging.getLogger("osm-rawdata")


class Overture(object):
    def __init__(
        self,
        filespec: str = None,
    ):
        """A class for parsing Overture V2 files.

        Args:
            data (list): The list of features
        """
        # pfile = pq.ParquetFile(filespec)
        # self.data = pfile.read()
        if filespec:
            try:
                self.data = pd.read_parquet(filespec)
                log.debug(f"Read {len(self.data)} entries from {filespec}")
            except:
                log.error(f"Couldn't read data from {filespec}!")
        self.filespec = filespec

    def parse(
        self,
        data: Series,
    ):
        # log.debug(data)
        entry = dict()
        # timer = Timer(text="importParquet() took {seconds:.0f}s")
        # timer.start()
        for key, value in data.to_dict().items():
            if value is None:
                continue
            if type(value) == float and math.isnan(value):
                continue
            if key == "geometry":
                geom = wkb.loads(value)
            if type(value) == ndarray:
                # print(f"LIST: {key} = {value}")
                if type(value[0]) == dict:
                    for k1, v1 in value[0].items():
                        if v1 is not None:
                            if type(v1) == ndarray:
                                import epdb

                                epdb.st()
                            entry[k1] = v1
                else:
                    # FIXME: for now the data only has one entry in the array,
                    # but this could change.
                    if type(value[0]) == ndarray:
                        import epdb

                        epdb.st()
                    entry[key] = value[0]
                continue
            if key == "sources" and type(value) == list:
                if "dataset" in value[0]:
                    entry["source"] = value[0]["dataset"]
                if "recordId" in valve[0] and ["recordId"] is not None:
                    entry["record"] = value[0]["recordId"]
                if value[0]["confidence"] is not None:
                    entry["confidence"] = value[0]["confidence"]
                else:
                    entry["source"] = value["dataset"]
                if value[0]["recordId"] is not None:
                    entry["record"] = value[0]["recordId"]
                if value[0]["confidence"] is not None:
                    entry["confidence"] = value[0]["confidence"]
            if type(value) == dict:
                if key == "bbox":
                    continue
                for k1, v1 in value.items():
                    if v1 is None:
                        continue
                    if type(v1) == dict:
                        # print(f"DICT: {key} = {value}")
                        for k2, v2 in v1.items():
                            if v2 is None:
                                continue
                            if type(v2) == ndarray:
                                for k3, v3 in v2.tolist()[0].items():
                                    if v3 is not None:
                                        entry[k3] = v3
                            elif type(v2) == str:
                                entry[k2] = v2
                        continue
                    # FIXME: we should use the language to adjust the name tag
                    # lang = v1[0]['language']
        # timer.stop()
        return Feature(geometry=geom, properties=entry)


def main():
    """This main function lets this class be run standalone by a bash script, primarily
    to assist in code development or debugging. This should really be a test case.

    """
    categories = ("buildings", "places", "highways", "admin", "localities")
    parser = argparse.ArgumentParser(
        prog="conflateDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This program contains common support used by the other programs",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="Input file")
    parser.add_argument("-o", "--outfile", default="overture.geojson", help="Output file")

    args = parser.parse_args()

    # if verbose, dump to the terminal.
    if args.verbose:
        log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(threadName)10s - %(name)s - %(levelname)s - %(message)s")
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
        entry = overture.parse(feature)
        if entry["properties"]["dataset"] != "OpenStreetMap":
            features.append(entry)

    if len(features) > 0:
        file = open(args.outfile, "w")
        geojson.dump(FeatureCollection(features), file)
        timer.stop()
        log.info(f"Wrote {args.outfile}")
    else:
        log.info(f"There was no non OSM data in {args.infile}")

    spin.finish()


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
