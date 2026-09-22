from pathlib import Path
import tempfile

from boletim_coc.package_import import import_package
from boletim_coc.repository import list_received
from boletim_coc.theme import header


def render(st, conn, paths, windows_user):
    header(st, "Recebidos", "Importe boletins enviados por outro computador")
    upload = st.file_uploader("Importar boletim (.zip)", type=["zip"])
    if upload and st.button("Importar", type="primary"):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp.write(upload.getvalue())
                temp_path = Path(tmp.name)
            row = import_package(conn, paths, temp_path, windows_user)
            st.success(f'{row["codigo"]} importado com sucesso.')
            st.session_state.selected_boletim_id = row["id"]
            st.session_state.coc_section = "detail"
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        finally:
            if temp_path:
                temp_path.unlink(missing_ok=True)

    rows = list_received(conn, windows_user)
    st.subheader("Boletins recebidos")
    if not rows:
        st.info("Nenhum boletim recebido.")
    for row in rows:
        with st.container(border=True):
            a, b = st.columns([5, 1])
            a.markdown(f'**{row["codigo"]} — {row["titulo"]}**')
            a.caption(f'Autor: {row["autor_original"]} · {row["data_ocorrencia"]}')
            if b.button("Abrir", key=f'received-{row["id"]}', use_container_width=True):
                st.session_state.selected_boletim_id = row["id"]
                st.session_state.coc_section = "detail"
                st.rerun()
