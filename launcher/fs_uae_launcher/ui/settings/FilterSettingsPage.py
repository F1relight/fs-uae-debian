from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import fs_uae_launcher.fsui as fsui
from ...I18N import _, ngettext
from .OptionUI import OptionUI

class FilterSettingsPage(fsui.Panel):

    def __init__(self, parent):
        fsui.Panel.__init__(self, parent)
        self.layout = fsui.VerticalLayout()
        self.layout.padding_left = 10
        self.layout.padding_right = 10
        self.layout.padding_top = 10
        self.layout.padding_bottom = 20

        label = fsui.HeadingLabel(self, _("Scaling Options"))
        self.layout.add(label, margin=10, margin_bottom=20)

        def add_option(name):
            self.layout.add(OptionUI.create_group(self, name), fill=True,
                    margin=10)

        add_option("zoom")
        add_option("keep_aspect")

        label = fsui.HeadingLabel(self, _("Filters"))
        self.layout.add(label, margin=10, margin_top=20, margin_bottom=20)

        add_option("scanlines")
        add_option("rtg_scanlines")
        # FIXME: gamma
        # FIXME: brightness / contrast / saturation
