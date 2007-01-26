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


import gtk
import os.path

def timeremaining(elapsed, percent):
    """Returns a string with the remaining time for an operation.        
       elapsed: elapsed time for the operation so far (in seconds)
       percent: percentage of the operation completed so far"""
       
    if percent == 0:
        return "unknown time"
    else:
        secs_rem = int((100-percent) * elapsed/float(percent))
        time_rem = hourminsec(secs_rem)
        #I'm sure there are much smarter ways to do this...
        if time_rem[0] == 1:
            h_string = "1 hour"
        else:
            h_string = "%i hours" %time_rem[0]
            
        if time_rem[1] == 1:
            m_string = "1 minute"
        else:
            m_string = "%i minutes" %time_rem[1]
        
        if time_rem[2] == 2:
            s_string = "1 second"
        else:
            s_string = "%i seconds" %time_rem[2]
        
        if secs_rem > 3600:
            return "%s %s" %(h_string, m_string)
        elif secs_rem > 180:
            return "%s" %(m_string)
        elif secs_rem > 60:
            return "%s %s" %(m_string, s_string)
        else:
            return "%s" %(s_string)
            

def hourminsec(time):
    """Converts a given time in seconds to an (hours,minutes,seconds) tuple"""
    seconds = time
    minutes = seconds // 60
    seconds = seconds % 60
    hours = minutes //60
    minutes = minutes % 60	
    return (hours, minutes, seconds)
        
def confirm_overwrite(path, window=None):
    """
    Displays a dialogue asking the user to confirm they wish to overwrite the
    file given in path. Return True if they wish to overwrite, False otherwise.
    The option argument window specifies a GtkWindow to use as a transient.
    (And yes, the text is copied word-for-word from Nautilus...)
    """
    dialogue = gtk.MessageDialog(window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
     gtk.BUTTONS_NONE,
      "A file named \"%s\" already exists. Do you want to replace it?" %os.path.basename(path))
    
    dirname = os.path.basename(os.path.dirname(path)) # Urgh!
    dialogue.format_secondary_text("The file already exists in \"%s\". Replacing it will overwrite its contents." %dirname)
    
    dialogue.add_buttons(gtk.STOCK_CANCEL, 0, "_Replace", 1)
    response = dialogue.run()
    dialogue.destroy()
    if response ==1: return True
    else: return False
