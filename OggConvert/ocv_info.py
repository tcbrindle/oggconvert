# -*- coding: UTF-8 -*-
#
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

import os.path
import sys

app_name = "oggconvert"

version = "0.3.0"

authors = ["Tristan Brindle <tcbrindle@gmail.com>"
          ,"Alex Kabakov <ak.anapa@gmail.com>"
          ,"Carlos Perelló Marín <carlos.perello@canonical.com>"]

artists = ["A. Bram Neijt <bneijt@gmail.com>"]

copyright = "© 2007 Tristan Brindle"

website = "http://oggconvert.tristanb.net/"

licence = """ This program is free software; you can redistribute it and/or 
 modify it under the terms of the GNU Lesser General Public
 License as published by the Free Software Foundation; either
 version 2.1 of the License, or (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 Lesser General Public License for more details.
 
 You should have received a copy of the GNU Lesser General Public
 License along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

basepath = os.path.abspath(sys.argv[0])

gladepath = os.path.dirname(os.path.abspath(__file__))
gladepath = os.path.join(gladepath, "oggcv.glade")

# This is a hack to work out whether we've been installed or are just running
# from an untarred directory.
# People who are squeamish should probably look away now

prefix = os.path.dirname(os.path.dirname(basepath))

localepath = os.path.join(prefix,"share","locale")
if not os.path.isdir(localepath):
    localepath = "mo"

pixmappath = os.path.join(prefix,"share","pixmaps")
if not os.path.isdir(pixmappath):
    pixmappath = "data"    

