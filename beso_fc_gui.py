# simple GUI to be used as FreeCAD macro
# all beso python files should be in the macro directory

__title__ = "BESO Topology Optimization"
__author__ = "František Löffelmann"
__date__ = "28/09/2020"
__Wiki__ = "https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD"
__Status__ = "experimental"
__Requires__ = "FreeCAD >=0.18, Python 3"

import datetime
import os
import threading
import webbrowser
from PySide.QtGui import (QDialog, QWidget, QLabel, QFileDialog, QPushButton, QLineEdit, QComboBox, QCheckBox,
                          QListWidget, QSlider, QAbstractItemView)
# from PySide.QtCore import pyqtSlot, Qt
from PySide.QtCore import Qt
import FreeCADGui
from femtools import ccxtools


class beso_gui(QDialog):

    def __init__(self):
        super().__init__()
        self.title = 'BESO Topology Optimization (experimental)'
        self.left = 250
        self.top = 30
        self.width = 550
        self.height = 730

        beso_gui.inp_file = ""
        beso_gui.beso_dir = os.path.dirname(__file__)

        self.initUI()

    # def closeEvent(self, event):
    #     self.close()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Select analysis file button
        button = QPushButton('Select analysis file', self)
        button.setToolTip('*.inp CalculiX analysis file.')
        button.move(10, 10)
        button.clicked.connect(self.on_click)

        # Text box - file path and name
        self.textbox_file_name = QLineEdit(self)
        self.textbox_file_name.move(120, 15)
        self.textbox_file_name.resize(420, 20)
        self.textbox_file_name.setText("None analysis file selected")
        self.textbox_file_name.setToolTip('Analysis file.')

        # Update button
        button1 = QPushButton('Update domains', self)
        button1.setToolTip('Update naming inputs and material data from FreeCAD.')
        button1.move(10, 50)
        button1.clicked.connect(self.on_click1)
        
        # Domains definition

        # Label above domains definition
        label21 = QLabel('Domain 0', self)
        label21.setStyleSheet("font-weight: bold")
        label21.move(120, 50)

        label21 = QLabel('Domain 1', self)
        label21.setStyleSheet("font-weight: bold")
        label21.move(260, 50)

        label21 = QLabel('Domain 2', self)
        label21.setStyleSheet("font-weight: bold")
        label21.move(400, 50)

        label24 = QLabel('Material object', self)
        label24.move(20, 80)

        label25 = QLabel('Thickness object', self)
        label25.move(20, 110)

        label26 = QLabel('As design domain', self)
        label26.move(20, 140)

        label27 = QLabel('Stress limit [MPa]', self)
        label27.move(20, 170)

        # Combo box - select domain by material object
        self.combo = QComboBox(self)
        self.combo.setToolTip('Material object to define the domain.')
        self.combo.move(120, 80)
        self.combo.resize(140, 30)
        self.combo.currentIndexChanged.connect(self.on_change)

        self.combo1 = QComboBox(self)
        self.combo1.setToolTip('Material object to define the domain.')
        self.combo1.move(260, 80)
        self.combo1.resize(140, 30)
        self.combo1.currentIndexChanged.connect(self.on_change1)

        self.combo2 = QComboBox(self)
        self.combo2.setToolTip('Material object to define the domain.')
        self.combo2.move(400, 80)
        self.combo2.resize(140, 30)
        self.combo2.currentIndexChanged.connect(self.on_change2)

        # Combo box - select thickness object
        self.combo0t = QComboBox(self)
        self.combo0t.setToolTip('Thickness object to specify if domain is for shells.')
        self.combo0t.move(120, 110)
        self.combo0t.resize(140, 30)

        self.combo1t = QComboBox(self)
        self.combo1t.setToolTip('Thickness object to specify if domain is for shells.')
        self.combo1t.move(260, 110)
        self.combo1t.resize(140, 30)

        self.combo2t = QComboBox(self)
        self.combo2t.setToolTip('Thickness object to specify if domain is for shells.')
        self.combo2t.move(400, 110)
        self.combo2t.resize(140, 30)

        self.textbox3 = QLineEdit(self)
        self.textbox3.move(120, 170)
        self.textbox3.resize(40, 20)
        # self.textbox3.setText("")
        self.textbox3.setToolTip('Thickness [mm] of shell elements in the domain.\n'
                                 'This value overwrites thickness defined in FreeCAD')

        self.textbox4 = QLineEdit(self)
        self.textbox4.move(260, 170)
        self.textbox4.resize(40, 20)
        # self.textbox4.setText("")
        self.textbox4.setToolTip('Thickness [mm] of shell elements in the domain.\n'
                                 'This value overwrites thickness defined in FreeCAD')

        self.textbox5 = QLineEdit(self)
        self.textbox5.move(400, 170)
        self.textbox5.resize(40, 20)
        # self.textbox5.setText("")
        self.textbox5.setToolTip('Thickness [mm] of shell elements in the domain.\n'
                                 'This value overwrites thickness defined in FreeCAD')

        # Check box - design or nondesign
        self.checkbox = QCheckBox('', self)
        self.checkbox.setChecked(True)
        self.checkbox.setToolTip('Check to be the design domain.')
        self.checkbox.move(120, 140)

        self.checkbox1 = QCheckBox('', self)
        self.checkbox1.setChecked(True)
        self.checkbox1.setToolTip('Check to be the design domain.')
        self.checkbox1.move(260, 140)

        self.checkbox2 = QCheckBox('', self)
        self.checkbox2.setChecked(True)
        self.checkbox2.setToolTip('Check to be the design domain.')
        self.checkbox2.move(400, 140)

        # Text box - stress limit
        self.textbox = QLineEdit(self)
        self.textbox.move(120, 170)
        self.textbox.resize(40, 20)
        # self.textbox.setText("")
        self.textbox.setToolTip('Von Mises stress [MPa] limit, when reached, material removing will stop.')

        self.textbox1 = QLineEdit(self)
        self.textbox1.move(260, 170)
        self.textbox1.resize(40, 20)
        # self.textbox1.setText("")
        self.textbox1.setToolTip('Von Mises stress [MPa] limit, when reached, material removing will stop.')

        self.textbox2 = QLineEdit(self)
        self.textbox2.move(400, 170)
        self.textbox2.resize(40, 20)
        # self.textbox2.setText("")
        self.textbox2.setToolTip('Von Mises stress [MPa] limit, when reached, material removing will stop.')

        # Filters

        # Label above filter definition
        label31 = QLabel('Filter 0', self)
        label31.setStyleSheet("font-weight: bold")
        label31.move(120, 210)

        label32 = QLabel('Filter 1', self)
        label32.setStyleSheet("font-weight: bold")
        label32.move(260, 210)

        label33 = QLabel('Filter 2', self)
        label33.setStyleSheet("font-weight: bold")
        label33.move(400, 210)

        label34 = QLabel('Type', self)
        label34.move(20, 240)

        label35 = QLabel('Range [mm]', self)
        label35.move(20, 270)

        label36 = QLabel('Direction vector', self)
        label36.move(20, 300)

        label37 = QLabel('Apply to', self)
        label37.move(20, 330)

        # Combo box - select filter type
        self.combo6 = QComboBox(self)
        self.combo6.setToolTip('Filters:\n'
                               '"simple" to suppress checkerboard effect,\n'
                               '"casting" to prescribe casting direction (opposite to milling direction)\n'
                               'Recommendation: for casting use as first "casting" and as second "simple"')
        self.combo6.addItem("None")
        self.combo6.addItem("simple")
        self.combo6.addItem("casting")
        self.combo6.setCurrentIndex(1)
        self.combo6.move(120, 240)
        self.combo6.currentIndexChanged.connect(self.on_change6)

        self.combo7 = QComboBox(self)
        self.combo7.setToolTip('Filters:\n'
                               '"simple" to suppress checkerboard effect,\n'
                               '"casting" to prescribe casting direction (opposite to milling direction)\n'
                               'Recommendation: for casting use as first "casting" and as second "simple"')
        self.combo7.addItem("None")
        self.combo7.addItem("simple")
        self.combo7.addItem("casting")
        self.combo7.move(260, 240)
        self.combo7.currentIndexChanged.connect(self.on_change7)

        self.combo8 = QComboBox(self)
        self.combo8.setToolTip('Filters:\n'
                               '"simple" to suppress checkerboard effect,\n'
                               '"casting" to prescribe casting direction (opposite to milling direction)\n'
                               'Recommendation: for casting use as first "casting" and as second "simple"')
        self.combo8.addItem("None")
        self.combo8.addItem("simple")
        self.combo8.addItem("casting")
        self.combo8.move(400, 240)
        self.combo8.currentIndexChanged.connect(self.on_change8)

        # Text box - filter range
        self.textbox6 = QLineEdit(self)
        self.textbox6.move(120, 270)
        self.textbox6.resize(50, 20)
        self.textbox6.setText("0.")
        self.textbox6.setToolTip('Filter range [mm], recommended two times mesh size.')

        self.textbox7 = QLineEdit(self)
        self.textbox7.move(260, 270)
        self.textbox7.resize(50, 20)
        self.textbox7.setText("0.")
        self.textbox7.setToolTip('Filter range [mm], recommended two times mesh size.')
        self.textbox7.setEnabled(False)

        self.textbox8 = QLineEdit(self)
        self.textbox8.move(400, 270)
        self.textbox8.resize(50, 20)
        self.textbox8.setText("0.")
        self.textbox8.setToolTip('Filter range [mm], recommended two times mesh size.')
        self.textbox8.setEnabled(False)

        # Text box - casting direction
        self.textbox9 = QLineEdit(self)
        self.textbox9.move(120, 300)
        self.textbox9.resize(80, 20)
        self.textbox9.setText("0, 0, 1")
        self.textbox9.setEnabled(False)
        self.textbox9.setToolTip('Casting direction vector, e.g. direction in z axis:\n'
                                 '0, 0, 1\n\n'
                                 'solid              void\n'
                                 'XXXXXX.................\n'
                                 'XXX........................\n'
                                 'XX...........................          --> z axis\n'
                                 'XXXXX....................\n'
                                 'XXXXXXXXXXX......')

        self.textbox10 = QLineEdit(self)
        self.textbox10.move(260, 300)
        self.textbox10.resize(80, 20)
        self.textbox10.resize(80, 20)
        self.textbox10.setText("0, 0, 1")
        self.textbox10.setEnabled(False)
        self.textbox10.setToolTip('Casting direction vector, e.g. direction in z axis:\n'
                                  '0, 0, 1\n\n'
                                 'solid              void\n'
                                 'XXXXXX.................\n'
                                 'XXX........................\n'
                                 'XX...........................          --> z axis\n'
                                 'XXXXX....................\n'
                                 'XXXXXXXXXXX......')

        self.textbox11 = QLineEdit(self)
        self.textbox11.move(400, 300)
        self.textbox11.resize(80, 20)
        self.textbox11.setText("0, 0, 1")
        self.textbox11.setEnabled(False)
        self.textbox11.setToolTip('Casting direction vector, e.g. direction in z axis:\n'
                                  '0, 0, 1\n\n'
                                 'solid              void\n'
                                 'XXXXXX.................\n'
                                 'XXX........................\n'
                                 'XX...........................          --> z axis\n'
                                 'XXXXX....................\n'
                                 'XXXXXXXXXXX......')

        # list widget - select domains
        self.widget = QListWidget(self)
        self.widget.setToolTip('Domains affected by the filter.\n'
                               'Select only from domains which you defined above.')
        self.widget.move(120, 330)
        self.widget.resize(140, 120)
        self.widget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.widget1 = QListWidget(self)
        self.widget1.setToolTip('Domains affected by the filter.\n'
                                'Select only from domains which you defined above.')
        self.widget1.move(260, 330)
        self.widget1.resize(140, 120)
        self.widget1.setSelectionMode(QAbstractItemView.MultiSelection)
        self.widget1.setEnabled(False)

        self.widget2 = QListWidget(self)
        self.widget2.setToolTip('Domains affected by the filter.\n'
                                'Select only from domains which you defined above.')
        self.widget2.move(400, 330)
        self.widget2.resize(140, 120)
        self.widget2.setSelectionMode(QAbstractItemView.MultiSelection)
        self.widget2.setEnabled(False)

        # Other settings
        label40 = QLabel('Other settings', self)
        label40.setStyleSheet("font-weight: bold")
        label40.move(10, 470)

        # AR, RR slider
        label41 = QLabel('Change per iteration:   low', self)
        label41.setFixedWidth(160)
        label41.move(10, 500)
        label42 = QLabel('high', self)
        label42.move(240, 500)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(1, 3)
        self.slider.setSingleStep(1)
        self.slider.setValue(2)
        self.slider.move(150, 500)
        self.slider.resize(80, 30)
        self.slider.setToolTip('Sets mass change per iteration, which is controlled as\n'
                               'slow:   mass_addition_ratio=0.01,  mass_removal_ratio=0.02\n'
                               'middle: mass_addition_ratio=0.015, mass_removal_ratio=0.03\n'
                               'fast:   mass_addition_ratio=0.03,  mass_removal_ratio=0.06')

        # optimization base combobox
        label51 = QLabel('Optimization base', self)
        label51.move(10, 530)
        self.combo51 = QComboBox(self)
        self.combo51.setToolTip('Basic principle to determine if element should remain or be removed:\n'
                                '"stiffness" to maximize stiffness (minimize compliance),\n'
                                '"heat" to maximize heat flow.')
        self.combo51.addItem("stiffness")
        self.combo51.addItem("heat")
        self.combo51.move(120, 530)

        # mass goal ratio
        label52 = QLabel('Mass goal ratio', self)
        label52.move(10, 560)
        self.textbox52 = QLineEdit(self)
        self.textbox52.move(120, 560)
        self.textbox52.resize(50, 20)
        self.textbox52.setText("0.4")
        self.textbox52.setToolTip('Fraction of all design domains masses to be achieved;\n'
                                  'between 0 and 1.')

        # generate conf. file button
        button21 = QPushButton('Generate conf. file', self)
        button21.setToolTip('Writes configuration file with optimization parameters.')
        button21.move(10, 600)
        button21.clicked.connect(self.on_click21)

        # edit conf. file button
        button22 = QPushButton('Edit conf. file', self)
        button22.setToolTip('Opens configuration file for hand modifications.')
        button22.move(10, 630)
        button22.clicked.connect(self.on_click22)

        # run optimization button
        button23 = QPushButton('Run optimization', self)
        button23.setToolTip('Writes configuration file and runs optimization.')
        button23.move(10, 660)
        button23.clicked.connect(self.on_click23)

        # generate conf file and run optimization button
        button24 = QPushButton('Generate conf.\nfile and run\noptimization', self)
        button24.setToolTip('Writes configuration file and runs optimization.')
        button24.move(120, 600)
        button24.resize(100, 90)
        button24.clicked.connect(self.on_click24)

        # help buttons
        label41 = QLabel('Help', self)
        label41.move(440, 560)

        button31 = QPushButton('Example', self)
        button31.setToolTip('https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD')
        button31.move(440, 590)
        # button31.resize(80, 50)
        button31.clicked.connect(self.on_click31)

        button32 = QPushButton('Conf. comments', self)
        button32.setToolTip('https://github.com/fandaL/beso/blob/master/beso_conf.py')
        button32.move(440, 620)
        # button32.resize(80, 50)
        button32.clicked.connect(self.on_click32)

        button33 = QPushButton('Close', self)
        button33.move(440, 690)
        # button33.resize(80, 50)
        button33.clicked.connect(self.on_click33)

        # open log file
        button40 = QPushButton('Open log file', self)
        button40.setToolTip('Opens log file in your text editor.\n'
                            '(Does not refresh automatically.)')
        button40.move(10, 690)
        button40.clicked.connect(self.on_click40)

        self.on_click1()  # first update
        self.show()

    # @pyqtSlot()
    def on_click(self):
        ex2 = SelectFile()
        self.show()
        self.textbox_file_name.setText(self.inp_file)

    def on_click1(self):
        # get material objects
        self.materials = []
        self.thicknesses = []
        try:
            App.ActiveDocument.Objects
        except AttributeError:
            App.newDocument("Unnamed")
            print("Warning: Missing active document with FEM analysis. New document have been created.")
        for obj in App.ActiveDocument.Objects:
            if obj.Name[:23] == "MechanicalSolidMaterial":
                self.materials.append(obj)
            elif obj.Name[:13] == "MaterialSolid":
                self.materials.append(obj)
            elif obj.Name[:13] == "SolidMaterial":
                self.materials.append(obj)
            elif obj.Name[:17] == "ElementGeometry2D":
                self.thicknesses.append(obj)
        # update materials combo boxes
        self.combo.clear()
        self.combo.addItem("None")
        self.combo1.clear()
        self.combo1.addItem("None")
        self.combo2.clear()
        self.combo2.addItem("None")
        self.combo0t.clear()
        self.combo0t.addItem("None")
        self.combo1t.clear()
        self.combo1t.addItem("None")
        self.combo2t.clear()
        self.combo2t.addItem("None")
        self.widget.clear()
        self.widget.addItem("All defined")
        self.widget.addItem("Domain 0")
        self.widget.addItem("Domain 1")
        self.widget.addItem("Domain 2")
        self.widget.setCurrentItem(self.widget.item(0))
        self.widget1.clear()
        self.widget1.addItem("All defined")
        self.widget1.addItem("Domain 0")
        self.widget1.addItem("Domain 1")
        self.widget1.addItem("Domain 2")
        self.widget1.setCurrentItem(self.widget1.item(0))
        self.widget2.clear()
        self.widget2.addItem("All defined")
        self.widget2.addItem("Domain 0")
        self.widget2.addItem("Domain 1")
        self.widget2.addItem("Domain 2")
        self.widget2.setCurrentItem(self.widget2.item(0))
        for mat in self.materials:
            self.combo.addItem(mat.Label)
            self.combo1.addItem(mat.Label)
            self.combo2.addItem(mat.Label)
        if self.materials:
            self.combo.setCurrentIndex(1)
        for th in self.thicknesses:
            self.combo0t.addItem(th.Label)
            self.combo1t.addItem(th.Label)
            self.combo2t.addItem(th.Label)

    def on_click21(self):
        """Overwrite beso_conf.py file in the macro directory"""

        file_name = os.path.split(self.textbox_file_name.text())[1]
        path = os.path.split(self.textbox_file_name.text())[0]

        fea = ccxtools.FemToolsCcx()
        fea.setup_ccx()
        path_calculix = fea.ccx_binary

        optimization_base = self.combo51.currentText()

        elset_id = self.combo.currentIndex() - 1
        thickness_id = self.combo0t.currentIndex() - 1
        if elset_id != -1:
            if thickness_id != -1:
                elset = self.materials[elset_id].Name + self.thicknesses[thickness_id].Name
            else:  # 0 means None thickness selected
                elset = self.materials[elset_id].Name + "Solid"
            modulus = float(self.materials[elset_id].Material["YoungsModulus"].split()[0])  # MPa
            if self.materials[elset_id].Material["YoungsModulus"].split()[1] != "MPa":
                raise Exception(" units not recognised in " + self.materials[elset_id].Name)
            poisson = float(self.materials[elset_id].Material["PoissonRatio"].split()[0])
            try:
                density = float(self.materials[elset_id].Material["Density"].split()[0]) * 1e-12  # kg/m3 -> t/mm3
                if self.materials[elset_id].Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
                    raise Exception(" units not recognised in " + self.materials[elset_id].Name)
            except KeyError:
                density = 0.
            try:
                conductivity = float(self.materials[elset_id].Material["ThermalConductivity"].split()[0])  # W/m/K
                if self.materials[elset_id].Material["ThermalConductivity"].split()[1] != "W/m/K":
                    raise Exception(" units not recognised in " + self.materials[elset_id].Name)
            except KeyError:
                conductivity = 0.
            try:
                if self.materials[elset_id].Material["ThermalExpansionCoefficient"].split()[1] == "um/m/K":
                    expansion = float(self.materials[elset_id].Material["ThermalExpansionCoefficient"].split()[
                                       0]) * 1e-6  # um/m/K -> mm/mm/K
                elif self.materials[elset_id].Material["ThermalExpansionCoefficient"].split()[1] == "m/m/K":
                    expansion = float(self.materials[elset_id].Material["ThermalExpansionCoefficient"].split()[
                                       0])  # m/m/K -> mm/mm/K
                else:
                    raise Exception(" units not recognised in " + self.materials[elset_id].Name)
            except KeyError:
                expansion = 0.
            try:
                specific_heat = float(self.materials[elset_id].Material["SpecificHeat"].split()[
                                      0]) * 1e6  #  J/kg/K -> mm^2/s^2/K
                if self.materials[elset_id].Material["SpecificHeat"].split()[1] != "J/kg/K":
                    raise Exception(" units not recognised in " + self.materials[elset_id].Name)
            except KeyError:
                specific_heat = 0.
            if thickness_id != -1:
                thickness = str(self.thicknesses[thickness_id].Thickness).split()[0]  # mm
                if str(self.thicknesses[thickness_id].Thickness).split()[1] != "mm":
                    raise Exception(" units not recognised in " + self.thicknesses[thickness_id].Name)
            else:
                thickness = 0.
            optimized = self.checkbox.isChecked()
            if self.textbox.text():
                von_mises = float(self.textbox.text())
            else:
                von_mises = 0.

        elset_id1 = self.combo1.currentIndex() - 1
        thickness_id1 = self.combo1t.currentIndex() - 1
        if elset_id1 != -1:
            if thickness_id1 != -1:
                elset1 = self.materials[elset_id1].Name + self.thicknesses[thickness_id1].Name
            else:  # 0 means None thickness selected
                elset1 = self.materials[elset_id1].Name + "Solid"
            modulus1 = float(self.materials[elset_id1].Material["YoungsModulus"].split()[0])  # MPa
            if self.materials[elset_id1].Material["YoungsModulus"].split()[1] != "MPa":
                raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
            poisson1 = float(self.materials[elset_id1].Material["PoissonRatio"].split()[0])
            try:
                density1 = float(self.materials[elset_id1].Material["Density"].split()[0]) * 1e-12  # kg/m3 -> t/mm3
                if self.materials[elset_id1].Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
                    raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
            except KeyError:
                density1 = 0.
            try:
                conductivity1 = float(self.materials[elset_id1].Material["ThermalConductivity"].split()[0])  # W/m/K
                if self.materials[elset_id1].Material["ThermalConductivity"].split()[1] != "W/m/K":
                    raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
            except KeyError:
                conductivity1 = 0.
            try:
                if self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[1] == "um/m/K":
                    expansion1 = float(self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[
                                       0]) * 1e-6  # um/m/K -> mm/mm/K
                elif self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[1] == "m/m/K":
                    expansion1 = float(self.materials[elset_id1].Material["ThermalExpansionCoefficient"].split()[
                                       0])  # m/m/K -> mm/mm/K
                else:
                    raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
            except KeyError:
                expansion1 = 0.
            try:
                specific_heat1 = float(self.materials[elset_id1].Material["SpecificHeat"].split()[
                                       0]) * 1e6  #  J/kg/K -> mm^2/s^2/K
                if self.materials[elset_id1].Material["SpecificHeat"].split()[1] != "J/kg/K":
                    raise Exception(" units not recognised in " + self.materials[elset_id1].Name)
            except KeyError:
                specific_heat1 = 0.
            if thickness_id1 != -1:
                thickness1 = str(self.thicknesses[thickness_id1].Thickness).split()[0]  # mm
                if str(self.thicknesses[thickness_id1].Thickness).split()[1] != "mm":
                    raise Exception(" units not recognised in " + self.thicknesses[thickness_id1].Name)
            else:
                thickness1 = 0.
            optimized1 = self.checkbox1.isChecked()
            if self.textbox1.text():
                von_mises1 = float(self.textbox1.text())
            else:
                von_mises1 = 0.

        elset_id2 = self.combo2.currentIndex() - 1
        thickness_id2 = self.combo2t.currentIndex() - 1
        if elset_id2 != -1:
            if thickness_id2 != -1:
                elset2 = self.materials[elset_id2].Name + self.thicknesses[thickness_id2].Name
            else:  # 0 means None thickness selected
                else2t = self.materials[elset_id2].Name + "Solid"
            modulus2 = float(self.materials[elset_id2].Material["YoungsModulus"].split()[0])  # MPa
            if self.materials[elset_id2].Material["YoungsModulus"].split()[1] != "MPa":
                raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
            poisson2 = float(self.materials[elset_id2].Material["PoissonRatio"].split()[0])
            try:
                density2 = float(self.materials[elset_id2].Material["Density"].split()[0]) * 1e-12  # kg/m3 -> t/mm3
                if self.materials[elset_id2].Material["Density"].split()[1] not in ["kg/m^3", "kg/m3"]:
                    raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
            except KeyError:
                density2 = 0.
            try:
                conductivity2 = float(self.materials[elset_id2].Material["ThermalConductivity"].split()[0])  # W/m/K
                if self.materials[elset_id2].Material["ThermalConductivity"].split()[1] != "W/m/K":
                    raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
            except KeyError:
                conductivity2 = 0.
            try:
                if self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[1] == "um/m/K":
                    expansion2 = float(self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[
                                       0]) * 1e-6  # um/m/K -> mm/mm/K
                elif self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[1] == "m/m/K":
                    expansion2 = float(self.materials[elset_id2].Material["ThermalExpansionCoefficient"].split()[
                                       0])  # m/m/K -> mm/mm/K
                else:
                    raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
            except KeyError:
                expansion2 = 0.
            try:
                specific_heat2 = float(self.materials[elset_id2].Material["SpecificHeat"].split()[
                                       0]) * 1e6  #  J/kg/K -> mm^2/s^2/K
                if self.materials[elset_id2].Material["SpecificHeat"].split()[1] != "J/kg/K":
                    raise Exception(" units not recognised in " + self.materials[elset_id2].Name)
            except KeyError:
                specific_heat2 = 0.
            if thickness_id2 != -1:
                thickness2 = str(self.thicknesses[thickness_id2].Thickness).split()[0]  # mm
                if str(self.thicknesses[thickness_id2].Thickness).split()[1] != "mm":
                    raise Exception(" units not recognised in " + self.thicknesses[thickness_id2].Name)
            else:
                thickness2 = 0.
            optimized2 = self.checkbox2.isChecked()
            if self.textbox2.text():
                von_mises2 = float(self.textbox2.text())
            else:
                von_mises2 = 0.

        with open(os.path.join(self.beso_dir, "beso_conf.py"), "w") as f:
            f.write("# This is the configuration file with input parameters. It will be executed as python commands\n")
            f.write("# Written by beso_fc_gui.py at {}\n".format(datetime.datetime.now()))
            f.write("\n")
            f.write("path_calculix = '{}'\n".format(path_calculix))
            f.write("path = '{}'\n".format(path))
            f.write("file_name = '{}'\n".format(file_name))
            f.write("\n")

            if elset_id != -1:
                f.write("elset_name = '{}'\n".format(elset))
                f.write("domain_optimized[elset_name] = {}\n".format(optimized))
                f.write("domain_density[elset_name] = [{}, {}]\n".format(density * 1e-6, density))
                if thickness:
                    f.write("domain_thickness[elset_name] = [{}, {}]\n".format(thickness, thickness))
                if von_mises:
                    f.write("domain_FI[elset_name] = [[('stress_von_Mises', {:.6})],\n".format(von_mises * 1e6))
                    f.write("                         [('stress_von_Mises', {:.6})]]\n".format(von_mises))
                f.write("domain_material[elset_name] = ['*ELASTIC\\n{:.6}, {}\\n*DENSITY\\n{:.6}\\n*CONDUCTIVITY\\n"
                        "{:.6}\\n*EXPANSION\\n{:.6}\\n*SPECIFIC HEAT\\n{:.6}\\n',\n".format(modulus * 1e-6, poisson,
                        density * 1e-6, conductivity * 1e-6, expansion * 1e-6, specific_heat * 1e-6))
                f.write("                               '*ELASTIC\\n{:.6}, {:.6}\\n*DENSITY\\n{:.6}\\n*CONDUCTIVITY\\n"
                        "{:.6}\\n*EXPANSION\\n{:.6}\\n*SPECIFIC HEAT\\n{:.6}\\n']\n".format(modulus, poisson, density,
                         conductivity, expansion, specific_heat))
                f.write("\n")
            if elset_id1 != -1:
                f.write("elset_name = '{}'\n".format(elset1))
                f.write("domain_optimized[elset_name] = {}\n".format(optimized1))
                f.write("domain_density[elset_name] = [{}, {}]\n".format(density1 * 1e-6, density1))
                if thickness1:
                    f.write("domain_thickness[elset_name] = [{}, {}]\n".format(thickness1, thickness1))
                if von_mises1:
                    f.write("domain_FI[elset_name] = [[('stress_von_Mises', {:.6})],\n".format(von_mises1 * 1e6))
                    f.write("                         [('stress_von_Mises', {:.6})]]\n".format(von_mises1))
                f.write("domain_material[elset_name] = ['*ELASTIC\\n{:.6}, {:.6}\\n*DENSITY\\n{:.6}\\n*CONDUCTIVITY"
                        "\\n{:.6}\\n*EXPANSION\\n{:.6}\\n*SPECIFIC HEAT\\n{:.6}\\n',\n".format(modulus1 * 1e-6,
                        poisson1, density1 * 1e-6, conductivity1 * 1e-6, expansion1 * 1e-6, specific_heat1 * 1e-6))
                f.write("                               '*ELASTIC\\n{:.6}, {:.6}\\n*DENSITY\\n{:.6}\\n*CONDUCTIVITY\\n"
                        "{:.6}\\n" "*EXPANSION\\n{:.6}\\n*SPECIFIC HEAT\\n{:.6}\\n']\n".format(modulus1, poisson1,
                         density1, conductivity1, expansion1, specific_heat1))
                f.write("\n")
            if elset_id2 != -1:
                f.write("elset_name = '{}'\n".format(elset2))
                f.write("domain_optimized[elset_name] = {}\n".format(optimized2))
                f.write("domain_density[elset_name] = [{}, {}]\n".format(density2 * 1e-6, density2))
                if thickness2:
                    f.write("domain_thickness[elset_name] = [{}, {}]\n".format(thickness2, thickness2))
                if von_mises2:
                    f.write("domain_FI[elset_name] = [[('stress_von_Mises', {:.6})],\n".format(von_mises2 * 1e6))
                    f.write("                         [('stress_von_Mises', {:.6})]]\n".format(von_mises2))
                f.write("domain_material[elset_name] = ['*ELASTIC\\n{:.6}, {:.6}\\n*DENSITY\\n{:.6}\\n*CONDUCTIVITY"
                        "\\n{:.6}\\n*EXPANSION\\n{:.6}\\n*SPECIFIC HEAT\\n{:.6}\\n',\n".format(modulus2 * 1e-6,
                        poisson2, density2 * 1e-6, conductivity2 * 1e-6, expansion2 * 1e-6, specific_heat2 * 1e-6))
                f.write("                               '*ELASTIC\\n{:.6}, {:.6}\\n*DENSITY\\n{:.6}\\n*CONDUCTIVITY\\n"
                        "{:.6}\\n*EXPANSION\\n{:.6}\\n*SPECIFIC HEAT\\n{:.6}\\n']\n".format(modulus2, poisson2,
                         density2, conductivity2, expansion2, specific_heat2))
                f.write("\n")
            f.write("mass_goal_ratio = " + self.textbox52.text())
            f.write("\n")

            f.write("filter_list = [")
            filter = self.combo6.currentText()
            range = self.textbox6.text()
            direction = self.textbox9.text()
            selection = [item.text() for item in self.widget.selectedItems()]
            filter_domains = []
            if "All defined" not in selection:
                if "Domain 0" in selection:
                    filter_domains.append(elset)
                if "Domain 1" in selection:
                    filter_domains.append(elset1)
                if "Domain 2" in selection:
                    filter_domains.append(elset2)
            if filter == "simple":
                f.write("['simple', {}".format(range))
                for dn in filter_domains:
                    f.write(", '{}'".format(dn))
                f.write("],\n")
            elif filter == "casting":
                f.write("['casting', {}, ({})".format(range, direction))
                for dn in filter_domains:
                    f.write(", '{}'".format(dn))
                f.write("],\n")

            filter1 = self.combo7.currentText()
            range1 = self.textbox7.text()
            direction1 = self.textbox10.text()
            selection = [item.text() for item in self.widget1.selectedItems()]
            filter_domains1 = []
            if "All defined" not in selection:
                if "Domain 0" in selection:
                    filter_domains1.append(elset)
                if "Domain 1" in selection:
                    filter_domains1.append(elset1)
                if "Domain 2" in selection:
                    filter_domains1.append(elset2)
            if filter1 == "simple":
                f.write("               ['simple', {}".format(range1))
                for dn in filter_domains1:
                    f.write(", '{}'".format(dn))
                f.write("],\n")
            elif filter1 == "casting":
                f.write("               ['casting', {}, ({})".format(range1, direction1))
                for dn in filter_domains1:
                    f.write(", '{}'".format(dn))
                f.write("],\n")

            filter2 = self.combo8.currentText()
            range2 = self.textbox8.text()
            direction2 = self.textbox11.text()
            selection = [item.text() for item in self.widget2.selectedItems()]
            filter_domains2 = []
            if "All defined" not in selection:
                if "Domain 0" in selection:
                    filter_domains2.append(elset)
                if "Domain 1" in selection:
                    filter_domains2.append(elset1)
                if "Domain 2" in selection:
                    filter_domains2.append(elset2)
            if filter2 == "simple":
                f.write("               ['simple', {}".format(range2))
                for dn in filter_domains2:
                    f.write(", '{}'".format(dn))
                f.write("],\n")
            elif filter2 == "casting":
                f.write("               ['casting', {}, ({})".format(range2, direction2))
                for dn in filter_domains2:
                    f.write(", '{}'".format(dn))
                f.write("],\n")
            f.write("               ]\n")
            f.write("\n")

            f.write("optimization_base = '{}'\n".format(optimization_base))
            f.write("\n")

            slider_position = self.slider.value()
            if slider_position == 1:
                f.write("mass_addition_ratio = 0.01\n")
                f.write("mass_removal_ratio = 0.02\n")
            if slider_position == 2:
                f.write("mass_addition_ratio = 0.015\n")
                f.write("mass_removal_ratio = 0.03\n")
            if slider_position == 3:
                f.write("mass_addition_ratio = 0.03\n")
                f.write("mass_removal_ratio = 0.06\n")
            f.write("ratio_type = 'relative'\n")
            f.write("\n")

    def on_click22(self):
        """Open beso_conf.py in FreeCAD editor"""
        FreeCADGui.insert(os.path.join(self.beso_dir, "beso_conf.py"))

    def on_click23(self):
        """"Run optimization"""
        # run in own thread (not freezing FreeCAD):      needs also to comment "plt.show()" on the end of beso_main.py
        # self.optimization_thread = RunOptimization("beso_main")
        # self.optimization_thread.start()

        # run in foreground (freeze FreeCAD)
        exec(open(os.path.join(beso_gui.beso_dir, "beso_main.py")).read())

    def on_click24(self):
        self.on_click21()  # generate beso_conf.py
        self.on_click23()  # run optimization

    def on_click31(self):
        webbrowser.open_new_tab("https://github.com/fandaL/beso/wiki/Example-4:-GUI-in-FreeCAD")

    def on_click32(self):
        webbrowser.open_new_tab("https://github.com/fandaL/beso/blob/master/beso_conf.py")

    def on_click33(self):
        self.close()

    def on_click40(self):
        """Open log file"""
        if self.textbox_file_name.text() in ["None analysis file selected", ""]:
            print("None analysis file selected")
        else:
            log_file = os.path.normpath(self.textbox_file_name.text()[:-4] + ".log")
            webbrowser.open(log_file)

    def on_change(self):
        if self.combo.currentText() == "None":
            self.combo0t.setEnabled(False)
            self.checkbox.setEnabled(False)
            self.textbox.setEnabled(False)
        else:
            self.combo0t.setEnabled(True)
            self.checkbox.setEnabled(True)
            self.textbox.setEnabled(True)

    def on_change1(self):
        if self.combo1.currentText() == "None":
            self.combo1t.setEnabled(False)
            self.checkbox1.setEnabled(False)
            self.textbox1.setEnabled(False)
        else:
            self.combo1t.setEnabled(True)
            self.checkbox1.setEnabled(True)
            self.textbox1.setEnabled(True)

    def on_change2(self):
        if self.combo2.currentText() == "None":
            self.combo2t.setEnabled(False)
            self.checkbox2.setEnabled(False)
            self.textbox2.setEnabled(False)
        else:
            self.combo2t.setEnabled(True)
            self.checkbox2.setEnabled(True)
            self.textbox2.setEnabled(True)

    def on_change6(self):
        if self.combo6.currentText() == "None":
            self.textbox6.setEnabled(False)
            self.textbox9.setEnabled(False)
            self.widget.setEnabled(False)
        elif self.combo6.currentText() == "casting":
            self.textbox6.setEnabled(True)
            self.textbox9.setEnabled(True)
            self.widget.setEnabled(True)
        else:
            self.textbox6.setEnabled(True)
            self.textbox9.setEnabled(False)
            self.widget.setEnabled(True)

    def on_change7(self):
        if self.combo7.currentText() == "None":
            self.textbox7.setEnabled(False)
            self.textbox10.setEnabled(False)
            self.widget1.setEnabled(False)
        elif self.combo7.currentText() == "casting":
            self.textbox7.setEnabled(True)
            self.textbox10.setEnabled(True)
            self.widget1.setEnabled(True)
        else:
            self.textbox7.setEnabled(True)
            self.textbox10.setEnabled(False)
            self.widget1.setEnabled(True)

    def on_change8(self):
        if self.combo8.currentText() == "None":
            self.textbox8.setEnabled(False)
            self.textbox11.setEnabled(False)
            self.widget2.setEnabled(False)
        elif self.combo8.currentText() == "casting":
            self.textbox8.setEnabled(True)
            self.textbox11.setEnabled(True)
            self.widget2.setEnabled(True)
        else:
            self.textbox8.setEnabled(True)
            self.textbox11.setEnabled(False)
            self.widget2.setEnabled(True)


class SelectFile(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Select analysis file *.inp'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        beso_gui.inp_file = self.openFileNameDialog()
        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        inp_file, _ = QFileDialog.getOpenFileName(self, "Select file", "", "Analysis Files (*.inp);;All Files (*)",
                                                  options=options)
        return inp_file


class RunOptimization(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        exec(open(os.path.join(beso_gui.beso_dir, "beso_main.py")).read())


if __name__ == '__main__':
    ex = beso_gui()
    ex.exec_()
