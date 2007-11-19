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


import gtk
import os.path
from gettext import gettext as _
import ocv_info
import webbrowser




def timeremaining(elapsed, percent):
    """Returns a string with the remaining time for an operation.        
       elapsed: elapsed time for the operation so far (in seconds)
       percent: percentage of the operation completed so far"""
       
    if percent == 0:
        return _("unknown time ")
    else:
        secs_rem = int((100-percent) * elapsed/float(percent))
        time_rem = hourminsec(secs_rem)
        output = ""
        
        # Add hours
        if time_rem[0]==0:
            pass
        elif time_rem[0] == 1:
            output = output + _("1 hour") + " "
        else:
            output += _("%i hours") %time_rem[0] + " "
            
        # Add minutes
        if time_rem[1] == 0:
            pass
        elif time_rem[1] == 1:
            output = output + _("1 minute") + " " 
        else:
            output = output + _("%i minutes") %time_rem[1] + " "
        
        # Only add seconds if there are less than three minutes to go
        if secs_rem <179:
            if time_rem[2] == 0:
                pass
            elif time_rem[2] == 1:
                output = output + _("1 second") + " " 
            else:
                output = output + _("%i seconds") %time_rem[2] + " "
        
        return output
            

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
      _("A file named \"%s\" already exists. Do you want to replace it?") %os.path.basename(path))
    
    dirname = os.path.basename(os.path.dirname(path)) # Urgh!
    dialogue.format_secondary_text(_("The file already exists in \"%s\". Replacing it will overwrite its contents.") %dirname)
    
    dialogue.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, _("_Replace"), gtk.RESPONSE_OK)
    response = dialogue.run()
    dialogue.destroy()
    if response ==gtk.RESPONSE_OK: return True
    else: return False
    
def dirac_warning(window=None):
    """
    Displays a warning box asking the user to make sure they realise Dirac is
    experimental.
    Returns True if the user chooses to continue, False otherwise
    """
    
    dialogue = gtk.MessageDialog(window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
                 gtk.BUTTONS_NONE, _("Dirac encoding still experimental"))
                 
    dialogue.format_secondary_text(_("The Dirac encoder is still experimental. \
Files you convert with this version may not be viewable with future versions \
of the decoder."))

    dialogue.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, _("Contin_ue"), gtk.RESPONSE_OK)
    response = dialogue.run()
    dialogue.destroy()
    if response==gtk.RESPONSE_OK: return True
    else: return False
    
    
def cancel_check(window=None):
    """
    Pops up a dialogue box asking if the user is sure they want to stop encoding
    Returns True if to stop, False otherwise
    """
    dialogue = gtk.MessageDialog(window, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION,
                gtk.BUTTONS_NONE, _("Encoding is not complete"))
    
    dialogue.format_secondary_text(_("Are you sure you wish to cancel?"))
    
    dialogue.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, _("Contin_ue"), gtk.RESPONSE_OK)
    
    response = dialogue.run()
    dialogue.destroy()
    if response==gtk.RESPONSE_CANCEL: return True
    else: return False
    
def about_dialogue(window=None):
    """
    Pops up a standard GTK About dialogue. Grabs all the info from ocv_info.
    """
    dialogue = gtk.AboutDialog()
    dialogue.set_transient_for(window)
    
    dialogue.set_name("OggConvert")
    dialogue.set_authors(ocv_info.authors)
    dialogue.set_artists(ocv_info.artists)
    dialogue.set_version(ocv_info.version)
    dialogue.set_copyright(ocv_info.copyright)
    dialogue.set_website(ocv_info.website)
    dialogue.set_license(ocv_info.licence) # Learn to spell, GTK!
    dialogue.set_translator_credits(_("translator-credits"))
    
    dialogue.run()
    dialogue.destroy()

def show_url(dialog, link, userdata):
    webbrowser.open(link)

# I know this is a bit of strange place to do this, but...
gtk.about_dialog_set_url_hook(show_url, None)
   
