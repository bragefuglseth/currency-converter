# convertion.py
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

import gi
from typing import Any, Dict, Union

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gio, Gtk
from ...components import CurrencySelector
from ...utils import CurrenciesListModel
from ...define import RES_PATH, CODES

resource = f"{RES_PATH}/pages/convertion/index.ui"

def convertion_page(application: Adw.Application, from_currency_value):
    builder = Gtk.Builder.new_from_resource(resource)
    settings = application.utils.settings
    convertion = application.utils.convertion
    page = builder.get_object("page")
    from_currency_selector: CurrencySelector = builder.get_object("from_currency_selector")
    to_currency_selector: CurrencySelector = builder.get_object("to_currency_selector")
    from_currency_entry = builder.get_object("from_currency_entry")
    to_currency_entry = builder.get_object("to_currency_entry")
    invert_currencies_button = builder.get_object("invert_currencies")
    stack = builder.get_object("stack")
    reload = builder.get_object("reload")
    toast_overlay = builder.get_object("toast_overlay")
    to_currency_value = 0

    def load_currencies(provider: int):
        codes = {currency: details for currency, details in CODES.items() if str(provider) in details['providers']}
        from_currency_model = CurrenciesListModel(currency_names_func)
        to_currency_model = CurrenciesListModel(currency_names_func)
        from_currency_selector.bind_models(from_currency_model)
        from_currency_model.set_currencies(codes)
        to_currency_selector.bind_models(to_currency_model)
        to_currency_model.set_currencies(codes)
        if not settings.get_string('src-currency') in codes or not settings.get_string('dest-currency') in codes:
            settings.set_string("src-currency", "USD")
            settings.set_string("dest-currency", "EUR")

        from_currency_selector.set_selected(settings.get_string('src-currency'))
        to_currency_selector.set_selected(settings.get_string('dest-currency'))

    def change_provider(settings, key):
        from_currency_selector.handler_block_by_func(currency_selectors_changed)
        load_currencies(settings.get_int(key))

    def invert_currencies():
        from_code = from_currency_selector.selected
        to_code = to_currency_selector.selected
        from_currency_selector.set_selected(to_code)
        to_currency_selector.set_selected(from_code)

    def is_loading():
        return stack.get_visible_child_name() == "loading"

    def currency_names_func(code):
        name = gettext(CODES.get(code, '')['name'])
        return name if name else None

    def valid_from_currency_value(value: str):
        if not value:
            return False
        try:
            f=float(value)
            return True
        except ValueError:
            return False

    def convert(value):
        if not is_loading() and valid_from_currency_value(value):
            def thread_cb(task: Gio.Task, self, task_data: object, cancellable: Gio.Cancellable):
                try:
                    convertion.convert(float(value), from_currency_selector.selected, to_currency_selector.selected, settings.get_int("providers"))
                    task.return_value(self.__converted_data)
                except Exception as e:
                    task.return_value(e)
            if convertion.converted_data["from"] != from_currency_selector.selected or convertion.converted_data["to"] != to_currency_selector.selected or not convertion.converted_data["converted"]:
                stack.set_visible_child_name("loading")
                task = Gio.Task.new(application, None, None, None)
                task.run_in_thread(thread_cb)
            else:
                convertion.convert(float(value), from_currency_selector.selected, to_currency_selector.selected, settings.get_int("providers"))

    def converted(data: Dict[str, Union[str, int]]):
        if not data["converted"]:
            stack.set_visible_child_name("convertion-error")
            toast_overlay.add_toast(Adw.Toast.new(
                title = _("Error converting, please try again."),
            ))
        else:
            stack.set_visible_child_name("result")
            to_currency_entry.set_text(str(data["amount"]))

    def currency_selectors_changed(_obj, _param):
        from_code = from_currency_selector.selected
        to_code = to_currency_selector.selected
        settings.set_string('src-currency', from_code)
        settings.set_string('dest-currency', to_code)
        if from_code != to_code:
            convert(from_currency_entry.get_text())

    load_currencies(settings.get_int("providers"))
    from_currency_entry.connect('changed', lambda entry: convert(entry.get_text()))
    from_currency_selector.connect('notify::selected', currency_selectors_changed)
    to_currency_selector.connect('notify::selected', currency_selectors_changed)
    invert_currencies_button.connect('clicked', lambda button: invert_currencies())
    reload.connect('clicked', lambda button: convert(from_currency_entry.get_text()))
    convertion.connect("converted", converted)
    settings.connect("changed::providers", change_provider)
    settings.connect("changed::high-precision", lambda settings, key: convert(from_currency_entry.get_text()))

    if from_currency_value:
        from_currency_entry.set_text(str(from_currency_value))
    else:
        from_currency_entry.set_text("1")

    return page
