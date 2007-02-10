#/usr/bin/python
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



# Leave this set to None to let the programme decide whether to use audiorate
# based on which version of GStreamer you have.
# If you want to override this for any reason, you can set this to True of False
# as appropriate. Be warned that setting this to True for GStreamer versions 
# older than 0.10.11 is likely to stop the pipeline working completely.
USE_AUDIORATE = None

# Leave this set to None to have OggConvert detect whether schroenc is installed
# on this computer. This is recommended. If you really want to though, you can
# set this to True or False as you like. Be aware that setting it to True when
# schroenc doesn't exist will cause problems if you try to encode to Dirac
HAVE_SCHRO = None

FORMATS = ["THEORA", "SCHRO"]

THEORA_QUALITY_MAPPING = {1 : 1
                        , 2 : 7
                        , 3 : 14
                        , 4 : 21
                        , 5 : 28
                        , 6 : 35 
                        , 7 : 42
                        , 8 : 49
                        , 9 : 56
                        , 10: 63}
 
THEORA_OPTS = {"sharpness" : 1} 
 
                        
VORBIS_QUALITY_MAPPING = {1 : 0.1
                        , 2 : 0.2
                        , 3 : 0.3
                        , 4 : 0.4
                        , 5 : 0.5
                        , 6 : 0.6
                        , 7 : 0.7
                        , 8 : 0.8
                        , 9 : 0.9
                        , 10 : 1.0}


VORBIS_OPTS = {}

OGGMUX_OPTS = {}

SCHRO_OPTS = {}
