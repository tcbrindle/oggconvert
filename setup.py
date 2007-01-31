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

from distutils.core import setup



setup(name='oggconvert',
      version='0.1.0',
      author='Tristan Brindle',
      author_email='t.c.brindle at gmail dot com',
      maintainer= 'Tristan Brindle',
      maintainer_email = 't.c.brindle at gmail dot com',
      description='A simple Gnome application to convert media to Free formats',
      url = 'http://launchpad.net/oggconvert',
      license='GNU LGPL',
      packages=['OggConvert'],
      package_data={'OggConvert' : ['*.glade']},
      scripts=['oggconvert'],
      data_files=[('share/applications/', ['oggconvert.desktop'])]
     )
