#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    bl-exit: Bunsenlabs exit dialog, offering various exit options
#     via both GUI and CLI
#    Copyright (C) 2012 Philip Newborough  <corenominal@corenominal.org>
#    Copyright (C) 2016 xaos52  <xaos52@gmail.com>
#    Copyright (C) 2017 damo  <damo@bunsenlabs.org>
#    Copyright (C) 2018 tknomanzr <webradley9929@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import pygtk
import gtk
import pango
import os
import logging
from custom_button import ColoredImageButton
from time import sleep
import dbus_interface
import default_theme
import validator
pygtk.require('2.0')

exit_log = logging.getLogger('Bunsen-Exit-Log')


class Gui:
    """
    This class creates a gtk based exit dialog. If no config files can be found
    whatsoever, a default gtk dialog will be created. However, if a config file
    can be found, a dialog will be created using that config file.
    If the theme file specified in the config file cannot be found, a default theme
    will be used.
    Individual elements will be handled on a per case basis.
    """
    # get a DBusInterface instance, so we can send message out.
    exit_bus = dbus_interface.DbusInterface()

    def key_press_event(self, widget, event):
        """
        Keypress event used to capture keyboard shortcuts
        :param widget: the widget
        :param event: the event
        :return:
        """
        keyval = event.keyval
        keyval_name = gtk.gdk.keyval_name(keyval)
        state = event.state
        alt = (state & gtk.gdk.MOD1_MASK)
        # Cancel shortcut
        if alt and keyval_name == 'l':
            self.send_to_dbus('Logout')
        # Suspend shortcut
        elif alt and keyval_name == 's':
            self.send_to_dbus('Suspend')
        # Reboot Shortcut
        elif alt and keyval_name == 'b':
            self.send_to_dbus('Reboot')
        # Poweroff shortcut
        elif alt and keyval_name == 'p':
            self.send_to_dbus('PowerOff')
        # Hibernate Shortcut
        elif alt and keyval_name == 'i':
            self.send_to_dbus('Hibernate')
        # Hybrid Sleep Shortcut
        elif alt and keyval_name == 'y':
            self.send_to_dbus('HybridSleep')
        # Cancel Shortcut
        elif keyval_name == 'Escape':
            self.destroy()
        elif keyval_name == 'Shift_L':
            self.show_labels = not self.show_labels
            if self.show_labels:
                self.dialog_height = self.dialog_height + int(self.label_height)
                self.button_height = self.button_height + int(self.label_height)
                self.button_box.destroy()
                self.window.set_size_request(self.dialog_width, int(self.dialog_height))
            else:
                self.dialog_height = self.dialog_height - int(self.label_height)
                self.button_height = self.button_height - int(self.label_height)
                self.button_box.destroy()
                self.window.set_size_request(self.dialog_width, int(self.dialog_height))
            self.create_button_box()
            self.create_buttons_from_list()
            self.window.add(self.button_box)
            self.window.show_all()
        else:
            return False
        return True

    def destroy(self, widget=None, event=None, data=None):
        """
        Destroys the window and all contained widgets
        Args:
        widget: optional
        event: optional
        data: optional
        """
        self.window.hide_all()
        gtk.main_quit()

    def __init__(self, button_values, exit_bus, theme, theme_entries):
        """

        Args:
        button_values: the list of buttons to create
        exit_bus: the dbs interface to send messages to
        theme: the specified theme
        theme_entries: the dictionary of theme entries for the specified theme.

        Returns:

        """
        # Attributes
        self.show_labels = False
        self.button_values = button_values
        self.exit_bus = exit_bus
        self.default = default_theme.DefaultTheme()
        self.entry_validator = validator.Validator()
        if not theme['name'] == "default":
            self.theme = theme['name']
            self.theme_entries = theme_entries
            # Sanitize input from config file and set to defaults if input is bad.
            key = "dialog_height"
            self.dialog_height = self.entry_validator.parse_int(key, self.theme_entries[key])
            key = "button_height"
            self.button_height = self.entry_validator.parse_int(key, self.theme_entries[key])
            key = "button_spacing"
            self.button_spacing = self.entry_validator.parse_int(key, self.theme_entries[key])
            key = "inner_border"
            self.inner_border = self.entry_validator.parse_int(key, self.theme_entries[key])
            key = "window_width_adjustment"
            self.width_adjustment = self.entry_validator.parse_float(key, self.theme_entries[key])
            key = "overall_opacity"
            self.overall_opacity = self.entry_validator.parse_int(key, self.theme_entries[key])
            key = "sleep_delay"
            self.sleep_delay = self.entry_validator.parse_float(key, self.theme_entries[key])
            key = "label_height"
            self.label_height = self.entry_validator.parse_int(key, self.theme_entries[key])
            key = "window_background_normal"
            self.window_background_normal = self.entry_validator.parse_color(key, self.theme_entries[key])
            key = "tooltip_background"
            self.tooltip_background = self.entry_validator.parse_color(key, self.theme_entries[key])
            key = "tooltip_foreground"
            self.tooltip_foreground = self.entry_validator.parse_color(key, self.theme_entries[key])
            # Other instance variables
            self.dialog_width = 0
            self.button_box = None
            self.window = None
        if theme['name'] == "default":
            # There is no config file to be found at all, so create a default
            # gtk window using button_values that shows buttons with labels
            # using the default gtk theme.
            # This will allow me to set some sane defaults for theme entries
            # later on without messing with the appearance of the most basic
            # default settings.
            self.create_default_window()
        else:
            self.create_custom_window()
        self.window.show_all()
        return

    def create_default_window(self):
        """
        Creates a gtk dialog using only the default gtk theme.
        This dialog is only used when a config file cannot be found.
        Hibernate and HybridSleep buttons are hidden by default in this scheme.
        Returns:

        """
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_name("Bunsen Exit")
        self.window.set_decorated(False)
        self.window.connect("delete_event", self.destroy)
        self.window.connect("destroy_event", self.destroy)
        self.window.connect("key-press-event", self.key_press_event)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.stick()
        self.window.set_position(gtk.WIN_POS_CENTER)
        window_icon = self.window.render_icon(gtk.STOCK_QUIT, gtk.ICON_SIZE_DIALOG)
        self.window.set_icon(window_icon)
        self.button_box = gtk.HButtonBox()
        self.button_box.set_layout(gtk.BUTTONBOX_SPREAD)
        for key, value in self.button_values.iteritems():
            # Format the keys into dbus actions
            if key == 'cancel':
                key = 'Cancel'
            elif key == 'logout':
                key = 'Logout'
            elif key == 'suspend':
                key = 'Suspend'
            elif key == 'poweroff':
                key = 'PowerOff'
            elif key == 'reboot':
                key = 'Reboot'
            elif key == 'hibernate':
                key = 'Hibernate'
            elif key == 'hybridsleep':
                key = 'HybridSleep'
            # only add buttons that are to be shown
            if value == 'show':
                exit_log.info('Creating button for ' + key)
                button = gtk.Button()
                button.set_name(key)
                button.set_relief(gtk.RELIEF_NONE)
                button.set_label(key)
                button.connect("clicked", self.clicked)
                self.button_box.pack_start(button, True, True, 0)
        self.window.add(self.button_box)
        self.window.show_all()
        return

    def create_custom_window(self):

        """
        This method creates a custom window using the theme specified in
        ~/.config/bunsen-exit/bl-exitrc. If that theme cannot be found
        a default theme will be used instead.
        """
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        # Get the screen width under the cursor
        screen_width = 800  # fallback width
        try:
            display = gtk.gdk.Display(gtk.gdk.get_display())
            screen, x, y, flags = display.get_pointer()
            curmon = screen.get_monitor_at_point(x, y)
            _, _, screen_width, _ = screen.get_monitor_geometry(curmon)
        except:
            exit_log.info('Error constructing UI. Not running under X')
        finally:
            del x, y, display, screen, curmon
        exit_log.debug("Detected screen_width is " + str(screen_width))
        if self.width_adjustment > 0:
            self.dialog_width = int(screen_width * self.width_adjustment)
        if self.dialog_width > screen_width:
            self.dialog_width = screen_width
        exit_log.debug("Dialog width is set to " + str(self.dialog_width))
        exit_log.debug("Dialog Height is set to" + str(self.dialog_height))
        # Format the window.
        self.window.set_name('Bunsen Exit')
        self.window.set_decorated(False)
        self.window.connect("delete_event", self.destroy)
        self.window.connect("destroy_event", self.destroy)
        self.window.connect("key-press-event", self.key_press_event)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.stick()
        self.window.set_position(gtk.WIN_POS_CENTER)
        window_icon = self.window.render_icon(gtk.STOCK_QUIT, gtk.ICON_SIZE_DIALOG)
        self.window.set_icon(window_icon)
        self.window.modify_bg(gtk.STATE_NORMAL, self.window_background_normal)
        self.create_button_box()
        self.create_buttons_from_list()
        self.window.set_size_request(self.dialog_width, self.dialog_height)
        self.window.add(self.button_box)
        self.window.set_opacity(0)
        self.window.show_all()
        for i in range(1, self.overall_opacity):
            sleep(self.sleep_delay)
            while gtk.events_pending():
                gtk.main_iteration(False)
                self.window.set_opacity(float(i)/100.0)

    def main(self):
        """
        Passes control to the gtk.main() loop
        """
        gtk.main()

    def create_button_box(self):
        """
        Creates a horizontal box packed with custom buttons.
        Returns:

        """
        self.button_box = gtk.HButtonBox()
        self.button_box.set_layout(gtk.BUTTONBOX_SPREAD)
        self.button_box.set_size_request(self.dialog_width - self.inner_border, self.dialog_height - self.inner_border)
        self.button_box.set_spacing(self.button_spacing)
        return

    def create_buttons_from_list(self):
        """
        Creates the custom buttons from the list of button_values
        Returns:

        """
        num_buttons = 0
        for key, value in self.button_values.iteritems():
            if value == "show":
                num_buttons += 1
        # Now build the array of buttons
        for key, value in self.button_values.iteritems():
            # Format the keys into dbus actions
            if key == 'cancel':
                key = 'Cancel'
            elif key == 'logout':
                key = 'Logout'
            elif key == 'suspend':
                key = 'Suspend'
            elif key == 'poweroff':
                key = 'PowerOff'
            elif key == 'reboot':
                key = 'Reboot'
            elif key == 'hibernate':
                key = 'Hibernate'
            elif key == 'hybridsleep':
                key = 'HybridSleep'
            # only add buttons that are to be shown
            if value == 'show':
                exit_log.debug('Creating button for ' + key)
                self.add_buttons(key, num_buttons)
        return

    def query_tooltip_custom_cb(self, widget, x, y, keyboard_tip, tooltip, key, tooltip_label, tooltip_window):
        """
        Creates custom tooltips using tooltip_foreground and tooltip_background
        theme entries to specify the background for the tooltip window and the tooltip
        text color.
        Args:
        widget:
        x:
        y:
        keyboard_tip:
        tooltip:
        key:
        tooltip_label:
        tooltip_window:

        Returns: True - I don't know why.

        """
        tooltip_font = self.theme_entries['tooltip_font_family']
        tooltip_font += " "
        tooltip_font += self.theme_entries['tooltip_font_style']
        tooltip_font += " "
        tooltip_font += self.theme_entries['tooltip_font_size']
        tooltip_label.modify_font(pango.FontDescription(tooltip_font))
        tooltip_label.set_markup(key)
        tooltip_label.show()
        return True

    def add_buttons(self, key, num_buttons):
        """
        This class creates the custom buttons
         Args:
         key: the key to be used as a button label.
        num_buttons: the number of buttons to create

        Returns:

        """
        icon_path = self.theme_entries['icon_path']
        image_key = 'button_image_' + key.lower()
        button_image = icon_path + "/" + self.theme_entries[image_key]
        if os.path.exists(button_image):
            exit_log.debug("Loading theme entry " + key + " from " + button_image)
            self.color_button = ColoredImageButton(key, button_image,
                                                   self.theme_entries, num_buttons,
                                                   self.dialog_width, self.show_labels)
            self.color_button.set_name(key)
            self.button_box.pack_start(self.color_button, False, False, self.button_spacing)
        else:
            exit_log.warn("Path does not exist for " + button_image + ".")
            button_image = gtk.STOCK_DIALOG_ERROR
            self.color_button = ColoredImageButton(key, button_image,
                                                   self.theme_entries, num_buttons,
                                                   self.dialog_width, self.show_labels)
            self.color_button.set_name(key)
            self.button_box.pack_start(self.color_button, False, False, self.button_spacing)
        # Add custom tooltips
        tooltip_window = gtk.Window(gtk.WINDOW_POPUP)
        tooltip_label = gtk.Label()
        tooltip_label.set_use_markup(True)
        tooltip_window.modify_bg(gtk.STATE_NORMAL, self.tooltip_background)
        tooltip_label.modify_fg(gtk.STATE_NORMAL, self.tooltip_foreground)
        self.color_button.connect("query-tooltip", self.query_tooltip_custom_cb, key, tooltip_label, tooltip_window)
        self.color_button.set_tooltip_window(tooltip_window)
        tooltip_window.add(tooltip_label)
        # Show the custom button
        self.button_box.show()
        self.color_button.show()
        return

    def configure(self, theme, theme_entries):
        """
        This is a superfluous method leftover from the previous fork. It should
        probably be removed as all it does at the moment is log the theme name and author
        for the specified theme. This is basically meta data
        Args:
        theme: the specified theme
        theme_entries: author and name entries are used.

        Returns:

        """
        if theme is not None or theme_entries is not None:
            msg = 'Loading theme \'' + theme_entries['name'] + ' by ' + theme_entries['author']
        else:
            msg = 'theme and theme_entries is set to None.'
        exit_log.info(msg)
        return

    def clicked(self, widget, data=None):
        """
        A button was clicked. This method is really here to support the defult gtk
        dialog as the custom buttons use their own event handling.
        Args:
        widget: the widget that was clicked
        data: optional

        Returns:

        """
        if widget.name == 'Cancel':
            self.destroy()
        else:
            self.send_to_dbus(widget.name)
        return

    def send_to_dbus(self, dbus_msg):
        """
        Once a button is pressed or keyboard shortcut is pressed, sends a properly
        formatted dbus message to the dbus interface.
        Args:
        dbus_msg: the message -- eg Poweroff.

        Returns:

        """
        exit_log.info("Executing action " + dbus_msg)
        if dbus_msg == 'Logout':
            self.exit_bus.logout()
        else:
            self.exit_bus.send_dbus(dbus_msg)
        return