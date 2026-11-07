"""Qt interface for a user-paired existing Chrome tab.

ALL remote page operations pass through the local authenticated tab bridge.
No pyautogui, SendInput, global shortcuts or new Chrome profiles are used.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QProcess, QTimer
from .paths import PRIVATE_DIR, TOKEN_FILE, SOURCE_EXTENSION_DIR, EXTENSION_DIR
from .view import ExistingTabViewMixin


def deploy_extension():
    """Stage generic extension assets in user-local storage, outside source Git."""
    EXTENSION_DIR.mkdir(parents=True, exist_ok=True)
    for filename in ("manifest.json", "worker.js", "workspace.js", "popup.html", "popup.js"):
        source = SOURCE_EXTENSION_DIR / filename
        destination = EXTENSION_DIR / filename
        if not source.is_file():
            raise FileNotFoundError(f"Extension file missing: {filename}")
        if not destination.exists() or source.read_bytes() != destination.read_bytes():
            shutil.copy2(source, destination)
    return EXTENSION_DIR


def bridge_is_running():
    try:
        with socket.create_connection(("127.0.0.1", 8765), timeout=0.25):
            return True
    except OSError:
        return False


def worker_python():
    """Use the windowless Python launcher on Windows when available."""
    binary = Path(sys.executable)
    if sys.platform == "win32" and binary.name.lower() == "python.exe":
        pythonw = binary.with_name("pythonw.exe")
        if pythonw.is_file():
            return str(pythonw)
    return str(binary)


class ExistingTabMixin(ExistingTabViewMixin):
    def tab_start_bridge(self):
        self._tab_keep_alive = True
        if getattr(self, "_tab_server", None) is not None and \
                self._tab_server.state() != QProcess.ProcessState.NotRunning:
            self.tab_status.setText("El puente local ya está iniciado.")
            return
        PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            deploy_extension()
        except OSError as exc:
            self.tab_status.setText(f"No se pudo preparar la extensión: {exc}")
            return
        if bridge_is_running():
            self.tab_status.setText("Puente activo en 127.0.0.1:8765; reconexión automática habilitada.")
            self._ensure_tab_watchdog()
            return
        server = QProcess(self)
        self._tab_server = server
        server.setProgram(worker_python())
        server.setArguments([
            "-m", "mouse_virtual.modules.agent_control.tab_bridge", "serve",
            "--token-file", str(TOKEN_FILE),
        ])
        server.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        server.readyReadStandardOutput.connect(self._tab_server_output)
        server.finished.connect(self._tab_server_finished)
        server.start()
        self._ensure_tab_watchdog()
        self.tab_status.setText("Iniciando servicio local en 127.0.0.1:8765...")

    def _ensure_tab_watchdog(self):
        watcher = getattr(self, "_tab_watchdog", None)
        if watcher is None:
            watcher=QTimer(self)
            watcher.setInterval(6000)
            watcher.timeout.connect(self._tab_watchdog_check)
            self._tab_watchdog=watcher
        if not watcher.isActive():
            watcher.start()

    def _tab_watchdog_check(self):
        if getattr(self, "_tab_keep_alive", False) and not bridge_is_running():
            self.tab_start_bridge()

    def _tab_server_output(self):
        if hasattr(self, "tab_output"):
            text = bytes(self._tab_server.readAllStandardOutput()).decode("utf-8", "replace")
            if "ready" in text:
                self.tab_status.setText("Puente iniciado. Empareja la pestaña desde Chrome.")
            else:
                self.tab_output.appendPlainText(text[:2000])

    def _tab_server_finished(self, code, status):
        if hasattr(self, "tab_status"):
            self.tab_status.setText(f"Puente detenido (código {code}).")

    def tab_copy_token(self):
        if not TOKEN_FILE.is_file():
            self.tab_status.setText("Inicia primero el puente local.")
            return
        token = TOKEN_FILE.read_text("ascii").strip()
        if len(token) != 64:
            self.tab_status.setText("El archivo de emparejamiento no es válido.")
            return
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(token)
        self.tab_status.setText("Código copiado. Pégalo en el panel de la extensión.")

    def tab_run(self, action):
        if getattr(self, "_tab_client", None) is not None and \
                self._tab_client.state() != QProcess.ProcessState.NotRunning:
            self.tab_status.setText("La operación anterior aún está ejecutándose.")
            return
        if not TOKEN_FILE.is_file():
            self.tab_status.setText("Inicia primero el puente local.")
            return
        PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
        plan = PRIVATE_DIR / ("action-" + uuid.uuid4().hex + ".json")
        plan.write_text(json.dumps([action], ensure_ascii=False), "utf-8")
        self._tab_plan = plan
        self._tab_last_action = action["action"]
        client = QProcess(self)
        self._tab_client = client
        client.setProgram(worker_python())
        args = ["-m", "mouse_virtual.modules.agent_control.tab_bridge",
                "run", "--token-file", str(TOKEN_FILE), "--plan", str(plan)]
        if action["action"] not in {"inspect", "status", "screenshot", "tab.list"}:
            args += ["--allow-writes"]
        if action["action"] == "screenshot":
            output = PRIVATE_DIR / ("capture-" + uuid.uuid4().hex + ".png")
            args += ["--screenshot-output", str(output)]
        if action["action"] in {"navigate", "workspace.create", "workspace.open"}:
            host = urlparse(action.get("url", "")).hostname
            if host:
                args += ["--allow-host", host]
        if action["action"] in {"tab.select", "tab.select_id"}:
            args += ["--allow-host", action["host"]]
        if action["action"] == "file":
            path = Path(action.get("path", "")).expanduser()
            if path.is_file():
                args += ["--allow-file-root", str(path.parent.resolve())]
        client.setArguments(args)
        client.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        client.finished.connect(self._tab_client_finished)
        client.start()
        self.tab_status.setText("Ejecutando acción dirigida a la pestaña...")

    def _tab_client_finished(self, code, status):
        output = bytes(self._tab_client.readAllStandardOutput()).decode("utf-8", "replace")
        if output:
            self.tab_output.appendPlainText(output[:8000])
            if code == 0 and getattr(self, "_tab_last_action", "") == "tab.list":
                try:
                    result = json.loads(output)
                    tabs = result[0]["result"]["tabs"]
                    group = result[0]["result"].get("workspace")
                    group_ids = {entry["tabId"] for entry in group["tabs"]} if group else set()
                    self.tab_tabs.blockSignals(True)
                    self.tab_tabs.clear()
                    for item in tabs:
                        marker = "[Grupo]" if item["tabId"] in group_ids else "[Chrome]"
                        active = " (activa)" if item["active"] else ""
                        if not item.get("controllable", False):
                            active += " (solo lectura)"
                        title = (item["title"] or item["url"])[:75]
                        self.tab_tabs.addItem(f"{marker} {title}{active}", item)
                    self.tab_tabs.blockSignals(False)
                    self.tab_status.setText(f"{len(tabs)} pestañas encontradas. Elige una inactiva.")
                except (ValueError, IndexError, KeyError, TypeError):
                    pass
        self.tab_status.setText("Acción confirmada." if code == 0 else
                                "Acción fallida o incierta. No se reintentará automáticamente.")
        try:
            self._tab_plan.unlink(missing_ok=True)
        except OSError:
            pass

    def tab_choose_from_list(self, index):
        item = self.tab_tabs.itemData(index)
        if not isinstance(item, dict):
            return
        self.tab_target_id.setValue(item["tabId"])
        if item.get("url"):
            self.tab_target_url.setText(item["url"])

    def tab_check_status(self):
        self.tab_run({"action": "status"})

    def tab_navigate(self):
        self.tab_run({"action": "navigate", "url": self.tab_url.text().strip()})

    def tab_attach_file(self):
        self.tab_run({"action": "file", "selector": self.tab_selector.text().strip(),
                      "path": self.tab_file.text().strip()})

    def tab_select_window_tab(self):
        target=self.tab_target_url.text().strip()
        parsed=urlparse(target)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            self.tab_status.setText("Introduzca una dirección HTTP(S) para la pestaña inactiva.")
            return
        payload={"action":"tab.select","host":parsed.hostname.lower()}
        if parsed.path and parsed.path != "/":
            payload["urlPrefix"]=target
        self.tab_run(payload)

    def tab_create_workspace(self):
        self.tab_run({"action": "workspace.create", "url": self.tab_url.text().strip()})

    def tab_open_workspace(self):
        self.tab_run({"action": "workspace.open", "url": self.tab_url.text().strip()})

    def tab_select_workspace(self):
        self.tab_run({"action": "workspace.select", "tabId": self.tab_target_id.value()})

    def tab_close_workspace(self):
        self.tab_run({"action": "workspace.close", "tabId": self.tab_target_id.value()})

    def tab_select_by_id(self):
        target = self.tab_target_url.text().strip()
        parsed = urlparse(target)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            self.tab_status.setText("Indica el sitio de la pestaña que deseas seleccionar.")
            return
        self.tab_run({"action": "tab.select_id",
                      "tabId": self.tab_target_id.value(),
                      "host": parsed.hostname.lower()})

    def tab_stop_bridge(self):
        self._tab_keep_alive=False
        watcher=getattr(self,"_tab_watchdog",None)
        if watcher is not None:
            watcher.stop()
        for key in ("_tab_client", "_tab_server"):
            process = getattr(self, key, None)
            if process is not None and process.state() != QProcess.ProcessState.NotRunning:
                process.terminate()
                if not process.waitForFinished(1200):
                    process.kill()
                    process.waitForFinished(500)
        if hasattr(self, "tab_status"):
            self.tab_status.setText("Supervisión detenida. Un servicio local externo puede seguir activo.")
