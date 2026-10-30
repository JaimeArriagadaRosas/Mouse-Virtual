from pathlib import Path
import ast
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "mouse_virtual"


def test_python_module_length_budget():
    for root in (ROOT / "src", ROOT / "scripts", ROOT / "tests"):
        for file in root.rglob("*.py"):
            lines = file.read_text(encoding="utf8").splitlines()
            assert len(lines) <= 300, f"{file.relative_to(ROOT)}: {len(lines)} lines, consider split"


def test_modules_never_import_main_window():
    for root in (PKG / "modules", PKG / "infrastructure"):
        for file in root.rglob("*.py"):
            tree = ast.parse(file.read_text(encoding="utf8"))
            imported = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    imported.append(node.module or "")
                if isinstance(node, ast.Import):
                    imported.extend(name.name for name in node.names)
            assert all(name != "main" and not name.startswith("mouse_virtual.app.main_window")
                       for name in imported), file.relative_to(ROOT)


def test_svg_resources_parse():
    for name in ("logo.svg", "banner.svg", "architecture.svg"):
        ET.parse(ROOT / "assets" / name)


def test_packaged_theme_and_project_metadata():
    assert (PKG / "resources" / "theme.qss").is_file()
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / "LICENSE").is_file()
    assert (ROOT / "CONTRIBUTING.md").is_file()

def test_cursor_svg_resource_parses():
    ET.parse(PKG / 'resources' / 'cursors' / 'black_pointer.svg')
