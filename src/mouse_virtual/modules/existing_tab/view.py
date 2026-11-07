"""Qt page layout for the existing-browser tab workspace."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QPlainTextEdit, QSpinBox, QFormLayout, QComboBox,
)
from .paths import EXTENSION_DIR

class ExistingTabViewMixin:
    def existing_tab_page(self):
        pane = QWidget()
        col = QVBoxLayout(pane)
        header = QLabel("Pestaña de Chrome existente — Mouse Virtual")
        header.setObjectName("sectionTitle")
        col.addWidget(header)
        subtitle = QLabel(
            "Usa un puntero propio dentro de la pestaña seleccionada, sin mover el mouse físico."
        )
        subtitle.setWordWrap(True)
        col.addWidget(subtitle)

        row = QHBoxLayout()
        btn_start = QPushButton("Iniciar puente local")
        btn_start.clicked.connect(self.tab_start_bridge)
        row.addWidget(btn_start)
        copy = QPushButton("Copiar código de emparejamiento")
        copy.clicked.connect(self.tab_copy_token)
        row.addWidget(copy)
        col.addLayout(row)
        extension = QLabel(f"Extensión de Chrome: {EXTENSION_DIR}")
        extension.setWordWrap(True)
        extension.setTextInteractionFlags(extension.textInteractionFlags() |
                                          extension.textInteractionFlags().TextSelectableByMouse)
        col.addWidget(extension)
        col.addWidget(QLabel(
            "Cárgala una sola vez en el Chrome que ya utilizas; después pulsa "
            "'Controlar esta pestaña' desde esa pestaña."
        ))

        self.tab_status = QLabel("Desconectado")
        self.tab_status.setWordWrap(True)
        col.addWidget(self.tab_status)
        form = QFormLayout()
        self.tab_x = QSpinBox()
        self.tab_x.setRange(0, 16384)
        self.tab_x.setValue(250)
        self.tab_y = QSpinBox()
        self.tab_y.setRange(0, 16384)
        self.tab_y.setValue(230)
        coords = QHBoxLayout()
        coords.addWidget(self.tab_x)
        coords.addWidget(self.tab_y)
        form.addRow("Puntero virtual (X, Y)", coords)
        self.tab_text = QLineEdit()
        self.tab_text.setPlaceholderText("Texto para escribir en la página")
        form.addRow("Escritura", self.tab_text)
        self.tab_url = QLineEdit()
        self.tab_url.setPlaceholderText("https://sitio-autorizado.example")
        form.addRow("Navegar a", self.tab_url)
        self.tab_selector = QLineEdit()
        self.tab_selector.setPlaceholderText("Selector CSS, por ejemplo #search")
        form.addRow("Elemento de página", self.tab_selector)
        self.tab_file = QLineEdit()
        self.tab_file.setPlaceholderText("Ruta de un archivo de video autorizado")
        form.addRow("Video", self.tab_file)
        self.tab_target_url = QLineEdit()
        self.tab_target_url.setPlaceholderText("https://sitio/autorizado — pestaña inactiva")
        form.addRow("Cambiar pestaña", self.tab_target_url)
        self.tab_target_id = QSpinBox()
        self.tab_target_id.setRange(1, 2147483647)
        form.addRow("ID de pestaña", self.tab_target_id)
        self.tab_tabs = QComboBox()
        self.tab_tabs.addItem("Pulsa «Ver todas las pestañas» para actualizar", None)
        self.tab_tabs.currentIndexChanged.connect(self.tab_choose_from_list)
        form.addRow("Pestañas disponibles", self.tab_tabs)
        col.addLayout(form)

        first = QHBoxLayout()
        for caption, fn in [
            ("Estado", self.tab_check_status),
            ("Capturar", lambda: self.tab_run({"action": "screenshot"})),
            ("Mover", lambda: self.tab_run({"action": "move",
                                           "x": self.tab_x.value(), "y": self.tab_y.value()})),
            ("Clic", lambda: self.tab_run({"action": "click",
                                          "x": self.tab_x.value(), "y": self.tab_y.value()})),
            ("Escribir", lambda: self.tab_run({"action": "type", "text": self.tab_text.text()})),
        ]:
            button = QPushButton(caption)
            button.clicked.connect(fn)
            first.addWidget(button)
        col.addLayout(first)
        second = QHBoxLayout()
        for caption, fn in [
            ("Ir a URL", self.tab_navigate),
            ("Inspeccionar", lambda: self.tab_run({"action": "inspect"})),
            ("Clic por selector", lambda: self.tab_run(
                {"action": "dom.click", "selector": self.tab_selector.text()})),
            ("Llenar campo", lambda: self.tab_run(
                {"action": "dom.fill", "selector": self.tab_selector.text(),
                 "text": self.tab_text.text()})),
            ("Adjuntar video", self.tab_attach_file),
            ("Cambiar pestaña", self.tab_select_window_tab),
        ]:
            button = QPushButton(caption)
            button.clicked.connect(fn)
            second.addWidget(button)
        col.addLayout(second)
        workspace_buttons = QHBoxLayout()
        for caption, fn in [
            ("Ver todas las pestañas", lambda: self.tab_run({"action": "tab.list"})),
            ("Crear grupo de trabajo", self.tab_create_workspace),
            ("Abrir pestaña en grupo", self.tab_open_workspace),
        ]:
            button = QPushButton(caption)
            button.clicked.connect(fn)
            workspace_buttons.addWidget(button)
        col.addLayout(workspace_buttons)
        choose_buttons = QHBoxLayout()
        for caption, fn in [
            ("Usar pestaña del grupo", self.tab_select_workspace),
            ("Elegir otra pestaña", self.tab_select_by_id),
            ("Cerrar pestaña del grupo", self.tab_close_workspace),
        ]:
            button = QPushButton(caption)
            button.clicked.connect(fn)
            choose_buttons.addWidget(button)
        col.addLayout(choose_buttons)
        self.tab_output = QPlainTextEdit()
        self.tab_output.setObjectName("existingTabLog")
        self.tab_output.setReadOnly(True)
        col.addWidget(self.tab_output, 1)
        disconnect = QPushButton("Detener puente local")
        disconnect.clicked.connect(self.tab_stop_bridge)
        col.addWidget(disconnect)
        return pane
