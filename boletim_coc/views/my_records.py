from boletim_coc.repository import list_my_records
from boletim_coc.theme import header


def render(st, conn, windows_user):
    header(st, "Meus Registros", f"Registros locais de {windows_user}")
    c1, c2, c3 = st.columns([2, 1, 1])
    query = c1.text_input("Pesquisar", placeholder="Código, título, descrição ou local")
    status = c2.selectbox("Status", ["Todos", "rascunho", "finalizado"])
    tipo = c3.text_input("Tipo", placeholder="Todos")
    rows = list_my_records(
        conn,
        windows_user,
        query=query,
        status=None if status == "Todos" else status,
        tipo=tipo.strip() or None,
    )
    if not rows:
        st.info("Nenhum registro encontrado.")
        return
    for row in rows:
        with st.container(border=True):
            a, b = st.columns([5, 1])
            a.markdown(f'**{row["codigo"]} — {row["titulo"]}**')
            a.caption(
                f'{row["data_ocorrencia"]} · {row["local"]} · '
                f'{row["tipo_ocorrencia"]} · {row["status"]}'
            )
            if b.button("Abrir", key=f'open-{row["id"]}', use_container_width=True):
                st.session_state.selected_boletim_id = row["id"]
                st.session_state.coc_section = "detail"
                st.rerun()
