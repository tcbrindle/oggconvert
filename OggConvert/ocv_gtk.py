#!/usr/bin/python
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

import gobject
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
import os
import os.path
import locale
from gettext import gettext as _
import gettext
import sys
from ocv_gst import Transcoder, MediaChecker
from ocv_util import timeremaining, hourminsec, confirm_overwrite, \
                dirac_warning, stall_warning, cancel_check, about_dialogue
import ocv_constants
from ocv_info import app_name

class Main:
    def __init__(self):
        # init get text traslations
        
        #Get the local directory since we are not installing anything
        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))+'/locale'
        
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
        gettext.bindtextdomain(app_name, self.local_path)
        gettext.textdomain(app_name)
        
        # Get the language to use
        self.lang = gettext.translation(app_name, self.local_path
            , languages=langs, fallback = True)
        """Install the language, map _() (which we marked our
        strings to translate with) to self.lang.gettext() which will
        translate them."""
        #print langs
        #_ = self.lang.gettext
        #print dir(self.lang)
        #print self.lang.output_charset()
        
        # init glade UI translations
        gtk.glade.bindtextdomain(app_name, self.local_path)
        gtk.glade.textdomain(app_name)

        gladepath = os.path.dirname(os.path.abspath(__file__))
        gladepath = os.path.join(gladepath, "oggcv.glade")
        self._wtree = gtk.glade.XML(gladepath, "app_window")
        self._input_has_video = False

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
        self._audio_quality_slider = self._wtree.get_widget("audio_quality_slider")
        self._go_button = self._wtree.get_widget("go_button")
        self._format_combobox = self._wtree.get_widget("format_combobox")
        self._format_label = self._wtree.get_widget("format_label")
        self._container_combobox = self._wtree.get_widget("container_combobox")

        self._format_combobox.set_active(0)
        if ocv_constants.HAVE_SCHRO:
            self._format_combobox.show()
            self._format_label.show()

        self._container_combobox.set_active(0)
        self._container_combobox.show()

        self._set_up_filechooser()
              
        self._wtree.signal_autoconnect(signals)
        
        self._window.set_title("OggConvert")
        
        self._window.show_all()
    
                  
    def _on_go(self, button):
        self._outfile_folder = self._save_folder_button.get_current_folder()
        self._outfile_name = self._outfile_entry.get_text()
        self._outfile = os.path.join(self._outfile_folder, self._outfile_name)
        allgood = True
        # Check destination is writable
        if not os.access(self._outfile_folder, os.W_OK):
            dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                                gtk.MESSAGE_ERROR,
                                gtk.BUTTONS_CLOSE,
                                _("Folder is not writable"))
            dialogue.format_secondary_text(_("Cannot save to this folder"))
            dialogue.run()
            dialogue.destroy()            
            allgood = False
        
        # Now check whether the file already exists
        if (os.path.exists(self._outfile) & allgood):        
            if os.path.samefile(self._outfile, self._input_file):
                dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_ERROR,
                                    gtk.BUTTONS_CLOSE,
                                    _("Using the same file for input and output"))
                dialogue.format_secondary_text(_("Choose a different name for the save file, or save to a different location."))
                dialogue.run()
                dialogue.destroy()            
                allgood = False      
            else: 
                if not confirm_overwrite(self._outfile, self._window):
                    allgood = False
              
        
        # If Dirac is selected, flash up a warning to show it's experimental
        format = ocv_constants.FORMATS[int(self._format_combobox.get_active())]
        if format == "SCHRO":
            if not dirac_warning(self._window):
                allgood = False

        # Get file format choosed.
        container = ocv_constants.CONTAINER_FORMATS[int(
            self._container_combobox.get_active())]

        # Now if we're still good to go...        
        if allgood:
            #self._window.hide()
            vquality = self._video_quality_slider.get_value()
            aquality = self._audio_quality_slider.get_value()
            tc = Transcoder(
                self._input_file, self._outfile, format, vquality, aquality,
                container)
            pr = ProgressReport(tc, self._input_file, self._outfile)
            self._window.hide()
            pr.run()
            self._window.show()

    def _on_quit(self, *args ):
        print _("Bye then!")
        gtk.main_quit()

    def _on_file_changed(self, filechooser):
        ## This function is a mess. Really needs cleaning up.
        self._input_file = filechooser.get_filename()
        if self._input_file == None:
            self._go_button.set_sensitive(False)
        else:
            mc = MediaChecker(self._input_file)
            mc.run()
            if mc.is_media:
                self._input_has_video = mc.is_video
                self._on_container_changed(self._container_combobox)
                self._go_button.set_sensitive(True)
            else:
                # What about auto codec installation?
                self._go_button.set_sensitive(False)  
                dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                             gtk.MESSAGE_ERROR,
                             gtk.BUTTONS_CLOSE,
                             _("The file \"%s\" cannot be converted") %os.path.basename(self._input_file))
                dialogue.format_secondary_text(_("The file format \"%s\" is not supported." %mc.mimetype))
                dialogue.run()
                dialogue.destroy()
                filechooser.unselect_all()

        folder = filechooser.get_current_folder()
        if os.access(folder,os.W_OK):
            self._outfile_folder = filechooser.get_current_folder()
        else:
            self._outfile_folder = os.path.expanduser('~')
        self._save_folder_button.set_current_folder(self._outfile_folder)

    def _on_container_changed(self, combobox):
        container = ocv_constants.CONTAINER_FORMATS[int(combobox.get_active())]
        if container == 'OGG':
            new_ext = 'ogg'
        elif container == 'MATROSKA':
            if (ocv_constants.FORMATS[
                int(self._format_combobox.get_active())] == 'SCHRO'):
                # DIRAC format selected. It cannot be stored in Matroska
                # container, warn the user and change the format to Theora.
                dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, _(
                    'Dirac video format cannot be stored in Matroska'
                    ' container, Theora video format will be used instead.'))
                dialogue.run()
                dialogue.destroy()
                self._format_combobox.set_active(
                    ocv_constants.FORMATS.index('THEORA'))

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
        elif self._input_file:
            # Get basename from the source file
            basename, ext = os.path.splitext(
                os.path.basename(self._input_file))
        else:
            # Nothing to do, no file is yet selected.
            return

        self._outfile_name = '%s.%s' % (basename, new_ext)
        self._outfile_entry.set_text(self._outfile_name)

    def _on_format_changed(self, combobox):
        if (ocv_constants.FORMATS[int(combobox.get_active())] == 'SCHRO'):
            # DIRAC format selected. It cannot be stored in Matroska
            # container, warn the user and change container to Ogg.
            if (ocv_constants.CONTAINER_FORMATS[
                int(self._container_combobox.get_active())] == 'MATROSKA'):
                dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, _(
                    'Dirac video format cannot be stored in Matroska'
                    ' container, Ogg container will be used instead.'))
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
        audio = gtk.FileFilter()
        audio.set_name(_("Audio Files"))
        audio.add_mime_type("audio/*")
        allmedia = gtk.FileFilter()
        allmedia.set_name(_("All Media Files"))
        allmedia.add_mime_type("video/*")
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


