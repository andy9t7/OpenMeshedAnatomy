import os
from trame.app import get_server
from trame.decorators import TrameApp, change, controller, life_cycle
from .ui import build_ui
from .visualization import VtkViewer

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------

@TrameApp()
class MyTrameApp:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")

        state, ctrl =  self.server.state,  self.server.controller

        # Set state variable
        self.state.trame__title = "Open Meshed Anatomy"

        state.active_actor = "HeadMesh"
        state.mesh_representation = 2
        state.mesh_color_preset = 0
        state.mesh_color_array_idx = 0
        state.mesh_opacity = 1.0

        state.active_labels = []

        self.atlas_label_file = os.path.join(CURRENT_DIRECTORY, "../data/atlas_with_skullscalp.ctbl")
        state.atlas_label = self.parse_file(self.atlas_label_file)
        self.material_label_file = os.path.join(CURRENT_DIRECTORY, "../data/material_with_skullscalp.ctbl")
        state.material_label = self.parse_file(self.material_label_file)

        state.selected_labels = []

        self._viz = VtkViewer(self)

        ctrl.getRenderWindow = self._viz.getRenderWindow
        ctrl.add_label = self._viz.add
        ctrl.remove_label = self._viz.remove
        ctrl.remove_all_labels = self._viz.remove_all
        ctrl.set_opacity = self._viz.set_opacity
        ctrl.set_representation = self._viz.set_representation
        ctrl.get_representation = self._viz.get_representation
        ctrl.extract_selection = self._viz.extract_selection
        ctrl.color_by_array = self._viz.color_by_array
        ctrl.use_preset = self._viz.use_preset

        ctrl.get_actor_list = self._viz.get_list

        state.dataset_arrays = [{'title': 'AtlasLabels', 'value': 0}, {'title': 'MaterialLabels', 'value': 1}]

        inititalize(self.server)
        self.ui = self._build_ui()

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller
    
    def parse_file(self, filepath):
        dict_list = []
        with open(filepath, 'r') as file:
            lines = file.readlines()
            for line in lines:
                split_line = line.split()
                title = split_line[1]
                value = int(split_line[0])
                rgb = [int(split_line[i]) for i in range(2, 5)]
                dict_list.append({"title": title, "value": value, "rgb": rgb})
        return dict_list
    
    @life_cycle.server_reload
    def _build_ui(self, **kwargs):
        return build_ui(self.server, **kwargs)

def inititalize(server):
    state, ctrl =  server.state,  server.controller

    @state.change("mesh_representation")
    def update_representation(mesh_representation, **kwargs):
        ctrl.set_representation(state.active_actor, mesh_representation)
        ctrl.view_update()

    @state.change("active_actor")
    def update_active_actor(active_actor, **kwargs):
        # update current_representation
        state.current_representation = ctrl.get_representation(active_actor)
        ctrl.view_update()    
    
    @state.change("mesh_opacity")
    def update_opacity(mesh_opacity, **kwargs):
        dirty = ctrl.set_opacity(state.active_actor, mesh_opacity)
        if dirty:
            ctrl.view_update()

    @ctrl.trigger("query_selection")
    def query_selection():
        ctrl.remove_all_labels()
        for label in state.selected_labels:
            extracted = ctrl.extract_selection(state.active_actor, label)
            ctrl.add_label(label.get("title"), extracted)
        state.mesh_opacity = 0.05
        ctrl.view_update()

    @ctrl.trigger("clear_selection")
    def clear_selection():
        ctrl.remove_all_labels()
        state.selected_labels = []
        ctrl.view_update()

    @state.change("mesh_color_array_idx")
    def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
        ctrl.color_by_array(state.active_actor, mesh_color_array_idx)
        ctrl.view_update()

    @state.change("mesh_color_preset")
    def update_mesh_color_preset(mesh_color_preset, **kwargs):
        ctrl.use_preset(state.active_actor, mesh_color_preset)
        ctrl.view_update()




