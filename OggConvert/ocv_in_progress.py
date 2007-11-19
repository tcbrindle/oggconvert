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
import gobject
import gtk

from gettext import gettext as _

from ocv_util import timeremaining, hourminsec, confirm_overwrite, \
                        stall_warning, cancel_check


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
        
