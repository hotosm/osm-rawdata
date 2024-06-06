# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm-rawdata.
#
#     osm-rawdata is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     osm-rawdata is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm-rawdata.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Configuration and fixtures for PyTest."""

import logging
import sys

import psycopg2
import pytest

logging.basicConfig(
    level="DEBUG",
    format=(
        "%(asctime)s.%(msecs)03d [%(levelname)s] "
        "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
    ),
    datefmt="%y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def db():
    """Existing psycopg2 connection."""
    return psycopg2.connect("postgresql://fmtm:testpass@db:5432/underpass")