class ProgressReport:
    def __init__(self, transcoder, infile, outfile):
    
        self._infile = infile
        self._infile_name = os.path.basename(infile)
        self._outfile = outfile
        self._outfile_name = os.path.basename(outfile)
        self._transcoder = transcoder
    
        # This is a bit hacky -- we should just be able to connect to the 
        # Transcoder class itself instead
        self._transcoder.bus.connect("message::eos",self._on_eos)
    
        gladepath = os.path.dirname(os.path.abspath(__file__))
        gladepath = os.path.join(gladepath, "oggcv.glade")
        self._wtree = gtk.glade.XML(gladepath, "progress_window")
        
        signals = {"on_pause_button_clicked" : self._on_pause,
                   "on_cancel_button_clicked" : self._on_cancel,
                   "on_progress_window_delete" : self._on_cancel}
                   
        self._wtree.signal_autoconnect(signals)
        
        self._window = self._wtree.get_widget("progress_window")
        self._progressbar = self._wtree.get_widget("progressbar")
        self._buttonbox = self._wtree.get_widget("buttonbox")
        self._pause_button = self._wtree.get_widget("pause_button")
        self._label = self._wtree.get_widget("convert_label")
        
        self._label.set_markup(_("<i>Converting \"%s\"</i>") %self._infile_name)
     
        self._old_pos = 0
        self._show_stall_warning = True
     
     
    def run(self):
        self._transcoder.pause()
        if not self._transcoder.sync():
            self._preroll_failed()
            return
        self._duration = self._transcoder.get_duration()
        self._window.show_all()
        self._transcoder.play()
        self._playing = True
        self._timer = 0.0
        if self._duration == None:
            gobject.timeout_add(100, self._pulse_progressbar)
        else: 
            self._duration = float(self._duration) # Otherwise we do integer div
            gobject.timeout_add(1000, self._update_progressbar)
        gtk.main()
        
    
    
    def _update_progressbar(self):
        pos = self._transcoder.get_position()
        
        # Check the new position against the old to see whether the encoder
        # has stalled. This often occurs when the EOS message doesn't get fired
        # for some reason.
        if pos <= self._old_pos:
            if (self._show_stall_warning and self._playing):
                stall_warning(self._window)
                self._show_stall_warning = False #Only display stall warning once
                
        self._old_pos = pos
        completed = pos/self._duration
        percent = 100*completed
    
        if self._playing:
            self._timer += 1
            timerem = timeremaining(self._timer, percent)
            self._progressbar.set_fraction(completed)
            self._progressbar.set_text(
                    _("%.1f%% completed, about %s left") %(percent, timerem))
            return True
        else: 
            self._progressbar.set_text(_('Paused (%.1f%% completed)') %(percent))
            return False
        
    def _pulse_progressbar(self):
        if self._playing:
            self._progressbar.pulse()
            return True
        else:
            self._progressbar.set_text(_("Paused"))
            return False
        
    def _on_pause(self, button):
        
        if self._playing:
            self._transcoder.pause()
            self._playing = False
            self._pause_button.set_label(_("_Resume"))
        else:
            self._transcoder.play()
            #self._playing = True
            if self._duration==None:
                gobject.timeout_add(100, self._pulse_progressbar)
                self._progressbar.set_text("")
                self._pulse_progressbar()
            else:
                gobject.timeout_add(1000, self._update_progressbar)
                self._update_progressbar()
            self._playing = True
            self._pause_button.set_label(_("_Pause"))
            
                   
    def _on_cancel(self, *args):
        if cancel_check(self._window):
            self._playing = False
            self._transcoder.stop()
            self._window.destroy()
            gtk.main_quit()   
                    
                    
    def _on_eos(self, bus, message):
        self._transcoder.stop()
        self._playing = False
        gtk.main_quit()
        self._progressbar.set_text(_("Encoding complete"))
        self._progressbar.set_fraction(1.0)
        dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_INFO,
                                    gtk.BUTTONS_CLOSE, _("Encoding complete"))
        dialogue.format_secondary_text(_("File saved to \"%s\".") %(self._outfile))
        dialogue.run()
        dialogue.destroy()             
        self._window.destroy()
        
    def _preroll_failed(self):
        self._transcoder.stop()
        # I really ought to put all the dialogues in one place...
        dialogue = gtk.MessageDialog(self._window, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_ERROR,
                                    gtk.BUTTONS_CLOSE, _("Cannot convert file"))
        dialogue.format_secondary_text(_("GStreamer error: preroll failed"))
        dialogue.run()
        dialogue.destroy()
        
        
if __name__ == "__main__":
    gobject.threads_init()
    main = Main()
    gtk.main()
        
