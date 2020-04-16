#  Copyright 2020 Jacob Shtabnoy <shtabnoyjacob@scps.net>
#  This source code file is available under the terms of the ISC License.
#  If the LICENSE file was not provided, you can find the full text of the license here:
#  https://opensource.org/licenses/ISC


class Plugin:
    def __init__(self):
        self.callbacks = {}

    def _add_callback(self, callback_id, func):
        self.callbacks[callback_id] = func

    def callback(self, callback_id):
        def inner(func):
            self._add_callback(callback_id, func)
            return func
        return inner
