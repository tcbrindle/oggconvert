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

import os
from os import path
import re
from distutils.core import setup
from OggConvert import ocv_info

data_files=[('share/applications/', ['data/oggconvert.desktop']),
            ('share/pixmaps/',['data/oggconvert.svg']) ]


# Freshly generate .mo from .po, add to data_files:
# This copied directly from KungFu, thanks Jason!
if path.isdir('mo/'):
	os.system ('rm -r mo/')
for name in os.listdir('po'):
	m = re.match(r'(.+)\.po$', name)
	if m != None:
		lang = m.group(1)
		out_dir = 'mo/%s/LC_MESSAGES' % lang
		out_name = path.join(out_dir, 'oggconvert.mo')
		install_dir = 'share/locale/%s/LC_MESSAGES/' % lang		
		os.makedirs(out_dir)
  		os.system('msgfmt -o %s po/%s' % (out_name, name))
		data_files.append((install_dir, [out_name]))
		
setup(name='oggconvert',
      version=ocv_info.version,
      author='Tristan Brindle',
      author_email='t.c.brindle at gmail dot com',
      description='A simple application to convert media to Free formats',
      url = 'http://oggconvert.tristanb.net',
      license='GNU LGPL',
      packages=['OggConvert'],
      package_data={'OggConvert' : ['*.glade']},
      scripts=['oggconvert'],
      data_files=data_files
     )
