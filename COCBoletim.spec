# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

streamlit_datas, streamlit_binaries, streamlit_hidden = collect_all("streamlit")
reportlab_datas, reportlab_binaries, reportlab_hidden = collect_all("reportlab")

# The Streamlit script is executed dynamically at runtime, so keep the local
# application as real .py files beside app.py instead of relying on PyInstaller's
# embedded importer. collect_data_files() is intentionally not used here because
# boletim_coc is a source-tree package, not an installed distribution.
local_app_datas = []
for source in Path("boletim_coc").rglob("*.py"):
    destination = Path("appsrc") / source.parent
    local_app_datas.append((str(source), str(destination)))

hiddenimports = (
    streamlit_hidden
    + reportlab_hidden
    + collect_submodules("boletim_coc")
)

datas = (
    streamlit_datas
    + reportlab_datas
    + copy_metadata("streamlit", recursive=True)
    + [("app.py", "appsrc")]
    + local_app_datas
)

binaries = streamlit_binaries + reportlab_binaries


a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="COCBoletim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="COCBoletim",
)
