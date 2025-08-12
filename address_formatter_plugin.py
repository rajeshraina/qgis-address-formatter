import os
import re
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QAction, QDialog, QMessageBox, QVBoxLayout, 
                                QHBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit)
from qgis.core import QgsProject, QgsVectorLayer, QgsField
from qgis.utils import iface

class AddressFormatterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Address Formatter")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Layer selection
        layout.addWidget(QLabel("Select Layer:"))
        self.layer_combo = QComboBox()
        layout.addWidget(self.layer_combo)
        
        # Address field selection
        layout.addWidget(QLabel("Select Address Field:"))
        self.field_combo = QComboBox()
        layout.addWidget(self.field_combo)
        
        # Output field
        layout.addWidget(QLabel("Output Field Name:"))
        self.output_field = QLineEdit("formatted_address")
        layout.addWidget(self.output_field)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("Format Addresses")
        self.btn_cancel = QPushButton("Cancel")
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Populate layers
        self.populate_layers()
        
        # Connect signals
        self.layer_combo.currentIndexChanged.connect(self.populate_fields)
        self.btn_run.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
    
    def populate_layers(self):
        self.layer_combo.clear()
        layers = QgsProject.instance().mapLayers().values()
        self.vector_layers = [layer for layer in layers if isinstance(layer, QgsVectorLayer)]
        for layer in self.vector_layers:
            self.layer_combo.addItem(layer.name(), layer)
        
        if self.vector_layers:
            self.populate_fields()
    
    def populate_fields(self):
        self.field_combo.clear()
        layer = self.layer_combo.currentData()
        if layer:
            for field in layer.fields():
                self.field_combo.addItem(field.name())

class AddressFormatterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr('&Address Formatter')
        self.dialog = None

    def tr(self, message):
        return QCoreApplication.translate('AddressFormatter', message)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr('Format Addresses'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        
        self.actions.append(action)
        return action

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr('&Address Formatter'), action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if not self.dialog:
            self.dialog = AddressFormatterDialog()
        
        if self.dialog.exec_():
            layer = self.dialog.layer_combo.currentData()
            address_field = self.dialog.field_combo.currentText()
            output_field = self.dialog.output_field.text().strip()
            
            if not layer or not address_field or not output_field:
                QMessageBox.warning(None, "Error", "All fields are required")
                return
            
            self.format_layer_addresses(layer, address_field, output_field)

    def to_title_case(self, s):
        if not isinstance(s, str):
            return ''
        known_abbreviations = ['KFC', 'SBI', 'PNB', 'HDFC', 'ICICI', 'LIC', 'IDBI', 'DTDC', 
                             'ATM', 'PSU', 'IOB', 'HSBC', 'BOB', 'RBI', 'ONGC', 'BHEL', 
                             'KS', 'AD', 'KG']
        
        def title_case_word(word):
            upper = word.upper()
            if upper == 'NO': return 'No'
            if upper == 'TO': return 'to'
            if upper in known_abbreviations or (len(upper) == 2 and upper.isupper()):
                return upper
            return word[0].upper() + word[1:].lower()
        
        return ' '.join(title_case_word(word) for word in s.split())

    def normalize_number_identifiers(self, s):
        s = re.sub(r'\b(\d+)([a-z])\b', lambda m: f"{m.group(1)}{m.group(2).upper()}", s, flags=re.IGNORECASE)
        s = re.sub(r'\b([\d\/\-]+)([a-z])\b', lambda m: f"{m.group(1)}{m.group(2).upper()}", s, flags=re.IGNORECASE)
        s = re.sub(r'(\d)([a-z])', lambda m: f"{m.group(1)}{m.group(2).upper()}", s, flags=re.IGNORECASE)
        return s

    def get_indian_cities_and_states(self):
        return {
            'cities': ['Bangalore', 'Chennai', 'Bengaluru', 'Hyderabad', 'Mumbai', 'Delhi', 
                      'Gurugram', 'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 
                      'Kanpur', 'Nagpur', 'Visakhapatnam', 'Indore', 'Thane', 'Bhopal', 
                      'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 
                      'Faridabad', 'Meerut', 'Rajkot', 'Kalyan', 'Vasai', 'Varanasi', 
                      'Srinagar', 'Aurangabad', 'Dhanbad', 'Kozhikode', 'Jamjodhpur'],
            'states': ['Karnataka', 'Tamil Nadu', 'Maharashtra', 'Andhra Pradesh', 'Telangana', 
                      'Kerala', 'Delhi', 'West Bengal', 'Uttar Pradesh', 'Rajasthan', 
                      'Gujarat', 'Madhya Pradesh', 'Punjab', 'Bihar', 'Odisha', 'Assam', 
                      'Chhattisgarh', 'Jharkhand', 'Haryana', 'Jammu and Kashmir']
        }

    def clean_address_input(self, raw):
        if not isinstance(raw, str):
            return ''
            
        raw = re.sub(r'\n+', ', ', raw).upper()
        
        abbreviation_map = {
            'CPLX': 'COMPLEX', 'CMPLX': 'COMPLEX', 'APT': 'APARTMENT',
            'RESI': 'RESIDENCY', 'PLZ': 'PLAZA', 'TWR': 'TOWER',
            'CTR': 'CENTER', 'CTRE': 'CENTRE', 'NVS': 'NIVAS',
            'NVAS': 'NIVAS', 'BLDG': 'BUILDING'
        }
        
        for abbr, full in abbreviation_map.items():
            raw = re.sub(rf'\b{abbr}\b', full, raw)
        
        raw = re.sub(r'\b(\w+)\s+St[.,]?\b', r'\1 Street', raw, flags=re.IGNORECASE)
        raw = re.sub(r'\b(\w+)\s+Rd[.,]?\b', r'\1 Road', raw, flags=re.IGNORECASE)
        
        replacements = [
            (r'\s*#\s*(\d+)', r' No \1'),
            (r'village|district|mandal|taluk', '', re.IGNORECASE),
            (r'\bflr\b', 'Floor', re.IGNORECASE),
            (r'\b(\d{1,2})(st|nd|rd|th)?\s*flr\b', r'\1\2 Floor', re.IGNORECASE),
            (r'\bfirst\s*floor\b', '1st Floor', re.IGNORECASE),
            (r'\bsecond\s*floor\b', '2nd Floor', re.IGNORECASE),
            (r'\bthird\s*floor\b', '3rd Floor', re.IGNORECASE),
            (r'\bfourth\s*floor\b', '4th Floor', re.IGNORECASE),
            (r'\bdoor\s*no\.?\:?\s*', 'Door No ', re.IGNORECASE),
            (r'\bplot\s*no\.?\:?\s*', 'Plot No ', re.IGNORECASE),
            (r'\bunit\s*no\.?\:?\s*', 'Unit No ', re.IGNORECASE),
            (r'\bshop\s*no\.?\:?\s*', 'Shop No ', re.IGNORECASE),
            (r'\bflat\s*no\.?\:?\s*', 'Flat No ', re.IGNORECASE),
            (r'\bmilkat\s*no\.?\:?\s*', 'Milkat No ', re.IGNORECASE),
            (r'\bs\s*no\.?\:?\s*', 'Survey No ', re.IGNORECASE),
            (r'\bsy\s*no\.?\:?\s*', 'Survey No ', re.IGNORECASE),
            (r'\bno\.?\:?\s*', 'No ', re.IGNORECASE),
            (r'\bopp\.?\b', 'Opposite', re.IGNORECASE),
            (r'\bnr\b', 'Near', re.IGNORECASE),
            (r'\bcross\b', 'Cross', re.IGNORECASE),
            (r'\bd no\b', 'Door No', re.IGNORECASE),
            (r'\bh no\b', 'House No', re.IGNORECASE),
            (r'\babv\b', 'Above', re.IGNORECASE),
            (r'\bblw\b', 'Below', re.IGNORECASE),
            (r' ?- ?', '-'),
            (r'\.(?!\d)', ''),
            (r'\:(?!\d)', ''),
            (r'\s*,\s*', ', '),
            (r',+', ','),
            (r'\s+', ' '),
            (r'\s+,', ','),
            (r',+\s*', ', ')
        ]
        
        for pattern, repl, *flags in replacements:
            flags = flags[0] if flags else 0
            raw = re.sub(pattern, repl, raw, flags=flags)
            
        return raw.strip()

    def format_address(self, raw):
        if not raw or not isinstance(raw, str):
            return ''
            
        raw = self.clean_address_input(raw)
        
        # Handle complex number patterns
        raw = re.sub(
            r'((?:House|H|Flat|Plot|Door|Unit|Old|New|Shop|Office|Survey)?\s*No\.?\s*\d+(?:,\s*\d+)*\s*&\s*\d+)',
            lambda m: m.group(0).replace(',', '||'),
            raw,
            flags=re.IGNORECASE
        )
        
        parts = [self.normalize_number_identifiers(p.strip().replace('||', ',')) 
                for p in raw.split(',') if p.strip()]
                
        # Separate state and pincode
        for i in range(len(parts)):
            match = re.match(r'^([A-Za-z\s]+)\s+(\d{6})$', parts[i])
            if match:
                parts[i:i+1] = [match.group(1).strip(), match.group(2)]
        
        identifiers = []
        floor = building = ward_no = street = road = cross = ''
        city = state = pincode = ''
        pn_numbers = []
        extras = []
        locality = []
        landmark_types = {
            'above': [], 'below': [], 'beside': [], 'next': [],
            'opposite': [], 'infront': [], 'behind': [], 'near': []
        }
        
        building_keywords = ['BUILDING','COMPLEX','MANSION','APARTMENT','TOWER','CENTER','CENTRE']
        locality_keywords = ['NAGAR','LAYOUT','COLONY','AREA','BLOCK','EXTENSION']
        
        nz_places = self.get_indian_cities_and_states()
        
        for p in parts:
            upper = p.upper()
            if re.match(r'^\d{6}$', upper):
                pincode = upper
            elif re.match(r'^PN\s*\d+$', upper):
                pn_numbers.append(p)
            elif re.match(r'^WARD\s*NO\.?\s*\d+', upper):
                ward_no = self.to_title_case(p)
            elif re.match(r'^(DOOR|PLOT|OFFICE|OLD|SHOP|UNIT|HOUSE|SURVEY|FLAT|MILKAT)\s*NO', upper):
                identifiers.append(self.to_title_case(p))
            elif re.match(r'^\d[\d\-\/\s&]*[A-Z]*$', upper):
                identifiers.append('No ' + upper)
            elif re.match(r'^(No\.?\s*)?\d[\dA-Za-z\-\/&]*$', upper):
                norm = self.normalize_number_identifiers(re.sub(r'^No\.?\s*', '', upper, flags=re.IGNORECASE))
                identifiers.append('No ' + norm)
            elif 'FLOOR' in upper:
                floor = ', '.join(filter(None, [floor, self.to_title_case(p)]))
            elif any(term in upper for term in ['ABOVE', 'BELOW', 'BESIDE', 'NEXT', 
                                             'OPPOSITE', 'INFRONT', 'BEHIND', 'NEAR']):
                key = next((k for k in landmark_types if k.upper() in upper), None)
                if key:
                    landmark_types[key].append(self.to_title_case(p))
            elif 'CROSS' in upper:
                cross = self.to_title_case(p)
            elif 'STREET' in upper:
                street = self.to_title_case(p)
            elif any(term in upper for term in ['ROAD', 'HIGHWAY', 'MARG']):
                road = self.to_title_case(p)
            elif not building and any(kw in upper for kw in building_keywords):
                building = self.to_title_case(p)
            elif not city and self.to_title_case(p) in nz_places['cities']:
                city = self.to_title_case(p)
            elif not state and self.to_title_case(p) in nz_places['states']:
                state = self.to_title_case(p)
            elif any(kw in upper for kw in locality_keywords):
                locality.append(self.to_title_case(p))
            else:
                extras.append(self.to_title_case(p))
        
        # Sort identifiers by priority
        identifier_priority = [
            'Survey No', 'Katha No', 'Plot No', 'No', 
            'Flat No', 'Unit No', 'House No', 'Door No'
        ]
        
        def get_priority(x):
            for i, p in enumerate(identifier_priority):
                if x.startswith(p):
                    return i
            return len(identifier_priority)
        
        identifiers.sort(key=get_priority)
        
        # Build final identifier
        final_identifier = ''
        if identifiers:
            main = identifiers[0]
            rest = [re.sub(r'^No\s+', '', id) for id in identifiers[1:]]
            if re.match(r'^(Door|Plot|Flat|Shop|Unit|House|Survey)\s+No', main, re.IGNORECASE):
                final_identifier = ', '.join(filter(None, [main] + rest))
            else:
                final_identifier = 'No ' + re.sub(r'^No\s+', '', main)
                if rest:
                    final_identifier += ', ' + ', '.join(rest)
        
        # Build address parts
        address_parts = [
            final_identifier,
            *pn_numbers,
            floor,
            building,
            *[item for sublist in landmark_types.values() for item in sublist],
            cross,
            street,
            road,
            *extras,
            *locality,
            ward_no,
            city,
            state,
            pincode
        ]
        
        return ', '.join(filter(None, address_parts))

    def format_layer_addresses(self, layer, address_field, output_field):
        try:
            # Add output field if needed
            fields = layer.fields()
            if fields.indexOf(output_field) == -1:
                layer.startEditing()
                layer.addAttribute(QgsField(output_field, QVariant.String, len=500))
                layer.commitChanges()
                fields = layer.fields()

            # Process features
            layer.startEditing()
            total = layer.featureCount()
            processed = 0
            
            for feature in layer.getFeatures():
                raw_address = feature[address_field]
                if raw_address:
                    formatted = self.format_address(str(raw_address))
                    feature.setAttribute(output_field, formatted)
                    layer.updateFeature(feature)
                
                processed += 1
                if processed % 10 == 0:
                    progress = int(100 * processed / total)
                    iface.mainWindow().statusBar().showMessage(
                        f"Formatting addresses... {progress}%")

            if layer.commitChanges():
                iface.messageBar().pushSuccess(
                    "Success", 
                    f"Formatted {processed} addresses in '{layer.name()}'")
            else:
                raise Exception("Failed to save changes")

        except Exception as e:
            if layer.isEditable():
                layer.rollBack()
            QMessageBox.critical(None, "Error", str(e))
        finally:
            iface.mainWindow().statusBar().clearMessage()
