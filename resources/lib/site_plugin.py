from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.config import cConfig


class SitePlugin(object):
    site_identifier = ''
    site_name = ''
    site_icon = None

    def __init__(self):
        self.params = ParameterHandler()
        self.gui = cGui()

    def load(self):
        raise NotImplementedError

    def _search(self, gui, search_term):
        return None

    def get_func(self, func_name):
        if hasattr(self, func_name):
            return getattr(self, func_name)
        return None

    @classmethod
    def _is_enabled(cls):
        return cConfig().getSetting('plugin_%s' % cls().site_identifier) == 'true'

    def _create_gui_element(self, title = '', func_name = None, site = None):
        if not site:
            site = self.site_identifier

        return cGuiElement(title, site, func_name)