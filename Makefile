# Copyright (c) 2020, 2021 Humanitarian OpenStreetMap Team
#
# This file is part of Osm-RawData.
#
#     Osm-RawData is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Osm-RawData is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Osm-RawData.  If not, see <https:#www.gnu.org/licenses/>.
#

PACKAGE := org.osm_rawdata.py
NAME := osm-rawdata
VERSION := 0.4.0

# All python source files
# MDS := $(wildcard ./docs/*.md)
MDS := \
	docs/json.md \
	docs/yaml.md

PDFS := $(MDS:.md=.pdf)

all:
	@echo "Targets are:"
	@echo "	clean - remove generate files"
	@echo "	apidoc - generate Doxygen API docs"
	@echo "	check - run the tests"
	@echo "	uml - generate UNML diagrams"
	@echo "	install - install package for development"
	@echo "	uninstall - remove package from python"

uninstall:
	pip3 uninstall $(NAME)

install:
	pip3 install -e .

check:
	@pytest

clean:
	@rm -fr docs/{apidocs,html,docbook,man} docs/packages.png docs/classes.png

uml:
	cd docs && pyreverse -o png ../osm_rawdata

apidoc: force
	cd docs && doxygen

lint:
	@vulture osm_rawdata
# pylint
# pyflakes
# coverage

# Strip any unicode out of the markdown file before converting to PDF
pdf: $(PDFS)
%.pdf: %.md
	@echo "Converting $< to a PDF"
	@new=$(notdir $(basename $<)); \
	iconv -f utf-8 -t US $< -c | \
	pandoc $< -f markdown -t pdf -s -o /tmp/$$new.pdf

.SUFFIXES: .md .pdf

.PHONY: apidoc

force:
