from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton

class AddressFormatterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Address Formatter")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Layer selection
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel("Layer:"))
        self.layerCombo = QComboBox()
        layer_layout.addWidget(self.layerCombo)
        layout.addLayout(layer_layout)
        
        # Input field selection
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input Field:"))
        self.inputFieldCombo = QComboBox()
        input_layout.addWidget(self.inputFieldCombo)
        layout.addLayout(input_layout)
        
        # Output field
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Field:"))
        self.outputFieldEdit = QLineEdit("formatted_address")
        output_layout.addWidget(self.outputFieldEdit)
        layout.addLayout(output_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")
        button_layout.addWidget(self.okButton)
        button_layout.addWidget(self.cancelButton)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.layerCombo.currentIndexChanged.connect(self.update_field_combos)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
    
    def update_field_combos(self):
        layer = self.layerCombo.currentData()
        self.inputFieldCombo.clear()
        
        if layer:
            fields = layer.fields()
            for field in fields:
                self.inputFieldCombo.addItem(field.name())