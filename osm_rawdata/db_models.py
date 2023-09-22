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

from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, Column, ARRAY
from sqlalchemy import String, BigInteger, SmallInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
# from sqlalchemy.orm import MappedAsDataclass
# from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB


Base = declarative_base()
# FmtmMetadata = Base.metadata

class RawData(Base):
    """
    The base class for the Underpass database schema

    Attributes:
        uid (BigInteger): The ID of the user.
        user (String): The username of the user.
        version (SmallInteger): The OSM Version
        changeset (BigInteger): The Changeset number
        timestamp (DateTime): The timestamp of the changeset
        tags (ARRAY(String)): The OSM tags
    """
    __tablename__ = 'base'
    osm_id = Column(BigInteger, primary_key=True)
    uid = Column(BigInteger)
    user = Column(String, unique=True)
    version = Column(SmallInteger)
    changeset = Column(BigInteger)
    timestamp = Column(DateTime)
    tags = Column(ARRAY(String, dimensions=2))

class Nodes(RawData):
    """
    Class for a node
    
    Attributes:
        geom (Geometry): The geometry of the node
    """
    __tablename__ = 'points'
    osm_id = Column(BigInteger, ForeignKey("base.osm_id"))
    geom = Column(Geometry('POINT'))

class Ways(RawData):
     """
     Class for a polygon
    
     Attributes:
         geom (Geometry): The geometry of the node
     """
     __tablename__ = 'polygons'
     osm_id = Column(BigInteger, ForeignKey("base.osm_id"))
     geom = Column(Geometry('POLYGON'))

class Lines(RawData):
    """
     Class for a linestring
    
     Attributes:
         geom (Geometry): The geometry of the node
     """
    __tablename__ = 'lines'
    osm_id = Column(BigInteger, ForeignKey("base.osm_id"))
    geom = Column(Geometry('LINESTRING'))

