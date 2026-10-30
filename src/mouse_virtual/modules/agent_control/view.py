"""Desktop-agent panel. UIA targets are chosen explicitly, never inferred."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QLineEdit,QPushButton,QLabel,QPlainTextEdit,QFormLayout

def build_agent_page(host):
    page=QWidget()
    layout=QVBoxLayout(page)
    layout.addWidget(QLabel("Agente IA — Controles de escritorio"))
    layout.addWidget(QLabel("Selecciona una ventana, inspecciona controles accesibles y autoriza cada operación."))
    form=QFormLayout()
    host.agent_windows=QComboBox()
    host.agent_windows.setObjectName("agentWindows")
    refresh=QPushButton("Actualizar ventanas")
    refresh.clicked.connect(host.agent_refresh_windows)
    row=QHBoxLayout();row.addWidget(host.agent_windows);row.addWidget(refresh)
    form.addRow("Ventana destino",row)
    host.agent_type=QComboBox()
    host.agent_type.addItems(["Edit","Button","Text"])
    form.addRow("Tipo de control",host.agent_type)
    host.agent_id=QComboBox()
    host.agent_id.setEditable(True)
    host.agent_id.setObjectName("agentControlId")
    form.addRow("AutomationId",host.agent_id)
    host.agent_text=QLineEdit()
    host.agent_text.setObjectName("agentText")
    host.agent_text.setPlaceholderText("Texto que deseas escribir")
    form.addRow("Texto",host.agent_text)
    layout.addLayout(form)
    buttons=QHBoxLayout()
    for name,fn in [("Inspeccionar",host.agent_inspect),("Escribir",host.agent_fill),
                    ("Invocar botón",host.agent_invoke),("Leer control",host.agent_read)]:
        action=QPushButton(name);action.clicked.connect(fn);buttons.addWidget(action)
    layout.addLayout(buttons)
    host.agent_output=QPlainTextEdit()
    host.agent_output.setObjectName("agentOutput")
    host.agent_output.setReadOnly(True)
    layout.addWidget(host.agent_output)
    return page
