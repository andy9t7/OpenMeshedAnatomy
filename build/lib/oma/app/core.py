
from trame.app import get_server
from trame.decorators import TrameApp, change, controller, life_cycle
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk
from oma.widgets import oma as my_widgets


# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------

@TrameApp()
class MyTrameApp:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")
        self.ui = self._build_ui()

        # Set state variable
        self.state.trame__title = "oma"

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    @life_cycle.server_reload
    def _build_ui(self, **kwargs):
        with SinglePageLayout(self.server) as layout:
            # Toolbar
            layout.title.set_text("Trame / vtk.js")
            with layout.toolbar:
                pass

            # Main content
            with layout.content:
                pass

            # Footer
            layout.footer.hide()

            return layout
