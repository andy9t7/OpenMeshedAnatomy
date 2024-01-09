from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import trame as trame_widgets, vuetify3 as vuetify_widgets, vtk as vtk_widgets

def build_ui(server, **kwargs):
    state, ctrl = server.state, server.controller

    with SinglePageWithDrawerLayout(server) as layout:
        # Header
        layout.title.set_text("Open Meshed Anatomy")

        with layout.toolbar as toolbar:
            create_toolbar(toolbar, ctrl)
        with layout.drawer as drawer:
            create_drawer(drawer, state, ctrl)
        with layout.content as content:
            create_content(content, state, ctrl)

        # Footer
        layout.footer.hide()

        return layout

#--------------------
# Toolbar
#--------------------

def create_toolbar(toolbar, ctrl):
    pass

#--------------------
# Drawer
#--------------------

def create_drawer(drawer, state, ctrl):
    drawer.width = 350
    with vuetify_widgets.VContainer(
        fluid=False, classes="pa-2"
    ):
        active_card(state)
        mesh_card(state)
        query_card(state)

def active_card(state):
    with vuetify_widgets.VCard(classes="mb-2"):
        vuetify_widgets.VCardTitle(
            "Mesh",
        )
        vuetify_widgets.VDivider()
        vuetify_widgets.VSelect(
            # Representation
            v_model=("active_actor"),
            # items=("scene", state.scene),
            label="Active",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pa-2"
        )

def mesh_card(state):
    with vuetify_widgets.VCard(classes="mb-2"):
        vuetify_widgets.VCardTitle(
            "Mesh Properties",
        )
        vuetify_widgets.VDivider()
        vuetify_widgets.VSelect(
            # Representation
            v_model=("mesh_representation"),
            items=(
                "representations",
                [
                    {"title": "Points",  "value": 0},
                    {"title": "Wireframe", "value": 1},
                    {"title": "Surface", "value": 2},
                    {"title": "SurfaceWithEdges", "value": 3},
                ],
            ),
            label="Representation",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pa-2"
        )

        with vuetify_widgets.VRow(classes="pa-2", dense=True):
            with vuetify_widgets.VCol(cols="6"):

                vuetify_widgets.VSelect(
                    # Color By
                    label="Color by",
                    v_model=("mesh_color_array_idx"),
                    items=("array_list", state.dataset_arrays),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )

            with vuetify_widgets.VCol(cols="6"):

                vuetify_widgets.VSelect(
                    # Color Map
                    label="Colormap",
                    v_model=("mesh_color_preset"),
                    items=(
                        "colormaps",
                        [
                            {"title": "Rainbow", "value": 0},
                            {"title": "Inv Rainbow", "value": 1},
                            {"title": "Greyscale", "value": 2},
                            {"title": "Inv Greyscale", "value": 3},
                            {"title": "Atlas", "value": 4},
                            {"title": "Material", "value": 5},
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )

        vuetify_widgets.VSlider(
            # Opacity
            v_model=("mesh_opacity"),
            min=0,
            max=1,
            step=0.05,
            label="Opacity",
            classes="pa-2 px-4",
            hide_details=True,
            dense=True,
        )

def query_card(state):
    with vuetify_widgets.VCard(classes="mx-auto"):
        vuetify_widgets.VCardTitle(
            "Query Data",
        )
        vuetify_widgets.VDivider()
        with vuetify_widgets.VList(height=400, classes="overflow-y-auto", shaped=True):
            vuetify_widgets.VListSubheader(title="Atlas Labels")

            with vuetify_widgets.VListItem(v_for="item in atlas_label",):
                with vuetify_widgets.VListItemAction():
                    vuetify_widgets.VListItemTitle("{{item.title}}")
                    vuetify_widgets.VCheckboxBtn(v_model=("selected_labels"), value=("item",), multiple=True)
                # vuetify_widgets.VCheckboxBtn(v_model=("selected_label",), value=("item",), dense=True)
        vuetify_widgets.VDivider()
        vuetify_widgets.VBtn("Query", block=True, click="trigger('query_selection')")
        vuetify_widgets.VBtn("Clear", block=True, click="trigger('clear_selection')")

#--------------------
# Content
#--------------------

def create_content(content, state, ctrl):
    with content:
        view = vtk_widgets.VtkLocalView(ctrl.getRenderWindow())
        ctrl.view_update = view.update
        ctrl.view_reset_camera = view.reset_camera
        ctrl.on_server_ready.add(view.update)

