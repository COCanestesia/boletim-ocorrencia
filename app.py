from pathlib import Path
import sys

APP_SOURCE_ROOT = Path(__file__).resolve().parent
APP_SOURCE_ROOT_TEXT = str(APP_SOURCE_ROOT)
if APP_SOURCE_ROOT_TEXT in sys.path:
    sys.path.remove(APP_SOURCE_ROOT_TEXT)
sys.path.insert(0, APP_SOURCE_ROOT_TEXT)

import streamlit as st

from boletim_coc.config import resolve_paths
from boletim_coc.db import connect_db, initialize_database
from boletim_coc.identity import current_windows_user
from boletim_coc.theme import apply_theme

st.set_page_config(
    page_title="COC · Boletim de Ocorrência",
    page_icon="📝",
    layout="wide",
)

paths = resolve_paths()
conn = connect_db(paths)
initialize_database(conn)
windows_user = current_windows_user()
apply_theme(st)

if "coc_section" not in st.session_state:
    st.session_state.coc_section = "new"

with st.sidebar:
    st.markdown("## COC")
    st.caption("Boletim de Ocorrência")
    st.info(f"Windows: {windows_user}")
    section = st.session_state.coc_section
    if st.button("📝 Novo Registro", use_container_width=True, type="primary" if section == "new" else "secondary"):
        st.session_state.coc_section = "new"; st.rerun()
    if st.button("📚 Meus Registros", use_container_width=True, type="primary" if section == "mine" else "secondary"):
        st.session_state.coc_section = "mine"; st.rerun()
    if st.button("📥 Recebidos", use_container_width=True, type="primary" if section == "received" else "secondary"):
        st.session_state.coc_section = "received"; st.rerun()

section = st.session_state.coc_section
if section == "new":
    from boletim_coc.views.new_record import render
    render(st, conn, paths, windows_user)
elif section == "mine":
    from boletim_coc.views.my_records import render
    render(st, conn, windows_user)
elif section == "received":
    from boletim_coc.views.received import render
    render(st, conn, paths, windows_user)
else:
    from boletim_coc.views.detail import render
    render(st, conn, paths)
