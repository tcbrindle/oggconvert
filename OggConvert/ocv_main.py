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

import locale
from gettext import gettext as _
import gettext
import sys
import os
import os.path
import urllib

import gobject
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade

import ocv_init
from ocv_in_progress import ProgressWindow
from ocv_transcoder import Transcoder 
from ocv_media_checker import MediaChecker
from ocv_util import confirm_overwrite, dirac_warning, about_dialogue
import ocv_constants
from ocv_info import app_name, gladepath, localepath, pixmappath

class Main:
    def __init__(self):
            
        # Init the list of languages to support
        langs = []
        
        #Check the default locale
        lc, encoding = locale.getdefaultlocale()
        if (lc):
            #If we have a default, it's the first in the list
            langs = [lc]
            
        # Now lets get all of the supported languages on the system
        language = os.environ.get('LANGUAGE', None)
        if (language):
            """langage comes back something like en_CA:en_US:en_GB:en
            on linuxy systems, on Win32 it's nothing, so we need to
            split it up into a list"""
            langs += language.split(":")
         
        """Now langs is a list of all of the languages that we are going
        to try to use.  First we check the default, then what the system
        told us, and finally the 'known' list"""
        gettext.bindtextdomain(app_name,localepath)
        gettext.textdomain(app_name)
        
        # Get the language to use
        self.lang = gettext.translation(app_name, localepath
            , languages=langs, fallback = True)
        """Install the language, map _() (which we marked our
        strings to translate with) to self.lang.gettext() which will
        translate them."""
        
        # init glade UI translations
        gtk.glade.bindtextdomain(app_name, localepath)
        gtk.glade.textdomain(app_name)

        self._wtree = gtk.glade.XML(gladepath, "app_window")

        signals = {
            "on_about_clicked" : self._about,
            "on_app_window_delete" : self._on_quit,
#            "on_app_window_destroy" : self._on_quit,
            "on_container_format_changed": self._on_container_changed,
            "on_convert_clicked" : self._on_go,
            "on_filechooserbutton_selection_changed" : self._on_file_changed,
            "on_format_changed": self._on_format_changed,
            "on_quit_clicked" : self._on_quit,
            }

        self._window = self._wtree.get_widget("app_window")
        self._file_chooser_button = self._wtree.get_widget("filechooserbutton")
        self._save_folder_button = self._wtree.get_widget("save_folder_button")
        self._outfile_entry = self._wtree.get_widget("outfile_entry") 
        self._video_quality_slider = self._wtree.get_widget("video_quality_slider")
        self._video_quality_label = self._wtree.get_widget("video_quality_label")
        self._audio_quality_slider = self._wtree.get_widget("audio_quality_slider")
        self._audio_quality_label = self._wtree.get_widget("audio_quality_label")
        self._go_button = self._wtree.get_widget("go_button")
        self._format_combobox = self._wtree.get_widget("format_combobox")
        self._format_label = self._wtree.get_widget("format_label")
        self._container_combobox = self._wtree.get_widget("container_combobox")
        self._container_expander = self._wtree.get_widget("container_expander")

        self._format_combobox.set_active(0)
        if ocv_constants.HAVE_SCHRO:
            self._format_combobox.show()
            self._format_label.show()

        if ocv_constants.HAVE_MATROSKA:
            self._container_expander.show()
            self._container_combobox.set_active(0)
            self._container_combobox.show()

        self._set_up_filechooser()
              
        self._wtree.signal_autoconnect(signals)
        
        self._window.set_title("OggConvert")
        
        gtk.window_set_default_icon_from_file(os.path.join(pixmappath,"oggconvert.svg"))
        # I want to set the window to a minimum of 360px, but allow it to be
        # wider if a translated version requires it (most do); whilst this
        # command does it, it also stops the window auto-resizing when the 
        # "Advanced" spin is opened. Anyone know how to get round this?
        #self._window.set_geometry_hints(None, min_width=360)
        self._window.show_all()
                  
    def _on_go(self, button):
        self._outfile_folder = self._save_folder_button.get_filename()
        self._outfile_name = self._outfile_entry.get_text()
        self._outfile = os.path.join(self._outfile_folder, self._outfile_name)

        # Check destination is writable
        if not os.access(self._outfile_folder, os.W_OK):
            dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                                gtk.MESSAGE_ERROR,
                                gtk.BUTTONS_CLOSE,
                                _("Folder is not writable"))
            dialogue.format_secondary_text(_("Cannot save to this folder"))
            dialogue.run()
            dialogue.destroy()            
            return
        
        # Now check whether the file already exists
        if os.path.exists(self._outfile) and (self._input_file != None):        
            if os.path.samefile(self._outfile, self._input_file):
                dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_ERROR,
                                    gtk.BUTTONS_CLOSE,
                                    _("Using the same file for input and output"))
                dialogue.format_secondary_text(_("Choose a different name for the save file, or save to a different location."))
                dialogue.run()
                dialogue.destroy()            
                return    
            else: 
                if not confirm_overwrite(self._outfile, self._window):
                    return
              
        
        # If Dirac is selected, flash up a warning to show it's experimental
        format = ocv_constants.FORMATS[int(self._format_combobox.get_active())]
        if format == "SCHRO":
            if not dirac_warning(self._window):
                return

        # Get file format choosen.
        container = ocv_constants.CONTAINER_FORMATS[int(
            self._container_combobox.get_active())]

        # Now if we're still good to go...        
        #self._window.hide()
        vquality = self._video_quality_slider.get_value()
        aquality = self._audio_quality_slider.get_value()
        tc = Transcoder(
            self._input_uri, self._outfile, format, vquality, aquality,
            container)
        pr = ProgressWindow(tc, self._input_uri, self._outfile)
        self._window.hide()
        pr.run()
        self._window.show()

    def _on_quit(self, *args ):
        print _("Bye then!")
        gtk.main_quit()

    def _on_file_changed(self, filechooser):
        # self._input_file is only defined if the source is local
        self._input_uri = filechooser.get_uri()
        self._input_file = filechooser.get_filename()
        self._set_sensitivities("NO_MEDIA")
        
        if not self._input_uri == None:
            # gtk.FileChooser.get_uri returns an escaped string, which is not
            # what we want, so this hack uses urllib to change it back.
            self._input_uri = urllib.url2pathname(self._input_uri)
            gobject.idle_add(self._check_media,self._input_uri)
            
        folder = filechooser.get_current_folder()
        if (folder != None) and (os.access(folder,os.W_OK)):
            self._outfile_folder = filechooser.get_current_folder()
        else:
            self._outfile_folder = os.path.expanduser('~')
        self._save_folder_button.set_current_folder(self._outfile_folder)
        self._outfile_entry.set_text("")

    def _check_media(self, filename):
        self.mc = MediaChecker(filename)
        self.mc.connect("finished", self._on_media_discovered)
        self.mc.run()
        return False # only get called once
        
    def _on_media_discovered(self, *args):
        if self.mc.is_media:
            self._input_has_video = self.mc.has_video
            self._set_extension()
            
            if (self.mc.has_audio):
                self._set_sensitivities("AUDIO")
            if (self.mc.has_video):
                self._set_sensitivities("VIDEO")
            
        else:
            # What about auto codec installation? 
            dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                         gtk.MESSAGE_ERROR,
                         gtk.BUTTONS_CLOSE,
                         _("The file \"%s\" cannot be converted") %os.path.basename(self._input_file))
            dialogue.format_secondary_text(_("The file format \"%s\" is not supported." %self.mc.mimetype))
            dialogue.run()
            dialogue.destroy()
            self._file_chooser_button.unselect_all()       
        del self.mc
        
        
    def _set_extension(self):
        container = ocv_constants.CONTAINER_FORMATS[int(self._container_combobox.get_active())] 
        if container=='OGG':
            if self._input_has_video:
                new_ext = 'ogv'
            else:
                new_ext = 'ogg'
        elif container=='MATROSKA':
            if self._input_has_video:
                new_ext = 'mkv'
            else:
                new_ext = 'mka'
        else:
            # When a new container support is added this code needs to be
            # updated.
            raise AssertionError('Unknown container format')
                    
        self._outfile_name = self._outfile_entry.get_text()
        if self._outfile_name:
            basename, ext = os.path.splitext(self._outfile_name)
        elif self._input_uri:
            # Get basename from the source file
            # Luckily, os.path.splitext works with uris as it does with files
            basename, ext = os.path.splitext(
                os.path.basename(self._input_uri))
        else:
            # Nothing to do, no file is yet selected.
            return

        self._outfile_name = '%s.%s' % (basename, new_ext)
        self._outfile_entry.set_text(self._outfile_name)

    def _on_container_changed(self, combobox):
        container = ocv_constants.CONTAINER_FORMATS[int(combobox.get_active())]
        if ((container == 'MATROSKA') & (ocv_constants.FORMATS[int(self._format_combobox.get_active())] == 'SCHRO')):
            # DIRAC format selected. It cannot be stored in Matroska
            # container, warn the user and change the format to Theora.
            dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, 
                _("Dirac video cannot be stored in Matroska files. Using Theora instead.") )
            dialogue.run()
            dialogue.destroy()
            self._format_combobox.set_active(
                ocv_constants.FORMATS.index('THEORA'))
        self._set_extension()


    def _on_format_changed(self, combobox):
        if (ocv_constants.FORMATS[int(combobox.get_active())] == 'SCHRO'):
             #DIRAC format selected. It cannot be stored in Matroska
             #container, warn the user and change container to Ogg.
            if (ocv_constants.CONTAINER_FORMATS[
                int(self._container_combobox.get_active())] == 'MATROSKA'):
                dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, 
                    _("Dirac video cannot be stored in Matroska files. Using Ogg instead.") )
                dialogue.run()
                dialogue.destroy()
                self._container_combobox.set_active(
                    ocv_constants.CONTAINER_FORMATS.index('OGG'))

    def _about(self, button):
        about_dialogue(self._window)

    def _set_up_filechooser(self):     
        video = gtk.FileFilter()
        video.set_name(_("Video Files"))
        video.add_mime_type("video/*")
        # Special case for Flash video
        video.add_mime_type("application/x-flash-video")
        audio = gtk.FileFilter()
        audio.set_name(_("Audio Files"))
        audio.add_mime_type("audio/*")
        allmedia = gtk.FileFilter()
        allmedia.set_name(_("All Media Files"))
        allmedia.add_mime_type("video/*")
        allmedia.add_mime_type("application/x-flash-video")
        allmedia.add_mime_type("audio/*")
        allfiles = gtk.FileFilter()
        allfiles.set_name(_("All Files"))
        allfiles.add_pattern("*")
        self._file_chooser_button.add_filter(allmedia) 
        self._file_chooser_button.add_filter(video)
        self._file_chooser_button.add_filter(audio)
        self._file_chooser_button.add_filter(allfiles)
        
        self._file_chooser_button.set_current_folder(
                        os.path.expanduser("~"))
        
        self._file_chooser_button.set_local_only(False)
                        

    def _set_sensitivities(self,status):
        if (status == "NO_MEDIA"):
            self._go_button.set_sensitive(False)
            self._audio_quality_slider.set_sensitive(False)
            self._audio_quality_label.set_sensitive(False)
            self._video_quality_slider.set_sensitive(False)
            self._video_quality_label.set_sensitive(False)
            self._format_combobox.set_sensitive(False)
            self._format_label.set_sensitive(False)
            self._container_expander.set_sensitive(False)
        elif (status == "AUDIO"):
            self._go_button.set_sensitive(True)
            self._audio_quality_slider.set_sensitive(True)
            self._audio_quality_label.set_sensitive(True)
            self._container_expander.set_sensitive(True)       
        elif (status == "VIDEO"):
            self._go_button.set_sensitive(True)
            self._video_quality_slider.set_sensitive(True)
            self._video_quality_label.set_sensitive(True)
            self._format_combobox.set_sensitive(True)
            self._format_label.set_sensitive(True)
            self._container_expander.set_sensitive(True)
        else:
            print "Undefined status ",status," called"
        
        
if __name__ == "__main__":
    gobject.threads_init()
    main = Main()
    gtk.main()
        
