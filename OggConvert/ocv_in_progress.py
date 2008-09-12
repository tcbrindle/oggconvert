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

import os
from time import time
import gobject
import gtk

from gettext import gettext as _

from ocv_util import timeremaining, hourminsec, confirm_overwrite, \
                        cancel_check


class ProgressWindow:
    def __init__(self, transcoder, infile, outfile):
    
        self._infile = infile
        self._infile_name = os.path.basename(infile)
        self._outfile = outfile
        self._outfile_name = os.path.basename(outfile)
        self._transcoder = transcoder
    
        # Connect to the transcoder's signals
        self._transcoder.connect("eos",self._on_eos)
        self._transcoder.connect("playing",self._on_playing)
        self._transcoder.connect("paused",self._on_paused)
    
        gladepath = os.path.dirname(os.path.abspath(__file__))
        gladepath = os.path.join(gladepath, "oggcv.glade")
        self._wtree = gtk.glade.XML(gladepath, "progress_window")
        
        signals = {"on_pause_button_clicked" : self._on_pause_clicked,
                   "on_cancel_button_clicked" : self._on_cancel_clicked,
                   "on_progress_window_delete" : self._on_cancel_clicked}
                   
        self._wtree.signal_autoconnect(signals)
        
        self._window = self._wtree.get_widget("progress_window")
        self._progressbar = self._wtree.get_widget("progressbar")
        self._buttonbox = self._wtree.get_widget("buttonbox")
        self._pause_button = self._wtree.get_widget("pause_button")
        self._label = self._wtree.get_widget("convert_label")
        
        self._label.set_markup(_("<i>Converting \"%s\"</i>") %self._infile_name)
     
     
    def run(self):
        self._transcoder.pause()
        if not self._transcoder.sync():
            self._preroll_failed()
            return
        self._duration = self._transcoder.get_duration()
        self._window.show_all()
        self._transcoder.play()
        self._timer = Timer()
        gtk.main()
        
    def _on_paused(self, unused):
        self._timer.stop()
        self._playing = False
        self._pause_button.set_label(_("_Resume"))
        
    def _on_playing(self, unused):
        self._playing = True
        if self._duration==None:
            self._progressbar.set_text("")
            gobject.timeout_add(100, self._pulse_progressbar)
        else:
            self._update_progressbar()
            gobject.timeout_add(1000, self._update_progressbar)
        self._pause_button.set_label(_("_Pause"))
        self._timer.start()
            
    def _update_progressbar(self):
        pos = self._transcoder.get_position()
        self._duration = self._transcoder.get_duration()
        if pos:
            completed = float(pos)/self._duration
        else:
            completed = 1
        percent = 100*completed
        elapsed = self._timer.get_elapsed()
    
        if self._playing:
            timerem = timeremaining(elapsed, percent)
            if elapsed>3.0: # Don't display any text for the first three seconds
                self._progressbar.set_fraction(completed)
                self._progressbar.set_text(
                    _("%.1f%% completed, about %sleft") %(percent, timerem))
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
        
    def _on_pause_clicked(self, button):        
        if self._playing:
            self._transcoder.pause()           
        else:
            self._transcoder.play()
                   
    def _on_cancel_clicked(self, *args):
        if cancel_check(self._window):
            self._playing = False
            self._transcoder.stop()
            self._window.destroy()
            gtk.main_quit()   
                    
                    
    def _on_eos(self, unused):
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
 
class Timer:
    def __init__(self):
        self._elapsed  = 0.0
        self._starttime = time()
        self._started = False
        
    def start(self):
        self._starttime = time()
        self._started = True
        
    def stop(self):
        self._elapsed += (time() - self._starttime)
        self._started = False
     
    def get_elapsed(self):
        if self._started:
            return (self._elapsed + time() - self._starttime)
        else:
            return self._elapsed
            
    def reset(self):
        self._elapsed = 0.0
