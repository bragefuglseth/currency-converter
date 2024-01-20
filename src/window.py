# window.py
#
# Copyright 2023 Ideve Core
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import gi, math

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
gi.require_version("Panel", "1")

from typing import Union, Any, Dict
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Panel
from .define import RES_PATH
from .pages import convertion_page
from .components import Shortcuts

resource = f"{RES_PATH}/window.ui"

def string_to_color(string: str):
    colors = {
        "light": Adw.ColorScheme.FORCE_LIGHT,
        "default": Adw.ColorScheme.DEFAULT,
        "dark": Adw.ColorScheme.FORCE_DARK,
    }
    return colors[string]

def create_main_window(application: Adw.Application, from_currency_value: int):
    builder = Gtk.Builder.new_from_resource(resource)
    settings = application.utils.settings
    convertion = application.utils.convertion
    window = builder.get_object("window")
    content = builder.get_object("content")
    menu_button = builder.get_object("menu_button")
    info = builder.get_object("info")
    disclaimer = builder.get_object("disclaimer")

    def set_color_scheme(color: str):
      Adw.StyleManager.get_default().set_color_scheme(string_to_color(color))

    def load_window_state():
        settings.bind(
            key="width",
            object=window,
            property="default-width",
            flags=Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            key="height",
            object=window,
            property="default-height",
            flags=Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            key="is-maximized",
            object=window,
            property="maximized",
            flags=Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            key="is-fullscreen",
            object=window,
            property="fullscreened",
            flags=Gio.SettingsBindFlags.DEFAULT,
        )
        settings.connect('changed::color-scheme', lambda setting, key: set_color_scheme(setting.get_string('color-scheme')));
        set_color_scheme(settings.get_string('color-scheme'))
        window.add_action(settings.create_action('color-scheme'))
        theme_selector_wg = Panel.ThemeSelector()
        theme_selector_wg.set_action_name('win.color-scheme')
        menu_button.props.popover.add_child(theme_selector_wg, 'theme')
        window.set_help_overlay(Shortcuts())

    def converted(data: Dict[str, Union[str, int]]):
        info.set_text(data["info"])
        disclaimer.set_visible(True)

    def load_convertion_page(from_currency_value: int = 0):
        content.set_child(convertion_page(application, from_currency_value))

    def open_uri(link: str):
        Gtk.show_uri(
          window,
          link,
          Gdk.CURRENT_TIME
        );

    load_window_state()
    disclaimer.connect('clicked', lambda button: open_uri(convertion.get_convertion()['disclaimer']))
    convertion.connect("converted", converted)
    load_convertion_page(from_currency_value)
    window.set_application(application)
    window.load_convertion_page = load_convertion_page
    return window
