# -*- coding: UTF-8 -*-
#
# OggConvert -- Converts media files to Free formats
# (c) 2007 Tristan Brindle <tcbrindle at gmail dot com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygst
pygst.require("0.10")
import gst
import ocv_constants

gstver = gst.version()

if ocv_constants.USE_AUDIORATE is None:
    if gstver[2] > 10:
        ocv_constants.USE_AUDIORATE = True
    else:
        ocv_constants.USE_AUDIORATE = False


if ocv_constants.HAVE_SCHRO is None:
    ocv_constants.HAVE_SCHRO = False
    if gstver[2] > 10:
        schrofac = gst.element_factory_find("schroenc")
        if schrofac is not None:
            if schrofac.check_version(0,10,14):
                print "Schrödinger encoder found, using"
                ocv_constants.HAVE_SCHRO = True
            else:
                print "Old Schrödinger version found, please upgrade"
            
if ocv_constants.HAVE_MATROSKA is None:
    if gst.element_factory_find("matroskamux") is None:
        ocv_constants.HAVE_MATROSKA = False
    else:
        ocv_constants.HAVE_MATROSKA = True
        
if ocv_constants.HAVE_WEBM is None:
    if (ocv_constants.HAVE_MATROSKA is True) and \
       gst.element_factory_find("matroskamux").check_version(0, 10, 22):
        print "Webm container multiplexer found, using"
        ocv_constants.HAVE_WEBM = True
    else:
        ocv_constants.HAVE_WEBM = False
           
if ocv_constants.HAVE_VP8 is None:
    if gst.element_factory_find("vp8enc"):
        print "VP8 encoder found, using"
        ocv_constants.HAVE_VP8 = True
    else:
        ocv_constants.HAVE_VP8 = False
