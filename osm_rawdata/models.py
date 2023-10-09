#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
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

# from sqlalchemy.orm import Mapped
# from sqlalchemy.orm import mapped_column
# from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, DateTime, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """The base class for the Underpass database schema.

    Attributes:
        uid (BigInteger): The ID of the user.
        user (String): The username of the user.
        version (SmallInteger): The OSM Version
        changeset (BigInteger): The Changeset number
        timestamp (DateTime): The timestamp of the changeset
        tags (ARRAY(String, dimension=2)): The OSM tags
    """

    uid: Column(BigInteger)
    user: Column(String)
    version: Column(SmallInteger)
    changeset: Column(BigInteger)
    timestamp: Column(DateTime)
    tags: Column(ARRAY(String, dimension=2))


class Nodes(Base):
    """Class for a node.

    Attributes:
        geom (Geometry): The geometry of the node
    """

    __tablenames__ = "points"
    geom = Column(Geometry("POINT"))


class Ways(Base):
    """Class for a polygon.

    Attributes:
        geom (Geometry): The geometry of the node
    """

    __tablenames__ = "polygons"
    geom = Column(Geometry("POLYGON"))


class Lines(Base):
    """Class for a linestring.

    Attributes:
        geom (Geometry): The geometry of the node
    """

    __tablenames__ = "lines"
    geom = Column(Geometry("LINESTRING"))
