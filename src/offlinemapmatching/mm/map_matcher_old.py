from PyQt5.QtWidgets import QProgressBar, QComboBox, QLabel, QApplication
from qgis.core import *
from .hidden_states.hidden_model import *
from .observation.network import *
from .observation.trajectory import *

class MapMatcher:
    
    def __init__(self):
        self.layers = []
        self.attributes = []
        self.hidden_model = None
        self.network = None
        self.trajectoy = None
    
    def startViterbiMatching(self, pb, trajectory_name, network_name, attribute_name, sigma, my, max_dist, label, crs):
        check_results = 0
        
        label.setText('initialise data structur')
        QgsMessageLog.logMessage('initialise data structur', level=Qgis.Info)
        self.setUp(network_name, trajectory_name, attribute_name, pb)
        
        label.setText('create candidate graph')
        QgsMessageLog.logMessage('create candidate graph', level=Qgis.Info)
        check_results = self.hidden_model.createGraph(sigma, my, max_dist, pb)
        if check_results != 0:
            label.setText('cannot create candidate graph')
            QgsMessageLog.logMessage('cannot create candidate graph', level=Qgis.Info)
            return -1
        
        label.setText('calculate starting probabilities')
        QgsMessageLog.logMessage('calculate starting probabilities', level=Qgis.Info)
        check_results = self.hidden_model.setStartingProbabilities(pb)
        if check_results != 0:
            label.setText('cannot calculate starting probabilities')
            QgsMessageLog.logMessage('cannot calculate starting probabilities', level=Qgis.Info)
            return -3
        
        
        label.setText('calculate transition probabilities')
        QgsMessageLog.logMessage('calculate transition probabilities', level=Qgis.Info)
        check_results = self.hidden_model.setTransitionProbabilities(pb)
        if check_results != 0:
            label.setText('cannot calculate transition probabilities')
            QgsMessageLog.logMessage('cannot calculate transition probabilities', level=Qgis.Info)
            return -3
        
        
        label.setText('create backtracking')
        QgsMessageLog.logMessage('create backtracking', level=Qgis.Info)
        check_results = self.hidden_model.createBacktracking(pb)
        if check_results != 0:
            label.setText('cannot create backtracking')
            QgsMessageLog.logMessage('cannot create backtracking', level=Qgis.Info)
            return -3
        
        
        label.setText('get most likely path')
        QgsMessageLog.logMessage('get most likely path', level=Qgis.Info)
        vertices = self.hidden_model.findViterbiPath()
        if len(vertices) == 0:
            QgsMessageLog.logMessage('Cannot get a most likely path. Try to change settings.', level=Qgis.Critical)
            label.setText('cannot get path')
            return -3
        
        label.setText('get network path')
        QgsMessageLog.logMessage('get network path', level=Qgis.Info)
        layer = self.hidden_model.getPathOnNetwork(vertices, pb, 'EPSG:' + crs)
        if layer == -1:
            label.setText('cannot map trajectory')
            QgsMessageLog.logMessage('Routing between the result points, i.e. candidates with the highest total probability, does not work.', level=Qgis.Critical)
            return -5
        
        self.hidden_model.addLayerToTheMap(layer)
        
        layer.select([])
        QgsProject.instance().addMapLayer(layer)
        label.setText('finished ^o^')
        QgsMessageLog.logMessage('finished ^o^', level=Qgis.Info)
        return 0

    def fillLayerComboBox(self, iface, combobox, geom_type):
        #first clear the combobox
        combobox.clear()
        
        #get all layers in the current QGIS project
        self.layers = []
        self.layers = iface.mapCanvas().layers()
        
        #populate the combobox
        for layer in self.layers:
            if (QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.Point and geom_type == 'POINT') or (QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.LineString and geom_type == 'LINESTRING'):
                combobox.addItem(layer.name())
    
    def fillAttributeComboBox(self, combobox, layername):
        #first clear the combobox
        combobox.clear()
        
        #extract all attributes
        layer = self.getLayer(layername)
        if layer is not None:
            self.attributes = layer.fields()
        
        #populate the combobox
        for attr in self.attributes:
            combobox.addItem(attr.name())
    
    def getLayer(self, layername):
        for layer in self.layers:
            if layer.name() == layername:
                return layer
        return None
    
    def setUp(self, line_layer, point_layer, point_attr, pb):
        #init progressbar
        pb.setValue(0)
        pb.setMaximum(3)
        QApplication.processEvents()
        
        self.trajectory = Trajectory(self.getLayer(point_layer), point_attr)
        pb.setValue(pb.value() + 1)
        QApplication.processEvents()
        
        self.network = Network(self.getLayer(line_layer))
        pb.setValue(pb.value() + 1)
        QApplication.processEvents()
        
        self.hidden_model = HiddenModel(self.trajectory, self.network)
        pb.setValue(pb.value() + 1)
        QApplication.processEvents()
    
    