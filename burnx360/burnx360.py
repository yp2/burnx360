#!/usr/bin/env python2.6
#-*- coding: utf-8 -*-

#       
#       Copyright 2009 Daniel Dereziński <daniel.derezinski@gmial.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import pygtk
pygtk.require("2.0")
import gtk
import os
import re
import gobject
import sys
import subprocess
import webbrowser
import ctypes
import locale
import gettext

__app__ = 'burnX360'
__version__ = '0.3'
__author__ = [u"Daniel 'yp2' Dereziński"]
__copyright__ = u"Copyright 2009,2011 Daniel 'yp2' Derezinski"

__opis__ = u"Program do nagrywania obrazów kopii zapasowych płyt dla Xbox360.\n\
            UŻYWASZ PROGRAMU NA WŁASNĄ ODPOWIEDZIALNOŚĆ ORAZ ZGODNIE Z PRAWEM.\n\
            PROGRAM SŁUŻY DO NAGRYWANIE KOPII ZAPASOWYCH PŁYT LEGALNIE ZAKUPIONYCH PRZEZ UŻYTKOWNIKA.\n\
            AUTOR NIE PONOSI ŻADNEJ ODPOWIEDZIALNOŚCI MATERIALNEJ ZA BŁĘDY PROGRAMU.\n\n\
            ZOSTAŁEŚ/ZOSTAŁAŚ OSTRZEŻONY/OSTRZEŻONA.\n\n\
            Więcje informacji znajdziesz w pliku README (/usr/share/doc/burnx360/README)."           

##Nazwa procesu
libc = ctypes.CDLL('libc.so.6')
libc.prctl(15, __app__+'\0', 0, 0, 0)

gui_file = os.path.expanduser('/usr/share/burnx360/gui.glade')
cfg_file = os.path.expanduser('~/.%s/%s.cfg' % (__app__, __app__))
ico_file = os.path.expanduser('/usr/share/burnx360/icon.png')

options = {}
d_options = {'dev_dvd': '/dev/sr0',
             'layer_break': '1913760',
             'xgd3_layer_break': '2086912',
             'xgd3_layer_break_lt_max': '2133520',
             'truncate_size': '8547991552',
             'burn_speed': '2',
             'buffer': '32',
             'last_used_dir': '~',
             'terminal': '1',
             'img_path': ''}
file_types = ['.iso', '.bin', '.000']

#ZMIENIĆ NA KATALOG INSTALCYJNY DLA PROGRAMU
burn_app_path ={'burn': os.path.expanduser('/usr/share/burnx360/burn.sh'),
                'xgd3_burn': os.path.expanduser('/usr/share/burnx360/xgd3_burn.sh'),
                'xgd3_burn_lt_max': os.path.expanduser('/usr/share/burnx360/xgd3_burn_lt_max.sh'), 
                'test_burn' : os.path.expanduser('/usr/share/burnx360/test_burn.sh')}
licence = os.path.expanduser('/usr/share/burnx360/LICENCE')


