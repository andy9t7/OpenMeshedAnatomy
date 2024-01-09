import os

from vtkmodules.vtkIOLegacy import vtkUnstructuredGridReader
from vtkmodules.vtkCommonCore import (
    vtkFloatArray, 
    vtkLookupTable, 
    vtkPoints,
    vtkIdTypeArray
)
from vtkmodules.vtkCommonDataModel import (
    vtkDataObject,
    vtkSelection,
    vtkSelectionNode,
)
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection

from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkDiscretizableColorTransferFunction,

)

from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch #noqa


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))

class Representation:
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3

class LookupTable:
    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3
    Atlas = 4
    Material = 5

# ---------------------------------------------------------
# Visualization
# ---------------------------------------------------------

class VtkViewer:
    def __init__(self, app):
        # Read Data
        self.reader = vtkUnstructuredGridReader()
        self.reader.SetFileName(os.path.join(CURRENT_DIRECTORY, "../data/brain_v1b_labelled_Legacy.vtk"))
        self.reader.Update()

        # Extract Array/Field information
        self.dataset_arrays = []
        fields = [
            (self.reader.GetOutput().GetCellData(), vtkDataObject.FIELD_ASSOCIATION_CELLS),
        ]

        for field in fields:
            field_arrays, association = field
            for i in range(field_arrays.GetNumberOfArrays()):
                array = field_arrays.GetArray(i)
                array_range = array.GetRange()
                self.dataset_arrays.append(
                    {
                        "title": array.GetName(),
                        "array": array,
                        "value": i,
                        "range": list(array_range),
                        "type": association,
                    }
                )
        default_array = self.dataset_arrays[0]
        default_min, default_max = default_array.get("range")

        self.renderer = vtkRenderer()
        self.renderWindow = vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)

        self.renderWindowInteractor = vtkRenderWindowInteractor()
        self.renderWindowInteractor.SetRenderWindow(self.renderWindow)
        self.renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self._scene = {}
        self.scalar_bars = []

        self.renderer.SetBackground(0.2, 0.4, 0.6)
        self.camera.SetViewUp(0.0, 0.0, 1.0)
        self.camera.SetPosition(50.0, 50.0 - 1.0, 50.0)
        self.camera.SetFocalPoint(50.0, 50.0, 50.0)

        # # Mesh
        # self.mesh_mapper = vtkDataSetMapper()
        # self.mesh_mapper.SetInputConnection(self.reader.GetOutputPort())
        # self.mesh_actor = vtkActor()
        # self.mesh_actor.SetMapper(self.mesh_mapper)
        # self.renderer.AddActor(self.mesh_actor)

        # # Mesh: Setup default representation to surface
        # self.mesh_actor.GetProperty().SetRepresentationToSurface()
        # self.mesh_actor.GetProperty().SetPointSize(1)
        # self.mesh_actor.GetProperty().EdgeVisibilityOn()

        # Add mesh to scene
        self.add("HeadMesh", self.reader)

        self.renderer.ResetCamera()
    
    def getRenderWindow(self):
        return self.renderWindow
    
    def resetCamera(self):
        self.renderer.ResetCamera()

    @property
    def camera(self):
        return self.renderer.GetActiveCamera()
    
    def add(self, name, source):
        if name in self._scene:
            print(f"Trying to add name({name}) twice in {self.name}")
            return None

        actor = vtkActor()
        mapper = vtkDataSetMapper()
        lut = vtkLookupTable()
        lut.Build()
        if source.IsA("vtkDataSet"):
            mapper.SetInputData(source)
        else:
            mapper.SetInputConnection(source.GetOutputPort())
        mapper.SetLookupTable(lut)
        mapper.SetScalarModeToUseCellData()
        mapper.SetColorModeToMapScalars()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        item = {
            "name": name,
            "source": source,
            "mapper": mapper,
            "actor": actor,
        }
        self._scene[name] = item
        return item    
    
    def get(self, name):
        return self._scene.get(name, None)

    def get_list(self):
        print(self._scene)

    def remove(self, name):
        item = self.get(name)
        if item:
            self.renderer.RemoveActor(item["actor"])
            self._scene.pop(name)
    
    def remove_all(self):
        for name in list(self._scene.keys()):
            if name != "HeadMesh":
                self.remove(name)
    
    def set_representation(self, name, mode):
        item = self.get(name)
        property = item.get("actor").GetProperty()
        if mode == Representation.Points:
            property.SetRepresentationToPoints()
            property.SetPointSize(5)
            property.EdgeVisibilityOff()
        elif mode == Representation.Wireframe:
            property.SetRepresentationToWireframe()
            property.SetPointSize(1)
            property.EdgeVisibilityOff()
        elif mode == Representation.Surface:
            property.SetRepresentationToSurface()
            property.SetPointSize(1)
            property.EdgeVisibilityOff()
        elif mode == Representation.SurfaceWithEdges:
            property.SetRepresentationToSurface()
            property.SetPointSize(1)
            property.EdgeVisibilityOn()
    
    def get_representation(self, name):
        item = self.get(name)
        property = item.get("actor").GetProperty()
        representation = property.GetRepresentation()
        return representation
    
    def extract_selection(self, name, query):
        # Extract and create a new mesh from a query based on a cell array
        item = self.get(name)
        source = item.get("source")

        # Get the cell array
        cell_data = source.GetOutput().GetCellData()

        vtk_array = cell_data.GetArray("AtlasLabels")

        # Get the array of cell indices that match the query as a vtkIdTypeArray
        cell_indices = vtkIdTypeArray()
        cell_indices.SetNumberOfComponents(1)
        cell_indices.SetName(query.get("title"))
        for i in range(vtk_array.GetNumberOfTuples()):
            if vtk_array.GetValue(i) == query.get("value"):
                cell_indices.InsertNextValue(i)

        selectionNode = vtkSelectionNode()
        selectionNode.SetFieldType(vtkSelectionNode.CELL)
        selectionNode.SetContentType(vtkSelectionNode.INDICES)
        selectionNode.SetSelectionList(cell_indices)

        selection = vtkSelection()
        selection.AddNode(selectionNode)

        # Create a new mesh from the cell indices
        extractSelection = vtkExtractSelection()
        extractSelection.SetInputData(0, source.GetOutput())
        extractSelection.SetInputData(1, selection)
        extractSelection.Update()

        return extractSelection.GetOutput()
    
    def set_opacity(self, name, value):
        item = self.get(name)
        if item:
            property = item.get("actor").GetProperty()
            if property.GetOpacity() == value:
                return 0
            else:
                property.SetOpacity(value)
                return 1
        return 0
    
    def add_scalar_bar(self, title, lookup_table):
        scalar_bar = vtkScalarBarActor()
        scalar_bar.SetTitle(title)
        scalar_bar.SetLookupTable(lookup_table)
        self.renderer.AddActor(scalar_bar)
        self.scalar_bars.append(scalar_bar)
    
    def get_atlas_ctf(self):
        # name: mesh-material-atlas-colortable,
        # interpolationspace: RGB, space: rgb
        # file name: atlas-colortable-paraview.json

        ctf = vtkDiscretizableColorTransferFunction()

        ctf.SetColorSpaceToRGB()
        ctf.SetScaleToLinear()

        ctf.AddRGBPoint(1.0, 0.0, 0.5, 0.0)
        # ctf.AddRGBPoint(239.0, 1.0, 0.5, 0.0)
        ctf.AddRGBPoint(1.0, 1.0, 0.752941, 0.796078)
        ctf.AddRGBPoint(2.0, 1.0, 1.0, 0.0)
        ctf.AddRGBPoint(3.0, 0.0, 0.0, 1.0)
        ctf.AddRGBPoint(4.0, 0.980392, 0.980392, 0.882353)
        ctf.AddRGBPoint(5.0, 0.345098, 0.415686, 0.843137)
        ctf.AddRGBPoint(6.0, 0.345098, 0.415686, 0.843137)
        ctf.AddRGBPoint(7.0, 0.705882, 0.823529, 0.470588)
        ctf.AddRGBPoint(8.0, 0.117647, 0.435294, 0.333333)
        ctf.AddRGBPoint(9.0, 0.823529, 0.615686, 0.65098)
        ctf.AddRGBPoint(10.0, 0.0588235, 0.196078, 1.0)
        ctf.AddRGBPoint(11.0, 0.345098, 0.415686, 0.843137)
        ctf.AddRGBPoint(12.0, 0.862745, 0.843137, 0.0784314)
        ctf.AddRGBPoint(13.0, 0.384314, 0.6, 0.439216)
        ctf.AddRGBPoint(14.0, 0.345098, 0.415686, 0.843137)
        ctf.AddRGBPoint(15.0, 0.345098, 0.415686, 0.843137)
        ctf.AddRGBPoint(16.0, 1.0, 0.647059, 0.0)
        ctf.AddRGBPoint(17.0, 0.647059, 0.0, 1.0)
        ctf.AddRGBPoint(18.0, 0.196078, 0.196078, 0.529412)
        ctf.AddRGBPoint(19.0, 0.568627, 0.360784, 0.427451)
        ctf.AddRGBPoint(20.0, 0.980392, 0.980392, 0.882353)
        ctf.AddRGBPoint(21.0, 0.345098, 0.415686, 0.843137)
        ctf.AddRGBPoint(22.0, 0.345098, 0.415686, 0.843137)
        ctf.AddRGBPoint(23.0, 0.705882, 0.823529, 0.470588)
        ctf.AddRGBPoint(24.0, 0.117647, 0.435294, 0.333333)
        ctf.AddRGBPoint(25.0, 0.823529, 0.615686, 0.65098)
        ctf.AddRGBPoint(26.0, 0.0588235, 0.196078, 1.0)
        ctf.AddRGBPoint(27.0, 0.862745, 0.843137, 0.0784314)
        ctf.AddRGBPoint(28.0, 0.384314, 0.6, 0.439216)
        ctf.AddRGBPoint(29.0, 0.647059, 0.0, 1.0)
        ctf.AddRGBPoint(30.0, 0.529412, 0.803922, 0.921569)
        ctf.AddRGBPoint(31.0, 0.0, 0.423529, 0.439216)
        ctf.AddRGBPoint(32.0, 0.0, 0.423529, 0.439216)
        ctf.AddRGBPoint(33.0, 0.992157, 0.529412, 0.752941)
        ctf.AddRGBPoint(34.0, 0.847059, 0.862745, 0.329412)
        ctf.AddRGBPoint(35.0, 0.611765, 0.670588, 0.423529)
        ctf.AddRGBPoint(36.0, 1.0, 0.588235, 0.0392157)
        ctf.AddRGBPoint(37.0, 1.0, 0.647059, 0.0)
        ctf.AddRGBPoint(38.0, 1.0, 0.588235, 0.0392157)
        ctf.AddRGBPoint(39.0, 0.388235, 0.415686, 0.0941176)
        ctf.AddRGBPoint(40.0, 0.803922, 0.0392157, 0.490196)
        ctf.AddRGBPoint(41.0, 0.490196, 0.54902, 0.705882)
        ctf.AddRGBPoint(42.0, 0.862745, 0.882353, 0.27451)
        ctf.AddRGBPoint(43.0, 0.490196, 0.54902, 0.705882)
        ctf.AddRGBPoint(44.0, 0.847059, 0.862745, 0.329412)
        ctf.AddRGBPoint(45.0, 0.611765, 0.670588, 0.423529)
        ctf.AddRGBPoint(46.0, 0.921569, 0.247059, 0.623529)
        ctf.AddRGBPoint(47.0, 0.121569, 0.686275, 0.282353)
        ctf.AddRGBPoint(48.0, 0.839216, 0.105882, 0.588235)
        ctf.AddRGBPoint(49.0, 0.862745, 0.152941, 0.172549)
        ctf.AddRGBPoint(50.0, 0.192157, 0.372549, 0.698039)
        ctf.AddRGBPoint(51.0, 0.945098, 0.921569, 0.105882)
        ctf.AddRGBPoint(52.0, 0.619608, 0.219608, 0.631373)
        ctf.AddRGBPoint(53.0, 0.219608, 0.470588, 0.247059)
        ctf.AddRGBPoint(54.0, 0.584314, 0.294118, 0.25098)
        ctf.AddRGBPoint(55.0, 0.454902, 0.25098, 0.639216)
        ctf.AddRGBPoint(56.0, 0.486275, 0.545098, 0.345098)
        ctf.AddRGBPoint(57.0, 0.960784, 0.835294, 0.0823529)
        ctf.AddRGBPoint(58.0, 0.45098, 0.8, 0.509804)
        ctf.AddRGBPoint(59.0, 0.862745, 0.443137, 0.682353)
        ctf.AddRGBPoint(60.0, 0.847059, 0.415686, 0.454902)
        ctf.AddRGBPoint(61.0, 0.168627, 0.662745, 0.901961)
        ctf.AddRGBPoint(62.0, 0.929412, 0.898039, 0.580392)
        ctf.AddRGBPoint(63.0, 0.682353, 0.454902, 0.596078)
        ctf.AddRGBPoint(64.0, 0.403922, 0.643137, 0.447059)
        ctf.AddRGBPoint(65.0, 0.654902, 0.482353, 0.34902)
        ctf.AddRGBPoint(66.0, 0.643137, 0.482353, 0.733333)
        ctf.AddRGBPoint(67.0, 0.741176, 0.780392, 0.505882)
        ctf.AddRGBPoint(68.0, 0.952941, 0.905882, 0.392157)
        ctf.AddRGBPoint(69.0, 0.952941, 0.713725, 0.74902)
        ctf.AddRGBPoint(70.0, 0.670588, 0.847059, 0.560784)
        ctf.AddRGBPoint(71.0, 0.952941, 0.945098, 0.521569)
        ctf.AddRGBPoint(72.0, 0.87451, 0.635294, 0.839216)
        ctf.AddRGBPoint(73.0, 0.576471, 0.823529, 0.760784)
        ctf.AddRGBPoint(74.0, 0.847059, 0.745098, 0.517647)
        ctf.AddRGBPoint(75.0, 0.686275, 0.690196, 0.866667)
        ctf.AddRGBPoint(76.0, 0.92549, 0.960784, 0.768627)
        ctf.AddRGBPoint(77.0, 0.945098, 0.847059, 0.933333)
        ctf.AddRGBPoint(78.0, 0.921569, 0.247059, 0.623529)
        ctf.AddRGBPoint(79.0, 0.121569, 0.686275, 0.282353)
        ctf.AddRGBPoint(80.0, 0.839216, 0.105882, 0.588235)
        ctf.AddRGBPoint(81.0, 0.862745, 0.152941, 0.172549)
        ctf.AddRGBPoint(82.0, 0.192157, 0.372549, 0.698039)
        ctf.AddRGBPoint(83.0, 0.945098, 0.921569, 0.105882)
        ctf.AddRGBPoint(84.0, 0.619608, 0.219608, 0.631373)
        ctf.AddRGBPoint(85.0, 0.219608, 0.470588, 0.247059)
        ctf.AddRGBPoint(86.0, 0.584314, 0.294118, 0.25098)
        ctf.AddRGBPoint(87.0, 0.454902, 0.25098, 0.639216)
        ctf.AddRGBPoint(88.0, 0.486275, 0.545098, 0.345098)
        ctf.AddRGBPoint(89.0, 0.960784, 0.835294, 0.0823529)
        ctf.AddRGBPoint(90.0, 0.45098, 0.8, 0.509804)
        ctf.AddRGBPoint(91.0, 0.862745, 0.443137, 0.682353)
        ctf.AddRGBPoint(92.0, 0.847059, 0.415686, 0.454902)
        ctf.AddRGBPoint(93.0, 0.168627, 0.662745, 0.901961)
        ctf.AddRGBPoint(94.0, 0.929412, 0.898039, 0.580392)
        ctf.AddRGBPoint(95.0, 0.682353, 0.454902, 0.596078)
        ctf.AddRGBPoint(96.0, 0.403922, 0.643137, 0.447059)
        ctf.AddRGBPoint(97.0, 0.654902, 0.482353, 0.34902)
        ctf.AddRGBPoint(98.0, 0.643137, 0.482353, 0.733333)
        ctf.AddRGBPoint(99.0, 0.741176, 0.780392, 0.505882)
        ctf.AddRGBPoint(100.0, 0.952941, 0.905882, 0.392157)
        ctf.AddRGBPoint(101.0, 0.952941, 0.713725, 0.74902)
        ctf.AddRGBPoint(102.0, 0.670588, 0.847059, 0.560784)
        ctf.AddRGBPoint(103.0, 0.952941, 0.945098, 0.521569)
        ctf.AddRGBPoint(104.0, 0.87451, 0.635294, 0.839216)
        ctf.AddRGBPoint(105.0, 0.576471, 0.823529, 0.760784)
        ctf.AddRGBPoint(106.0, 0.847059, 0.745098, 0.517647)
        ctf.AddRGBPoint(107.0, 0.686275, 0.690196, 0.866667)
        ctf.AddRGBPoint(108.0, 0.92549, 0.960784, 0.768627)
        ctf.AddRGBPoint(109.0, 0.945098, 0.847059, 0.933333)
        ctf.AddRGBPoint(110.0, 0.392157, 0.784314, 0.392157)
        ctf.AddRGBPoint(111.0, 1.0, 0.0, 0.0)
        ctf.AddRGBPoint(112.0, 0.392157, 0.784314, 0.392157)
        ctf.AddRGBPoint(113.0, 1.0, 0.0, 0.0)
        ctf.AddRGBPoint(114.0, 0.952941, 0.533333, 0.243137)
        ctf.AddRGBPoint(115.0, 0.529412, 0.968627, 0.0156863)
        ctf.AddRGBPoint(116.0, 0.576471, 0.270588, 0.0705882)
        ctf.AddRGBPoint(117.0, 0.0156863, 0.921569, 0.490196)
        ctf.AddRGBPoint(118.0, 0.490196, 0.14902, 0.803922)
        ctf.AddRGBPoint(119.0, 0.952941, 0.533333, 0.243137)
        ctf.AddRGBPoint(120.0, 0.529412, 0.968627, 0.0156863)
        ctf.AddRGBPoint(121.0, 0.576471, 0.270588, 0.0705882)
        ctf.AddRGBPoint(122.0, 0.0156863, 0.921569, 0.490196)
        ctf.AddRGBPoint(123.0, 0.490196, 0.14902, 0.803922)
        ctf.AddRGBPoint(124.0, 0.784314, 0.0980392, 0.54902)
        ctf.AddRGBPoint(125.0, 0.784314, 0.0980392, 0.54902)
        ctf.AddRGBPoint(126.0, 0.784314, 0.784314, 0.784314)
        ctf.AddRGBPoint(127.0, 0.784314, 0.784314, 0.784314)
        ctf.AddRGBPoint(128.0, 0.490196, 0.980392, 0.0784314)
        ctf.AddRGBPoint(129.0, 0.490196, 0.980392, 0.0784314)
        ctf.AddRGBPoint(130.0, 0.392157, 0.705882, 1.0)
        ctf.AddRGBPoint(131.0, 0.392157, 0.705882, 1.0)
        ctf.AddRGBPoint(132.0, 0.247059, 0.411765, 0.882353)
        ctf.AddRGBPoint(133.0, 0.247059, 0.411765, 0.882353)
        ctf.AddRGBPoint(134.0, 1.0, 0.0980392, 0.509804)
        ctf.AddRGBPoint(135.0, 1.0, 0.0980392, 0.509804)
        ctf.AddRGBPoint(136.0, 0.235294, 0.745098, 0.509804)
        ctf.AddRGBPoint(137.0, 0.235294, 0.745098, 0.509804)
        ctf.AddRGBPoint(138.0, 0.745098, 0.705882, 0.411765)
        ctf.AddRGBPoint(139.0, 0.745098, 0.705882, 0.411765)
        ctf.AddRGBPoint(140.0, 1.0, 0.835294, 0.0)
        ctf.AddRGBPoint(141.0, 1.0, 0.835294, 0.0)
        ctf.AddRGBPoint(142.0, 0.235294, 0.705882, 0.705882)
        ctf.AddRGBPoint(143.0, 0.235294, 0.705882, 0.705882)
        ctf.AddRGBPoint(144.0, 0.803922, 0.509804, 0.0)
        ctf.AddRGBPoint(145.0, 0.803922, 0.509804, 0.0)
        ctf.AddRGBPoint(146.0, 0.686275, 0.764706, 0.862745)
        ctf.AddRGBPoint(147.0, 0.686275, 0.764706, 0.862745)
        ctf.AddRGBPoint(148.0, 0.882353, 0.666667, 0.411765)
        ctf.AddRGBPoint(149.0, 0.882353, 0.666667, 0.411765)
        ctf.AddRGBPoint(150.0, 0.901961, 0.509804, 0.509804)
        ctf.AddRGBPoint(151.0, 0.901961, 0.509804, 0.509804)
        ctf.AddRGBPoint(152.0, 0.490196, 0.0196078, 0.0980392)
        ctf.AddRGBPoint(153.0, 0.0980392, 0.392157, 0.156863)
        ctf.AddRGBPoint(154.0, 0.490196, 0.392157, 0.627451)
        ctf.AddRGBPoint(155.0, 0.392157, 0.0980392, 0.0)
        ctf.AddRGBPoint(156.0, 0.862745, 0.0784314, 0.392157)
        ctf.AddRGBPoint(157.0, 0.72549, 0.0588235, 0.0392157)
        ctf.AddRGBPoint(158.0, 0.705882, 0.862745, 0.54902)
        ctf.AddRGBPoint(159.0, 0.72549, 0.352941, 0.72549)
        ctf.AddRGBPoint(160.0, 0.705882, 0.156863, 0.470588)
        ctf.AddRGBPoint(161.0, 0.54902, 0.0784314, 0.54902)
        ctf.AddRGBPoint(162.0, 0.0784314, 0.117647, 0.54902)
        ctf.AddRGBPoint(163.0, 0.137255, 0.294118, 0.196078)
        ctf.AddRGBPoint(164.0, 0.882353, 0.54902, 0.54902)
        ctf.AddRGBPoint(165.0, 0.784314, 0.137255, 0.294118)
        ctf.AddRGBPoint(166.0, 0.627451, 0.392157, 0.196078)
        ctf.AddRGBPoint(167.0, 0.956863, 0.956863, 0.0941176)
        ctf.AddRGBPoint(168.0, 0.235294, 0.686275, 0.313725)
        ctf.AddRGBPoint(169.0, 0.862745, 0.705882, 0.54902)
        ctf.AddRGBPoint(170.0, 0.862745, 0.54902, 0.705882)
        ctf.AddRGBPoint(171.0, 0.862745, 0.235294, 0.0784314)
        ctf.AddRGBPoint(172.0, 0.470588, 0.392157, 0.235294)
        ctf.AddRGBPoint(173.0, 0.764706, 0.156863, 0.156863)
        ctf.AddRGBPoint(174.0, 0.862745, 0.705882, 0.862745)
        ctf.AddRGBPoint(175.0, 0.372549, 0.294118, 0.686275)
        ctf.AddRGBPoint(176.0, 0.627451, 0.54902, 0.705882)
        ctf.AddRGBPoint(177.0, 0.313725, 0.0784314, 0.54902)
        ctf.AddRGBPoint(178.0, 0.294118, 0.196078, 0.490196)
        ctf.AddRGBPoint(179.0, 0.196078, 0.627451, 0.588235)
        ctf.AddRGBPoint(180.0, 0.0784314, 0.705882, 0.54902)
        ctf.AddRGBPoint(181.0, 0.54902, 0.862745, 0.862745)
        ctf.AddRGBPoint(182.0, 0.313725, 0.627451, 0.0784314)
        ctf.AddRGBPoint(183.0, 0.392157, 0.0, 0.392157)
        ctf.AddRGBPoint(184.0, 0.27451, 0.27451, 0.27451)
        ctf.AddRGBPoint(185.0, 0.588235, 0.588235, 0.784314)
        ctf.AddRGBPoint(186.0, 0.568627, 0.196078, 0.254902)
        ctf.AddRGBPoint(187.0, 0.490196, 0.0196078, 0.0980392)
        ctf.AddRGBPoint(188.0, 0.0980392, 0.392157, 0.156863)
        ctf.AddRGBPoint(189.0, 0.490196, 0.392157, 0.627451)
        ctf.AddRGBPoint(190.0, 0.392157, 0.0980392, 0.0)
        ctf.AddRGBPoint(191.0, 0.862745, 0.0784314, 0.392157)
        ctf.AddRGBPoint(192.0, 0.72549, 0.0588235, 0.0392157)
        ctf.AddRGBPoint(193.0, 0.705882, 0.862745, 0.54902)
        ctf.AddRGBPoint(194.0, 0.72549, 0.352941, 0.72549)
        ctf.AddRGBPoint(195.0, 0.705882, 0.156863, 0.470588)
        ctf.AddRGBPoint(196.0, 0.54902, 0.0784314, 0.54902)
        ctf.AddRGBPoint(197.0, 0.0784314, 0.117647, 0.54902)
        ctf.AddRGBPoint(198.0, 0.137255, 0.294118, 0.196078)
        ctf.AddRGBPoint(199.0, 0.882353, 0.54902, 0.54902)
        ctf.AddRGBPoint(200.0, 0.784314, 0.137255, 0.294118)
        ctf.AddRGBPoint(201.0, 0.627451, 0.392157, 0.196078)
        ctf.AddRGBPoint(202.0, 0.956863, 0.956863, 0.0941176)
        ctf.AddRGBPoint(203.0, 0.235294, 0.686275, 0.313725)
        ctf.AddRGBPoint(204.0, 0.862745, 0.705882, 0.54902)
        ctf.AddRGBPoint(205.0, 0.862745, 0.54902, 0.705882)
        ctf.AddRGBPoint(206.0, 0.862745, 0.235294, 0.0784314)
        ctf.AddRGBPoint(207.0, 0.470588, 0.392157, 0.235294)
        ctf.AddRGBPoint(208.0, 0.764706, 0.156863, 0.156863)
        ctf.AddRGBPoint(209.0, 0.862745, 0.705882, 0.862745)
        ctf.AddRGBPoint(210.0, 0.372549, 0.294118, 0.686275)
        ctf.AddRGBPoint(211.0, 0.627451, 0.54902, 0.705882)
        ctf.AddRGBPoint(212.0, 0.313725, 0.0784314, 0.54902)
        ctf.AddRGBPoint(213.0, 0.294118, 0.196078, 0.490196)
        ctf.AddRGBPoint(214.0, 0.196078, 0.627451, 0.588235)
        ctf.AddRGBPoint(215.0, 0.0784314, 0.705882, 0.54902)
        ctf.AddRGBPoint(216.0, 0.54902, 0.862745, 0.862745)
        ctf.AddRGBPoint(217.0, 0.313725, 0.627451, 0.0784314)
        ctf.AddRGBPoint(218.0, 0.392157, 0.0, 0.392157)
        ctf.AddRGBPoint(219.0, 0.27451, 0.27451, 0.27451)
        ctf.AddRGBPoint(220.0, 0.588235, 0.588235, 0.784314)
        ctf.AddRGBPoint(221.0, 0.568627, 0.196078, 0.254902)
        ctf.AddRGBPoint(222.0, 0.901961, 0.607843, 0.843137)
        ctf.AddRGBPoint(223.0, 0.901961, 0.607843, 0.843137)
        ctf.AddRGBPoint(224.0, 0.607843, 0.901961, 1.0)
        ctf.AddRGBPoint(225.0, 0.607843, 0.901961, 1.0)
        ctf.AddRGBPoint(226.0, 0.380392, 0.443137, 0.619608)
        ctf.AddRGBPoint(227.0, 0.25098, 0.482353, 0.576471)
        ctf.AddRGBPoint(228.0, 0.25098, 0.482353, 0.576471)
        ctf.AddRGBPoint(229.0, 0.137255, 0.764706, 0.137255)
        ctf.AddRGBPoint(230.0, 0.235294, 0.560784, 0.32549)
        ctf.AddRGBPoint(231.0, 0.360784, 0.635294, 0.427451)
        ctf.AddRGBPoint(232.0, 0.945098, 0.839216, 0.568627)
        ctf.AddRGBPoint(233.0, 0.866667, 0.509804, 0.396078)
        ctf.AddRGBPoint(234.0, 0.694118, 0.478431, 0.396078)
        ctf.AddRGBPoint(235.0, 0.435294, 0.721569, 0.823529)
        ctf.AddRGBPoint(236.0, 0.568627, 0.54902, 0.862745)
        ctf.AddRGBPoint(237.0, 0.686275, 0.941176, 0.54902)
        ctf.AddRGBPoint(238.0, 0.470588, 0.823529, 0.823529)
        ctf.AddRGBPoint(239.0, 0.54902, 0.54902, 0.447059)

        ctf.SetNumberOfValues(241)
        ctf.DiscretizeOn()
        ctf.IndexedLookupOn()

        ctf.Build()
        return ctf

    def get_material_ctf(self):
        # name: mesh-material-atlas-colortable2,
        # interpolationspace: RGB, space: rgb
        # file name: material-atlas-colortable-paraview.json

        ctf = vtkDiscretizableColorTransferFunction()

        ctf.SetColorSpaceToRGB()
        ctf.SetScaleToLinear()


        # ctf.AddRGBPoint(1.0, 0.0, 0.5, 0.0)
        # ctf.AddRGBPoint(7.0, 1.0, 0.5, 0.0)
        # ctf.AddRGBPoint(1.0, 1.0, 0.752941, 0.796078)
        # ctf.AddRGBPoint(2.0, 1.0, 1.0, 0.0)
        # ctf.AddRGBPoint(4.0, 0.501961, 0.501961, 0.501961)
        # ctf.AddRGBPoint(5.0, 0.0, 0.0, 1.0)
        # ctf.AddRGBPoint(7.0, 1.0, 1.0, 1.0)

        ctf.AddRGBPoint(1.0, 0.0, 0.5, 0.0)
        ctf.AddRGBPoint(2.0, 1.0, 0.5, 0.0)
        ctf.AddRGBPoint(3.0, 1.0, 0.752941, 0.796078)
        ctf.AddRGBPoint(4.0, 1.0, 1.0, 0.0)
        ctf.AddRGBPoint(5.0, 0.501961, 0.501961, 0.501961)
        ctf.AddRGBPoint(6.0, 0.0, 0.0, 1.0)
        ctf.AddRGBPoint(7.0, 1.0, 1.0, 1.0)

        ctf.SetNumberOfValues(7)
        ctf.DiscretizeOn()
        ctf.IndexedLookupOn()

        ctf.Build()

        return ctf

    def color_by_array(self, actor_name, idx):
            actor = self.get(actor_name).get("actor")
            _min, _max = self.dataset_arrays[idx].get("range")
            print(_min, _max)
            mapper = actor.GetMapper()
            mapper.SelectColorArray(self.dataset_arrays[idx].get("title"))
            mapper.GetLookupTable().SetRange(_min, _max)
            mapper.SetScalarModeToUseCellFieldData()
            mapper.SetScalarVisibility(True)
            mapper.SetUseLookupTableScalarRange(True)

    # Color Map Callbacks
    def use_preset(self, actor_name, preset):
        actor = self.get(actor_name).get("actor")
        lut = actor.GetMapper().GetLookupTable()
        if preset == LookupTable.Rainbow:
            lut.SetHueRange(0.666, 0.0)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(1.0, 1.0)
            lut.Build()
            self.add_scalar_bar(actor_name, lut)

        elif preset == LookupTable.Inverted_Rainbow:
            lut.SetHueRange(0.0, 0.666)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(1.0, 1.0)
            lut.Build()
            self.add_scalar_bar(actor_name, lut)

        elif preset == LookupTable.Greyscale:
            lut.SetHueRange(0.0, 0.0)
            lut.SetSaturationRange(0.0, 0.0)
            lut.SetValueRange(0.0, 1.0)
            lut.Build()
            self.add_scalar_bar(actor_name, lut)

        elif preset == LookupTable.Inverted_Greyscale:
            lut.SetHueRange(0.0, 0.666)
            lut.SetSaturationRange(0.0, 0.0)
            lut.SetValueRange(1.0, 0.0)
            lut.Build()
            self.add_scalar_bar(actor_name, lut)

        elif preset == LookupTable.Atlas:
            ctf = self.get_atlas_ctf()
            mapper = actor.GetMapper()
            mapper.SetScalarModeToUseCellData()
            mapper.SetColorModeToMapScalars()
            mapper.SetLookupTable(ctf)
            self.add_scalar_bar(actor_name, ctf)


        elif preset == LookupTable.Material:
            ctf = self.get_material_ctf()
            mapper = actor.GetMapper()
            mapper.SetLookupTable(ctf)
            mapper.SelectColorArray("MaterialLabels")

            self.add_scalar_bar(actor_name, ctf)









        
    

