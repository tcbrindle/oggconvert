#!/usr/bin/python
#
#
# OggConvert -- Converts media files to Free formats
# (c) 2007 Tristan Brindle <t.c.brindle at gmail dot com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygst
pygst.require("0.10")
import gst
import ocv_constants

gstver = gst.version()

if ocv_constants.USE_AUDIORATE == None:
    if gstver[2] > 10:
        ocv_constants.USE_AUDIORATE = True
    else:
        ocv_constants.USE_AUDIORATE = False


if ocv_constants.HAVE_SCHRO == None:
    ocv_constants.HAVE_SCHRO = False
    if gstver[2] > 10:
        if not gst.element_factory_find("schroenc")==None:
            print "Schroedinger encoder found, using"
            ocv_constants.HAVE_SCHRO = True

