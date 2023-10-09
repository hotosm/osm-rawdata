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

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, Column, DateTime, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# FmtmMetadata = Base.metadata


class RawData(Base):
    """The base class for the Underpass database schema.

    Attributes:
        osm_id (BigInteger): The ID of the feature
        uid (BigInteger): The ID of the user
        user (String): The username of the user
        version (SmallInteger): The OSM Version
        changeset (BigInteger): The Changeset number
        timestamp (DateTime): The timestamp of the changeset
        tags (JSONB): The OSM tags
    """

    __tablename__ = "base"
    osm_id = Column(BigInteger, primary_key=True, unique=True)
    uid = Column(BigInteger)
    user = Column(String)
    version = Column(SmallInteger)
    changeset = Column(BigInteger)
    timestamp = Column(DateTime)
    tags = Column(JSONB)


class Nodes(Base):
    """Class for a node.

    Attributes:
        id (BigInteger): The ID of the feature
        geom (Geometry): The geometry of the node
        tags (JSONB): The OSM tags
    """

    __tablename__ = "nodes"
    osm_id = Column(BigInteger, primary_key=True, unique=True)
    # osm_id = Column(BigInteger, ForeignKey("base.osm_id"))
    tags = Column(JSONB)
    geom = Column(Geometry("POINT", srid=4326))


class Ways(Base):
    """Class for a polygon.

    Attributes:
       uid (BigInteger): The ID of the user.
       geom (Geometry): The geometry of the node
    """

    __tablename__ = "ways_poly"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # osm_id = Column(BigInteger, ForeignKey("base.osm_id"))
    tags = Column(JSONB)
    geom = Column(Geometry("POLYGON", srid=4326))


class Lines(Base):
    """Class for a linestring.

    Attributes:
       uid (BigInteger): The ID of the user.
       geom (Geometry): The geometry of the node
    """

    __tablename__ = "ways_line"
    # osm_id = Column(BigInteger, ForeignKey("base.osm_id"))
    id = Column(BigInteger, primary_key=True, unique=True)
    tags = Column(JSONB)
    geom = Column(Geometry("LINESTRING", srid=4326))