class Gui:
    def __init__(self):
        self.gui = gtk.Builder()
        self.gui.add_from_file(gui_file)
        self.obj = {}
        self.init_obj()
        self.init_settings()
        self.init_options()
        
        self.gui.connect_signals({'on_main_window_delete_event': self.quit,
                                  'on_main_window_destroy_event': self.quit,
                                  'on_main_window_destroy': self.quit,
                                  'on_rev_options_clicked': self.rev_options,
                                  'on_notebook1_switch_page': self.update_options,
                                  'on_save_opt_clicked': self.save_option_to_dict,
                                  'on_quit_clicked': self.quit,
                                  'on_filechooser_clicked': self.filechooser_dialog,
                                  'on_burn_clicked': self.choose_action,
                                  'on_xgd3_burn_clicked': self.choose_action,
                                  'on_xgd3_burn_lt_max_clicked': self.choose_action,
                                  'on_run_test_clicked': self.choose_action,
                                  'on_run_abgx360gui_clicked': self.run_abgx360_gui,
                                  'on_about_clicked': self.about_dialog})
        
        self.main_window = self.obj['main_window']
        self.main_window.set_title(__app__ +' '+ __version__)
        self.main_window.set_icon_from_file(ico_file)
        self.main_window.show()
    
    def init_obj(self):
        #utowrzenie listy objektów
        obj = self.gui.get_objects()
        for ele in obj:
            self.obj[gtk.Buildable.get_name(ele)] = ele
        
    def filechooser_dialog(self, w=None, d=None):
        dialog = gtk.FileChooserDialog("Otwórz...",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_icon_from_file(ico_file)
        if options['last_used_dir'] == '':
            dialog.set_current_folder(os.path.expanduser(d_options['last_used_dir']))
        else:
            dialog.set_current_folder(os.path.expanduser(options['last_used_dir']))
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_select_multiple(False)
        
        filter_file = gtk.FileFilter()
        filter_file.set_name('Obrazy (%s)' % str('\\'.join(file_types)))
        for ele in file_types:
            filter_file.add_pattern('*'+ele)
            
        filter_file.add_pattern('*.iso')
        filter_file.add_pattern('*.bin')
        filter_file.add_pattern('*.000')
        dialog.add_filter(filter_file)
        
        filter_file = gtk.FileFilter()
        filter_file.set_name('Wszystkie pliki')
        filter_file.add_pattern('*')
        dialog.add_filter(filter_file)
        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            options['img_path'] = dialog.get_filename()
            options['last_used_dir'] = os.path.split(dialog.get_filename())[0]
            self.obj['image_name'].set_text(os.path.split(dialog.get_filename())[1])
        elif response == gtk.RESPONSE_CANCEL:
            pass
        dialog.destroy()
        
    def init_settings(self):
        
        #ustawienia startowe oraz defincjie niektórych widgetów
        self.dev_dvd = self.obj['dev_dvd']
        
        #layer_break
        adj = gtk.Adjustment(lower=0, upper=99999999, step_incr=1, page_incr=10, page_size=10)
        self.layer_break = gtk.SpinButton()
        self.obj['table1'].attach(self.layer_break, left_attach=1, right_attach=2, top_attach=1, bottom_attach=2)
        self.layer_break.set_adjustment(adj)
        self.layer_break.show()
        
        #layer_break XGD3 bez LT-MAX
        adj = gtk.Adjustment(lower=0, upper=99999999, step_incr=1, page_incr=10, page_size=10)
        self.xgd3_layer_break = gtk.SpinButton()
        self.obj['table1'].attach(self.xgd3_layer_break, left_attach=1, right_attach=2, top_attach=2, bottom_attach=3)
        self.xgd3_layer_break.set_adjustment(adj)
        self.xgd3_layer_break.show()
        
        #layer_break XGD3 z LT-MAX
        adj = gtk.Adjustment(lower=0, upper=99999999, step_incr=1, page_incr=10, page_size=10)
        self.xgd3_layer_break_lt_max = gtk.SpinButton()
        self.obj['table1'].attach(self.xgd3_layer_break_lt_max, left_attach=1, right_attach=2, top_attach=3, bottom_attach=4)
        self.xgd3_layer_break_lt_max.set_adjustment(adj)
        self.xgd3_layer_break_lt_max.show()
        
        #rozmiar dla truncate dla XGD3 bez LT-MAX - przycięcie obrazu przed nagrywaniem
        adj = gtk.Adjustment(lower=0, upper=9999999999, step_incr=1, page_incr=10, page_size=10)
        self.truncate_size = gtk.SpinButton()
        self.obj['table1'].attach(self.truncate_size, left_attach=1, right_attach=2, top_attach=4, bottom_attach=5)
        self.truncate_size.set_adjustment(adj)
        self.truncate_size.show()
        
        #prędkość nagrywania
        self.burn_speeds = ['x1', 'x2', 'x4', 'x8']
        self._burn_speeds = ['1', '2', '4', '8']
        self.burn_speed = gtk.combo_box_new_text()
        self.burn_speed.show()
        self.obj['table1'].attach(self.burn_speed, left_attach=1, right_attach=2, top_attach=5, bottom_attach=6)
        for ele in self.burn_speeds:
            self.burn_speed.append_text(ele)
            
        #bufor dla growisofs
        adj = gtk.Adjustment(lower=0, upper=9999, step_incr=1, page_incr=10, page_size=10)
        self.buffer = gtk.SpinButton()
        self.obj['table1'].attach(self.buffer, left_attach=1, right_attach=2, top_attach=6, bottom_attach=7)
        self.buffer.set_adjustment(adj)
        self.buffer.show()
        
        #terminal
        self.terminals = ['xterm', 'gnome-terminal', 'terminator']
        self.terminal = gtk.combo_box_new_text()
        self.terminal.show()
        self.obj['table1'].attach(self.terminal, left_attach=1, right_attach=2, top_attach=7, bottom_attach=8)
        for ele in self.terminals:
            self.terminal.append_text(ele)
            
    def update_options(self, w=None, d=None, page_num=None):
        self.save_option_to_dict()

    def rev_options(self,w=None, d=None, d_1=None):
        options.update(d_options)
        self.set_options()
    
    def save_option_to_dict(self, w=None, d=None):
        options['dev_dvd'] = self.dev_dvd.get_text()
        options['layer_break'] = str(int(self.layer_break.get_value()))
        options['xgd3_layer_break'] = str(int(self.xgd3_layer_break.get_value()))
        options['xgd3_layer_break_lt_max'] = str(int(self.xgd3_layer_break_lt_max.get_value()))
        options['truncate_size'] =  str(int(self.truncate_size.get_value()))
        options['burn_speed'] = str(self.burn_speed.get_active())
        options['buffer'] =  str(int(self.buffer.get_value()))
        options['terminal'] = str(self.terminal.get_active())
        
    def init_options(self):
        if os.path.exists(cfg_file) == True:
            try:
                self.read_options()
                self.set_options()
            except:
                options.update(d_options)
                self.set_options()
                self.dialog_error("Nie można odczytać pliku z opcjami.\n Błąd wartości opcji.\
                                    \nUżywam domyślnych opcji.")
        else:
            #nie istnieje pliki konfiguracyjny domyślen opcje
            #kopia domyślnych opcji
            options.update(d_options)
            #ustawienie wartości opcji
            self.set_options()
    
    def set_options(self):
        self.dev_dvd.set_text(options.get('dev_dvd', d_options['dev_dvd']))
        self.layer_break.set_value(int(options.get('layer_break', d_options['layer_break'])))
        self.xgd3_layer_break.set_value(int(options.get('xgd3_layer_break', d_options['xgd3_layer_break'])))
        self.xgd3_layer_break_lt_max.set_value(int(options.get('xgd3_layer_break_lt_max', d_options['xgd3_layer_break_lt_max'])))
        self.truncate_size.set_value(int(options.get('truncate_size', d_options['truncate_size'])))
        self.burn_speed.set_active(int(options.get('burn_speed', d_options['burn_speed'])))
        self.buffer.set_value(int(options.get('buffer', d_options['buffer'])))
        self.terminal.set_active(int(options.get('terminal', d_options['terminal'])))
    
    def dialog_error(self, mes):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, mes)
        dialog.set_property('skip-taskbar-hint', True)
        dialog.set_icon_from_file(ico_file)
        res = dialog.run()
        if res == gtk.RESPONSE_OK:
            dialog.destroy()
        else:
            dialog.destroy()
        
    def save_options(self):
        _cfg_file = os.path.expanduser(cfg_file)
        if os.path.exists(_cfg_file) == True:
            self.write_options()
        else:
            #plik nie istnieje sprawdzamy czy istneje katalog
            if os.path.exists(os.path.split(_cfg_file)[0]) == False:
                #katalog nie istnieje tworzymy go
                try:
                    os.mkdir(os.path.split(_cfg_file)[0])
                except:
                    self.dialog_error(u"Nie można utowrzyć katalogu,\nopcje nie zostaną zapisane.")
                
                #zapisujemy opcje
                self.write_options()
            else:
                self.write_options()
                
    def write_options(self): 
        try:
            _cfg_file = os.path.expanduser(cfg_file)            
            f = open(_cfg_file, 'w')
            for k,v in options.iteritems():
                if k == 'img_path':
                    line = '%s=%s\n' % (k,'')
                    f.write(line)
                else:
                    line = '%s=%s\n' % (k,v)
                    f.write(line)
        except:
            self.dialog_error("Nie można zapsiać pliku z opcjami.")
            sys.exit(2)
            
    def read_options(self):
        try:
            _cfg_file = os.path.expanduser(cfg_file)
            opt = open(_cfg_file, 'r').readlines()
            opt = [ele.strip('\n') for ele in opt]
            for ele in opt:
                k,v = ele.split('=')
                options[k] = v
        except:
            options.update(d_options)
            self.dialog_error("Nie można odczytać pliku z opcjami.\
                                \nUżywam domyślnych ustawień.")
    
    def choose_action(self, w, d=None):
        path = self.check_path()
        if path is True:
            self.action(self.get_w_name(w))
        else:
            print 'False'
    
    def get_w_name(self, widget):
        # obejście problemu nazwy widgetu, widget.get_name() nie działa
        # działa gtk.Buildable.get_name(widget)
        return gtk.Buildable.get_name(widget)
    
    def action(self, act):
        if act == 'run_test':
            #uruchom test
            self.app(burn_app_path['test_burn'])
        elif act == 'burn':
            #uruchom nagrywanie xgd2
            self.app(burn_app_path['burn'])
        elif act == 'xgd3_burn':
            #uruchom nagrywanie xgd3
            self.app(burn_app_path['xgd3_burn'], 'xgd3')
        elif act == 'xgd3_burn_lt_max':
            #uruchom nagrywanie xgd3 z lt_max
            self.app(burn_app_path['xgd3_burn_lt_max'], 'xgd3_lt_max')
        else:
            self.dialog_error('Błąd. Nie wiem co robić.\nBłąd raczej krytyczny :(')

    def app(self, app, iso_format='xgd2'):
        
        #wspólne opcje dla różnych formatów zapisu iso
        terminal = self.terminals[int(options['terminal'])]
        burn_speed = self._burn_speeds[int(options['burn_speed'])]
        img_path = '%s' % options['img_path']
        dev_dvd = options['dev_dvd']
        buffer = options['buffer']
        
        #wybór formatu zapisu
        if iso_format == 'xgd2':
            # xgd2
            layer_break = options['layer_break']
            
            #argumenty xgd2
            args = [app, layer_break, buffer, burn_speed, dev_dvd, img_path]
            
        elif iso_format == 'xgd3':
            # xgd3
            layer_break = options['xgd3_layer_break']
            truncate_size = options['truncate_size']
            
            #przycięcie samego iso przy pomocy truncate
            
            #argumenty xgd3
            args = [app, truncate_size, layer_break, buffer, burn_speed, dev_dvd, img_path]
        
        elif iso_format == 'xgd3_lt_max':
            layer_break = options['xgd3_layer_break_lt_max']
            #argumenty xgd3 z lt-max
            args = [app, layer_break, buffer, burn_speed, dev_dvd, img_path]
            
        #utowrzenie komendy nadgrywania.
        args = ' '.join(args)

        #uruchomienie terminala z procesem growisofs
        if terminal == 'xterm':
            subprocess.Popen([terminal, '-bg', 'black', '-fg', 'white', '-e', args])
        else:
            subprocess.Popen([terminal, '-e', args])
    
    def check_path(self):
        if options['img_path'] == '':
            self.dialog_error('Brak ścieżki do pliku z obrazem płyty.\
                                \nWybierz obraz...')
            return False
        else:
            if os.path.splitext(options['img_path'])[1] in file_types:
                return True
            else:
                self.dialog_error('Nie obsługiwany format pliku')
                return False

    def run_abgx360_gui(self, w=None, d=None):
        app = 'abgx360gui'
        subprocess.Popen([app])
    
    def about_dialog(self, w=None, d=None):
        li = ''.join(open(licence, 'r').readlines())
        dialog = gtk.AboutDialog()
        dialog.set_name(__app__)
        dialog.set_version(__version__)
        dialog.set_license(li)
        dialog.set_icon_from_file(ico_file)
#        dialog.set_website(__website__)
#        dialog.set_website_label("Strona projektu")
        dialog.set_comments(__opis__)
        dialog.set_authors(__author__)
        dialog.set_copyright(__copyright__)
        
        response = dialog.run()
        if response == gtk.RESPONSE_CLOSE:
            dialog.destroy()
        else:
            dialog.destroy()
    
    def quit(self, w=None, d=None):
        gtk.main_quit()
        self.save_options()
        
    def main(self):
        gtk.main()
        
#hadler dla linków http dla gtk.AboutDialog
#def url_handler(dialog, link, data=None):
#    webbrowser.open(link)
#
#gtk.about_dialog_set_url_hook(url_handler)

if __name__ == "__main__":
    gui=Gui()
    gui.main()
