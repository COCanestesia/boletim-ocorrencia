from datetime import date, time

from boletim_coc.attachments import list_attachments, resolve_attachment_path
from boletim_coc.package_export import export_pdf_file, export_zip
from boletim_coc.repository import finalize_boletim, get_boletim, update_draft
from boletim_coc.theme import header
from boletim_coc.views.new_record import TIPOS


def _edit_form(st, conn, row):
    with st.expander("Editar rascunho", expanded=False):
        with st.form(f'edit-{row["id"]}'):
            c1, c2 = st.columns(2)
            data_value = c1.date_input(
                "Data da ocorrência",
                value=date.fromisoformat(row["data_ocorrencia"]),
                key=f'edit-date-{row["id"]}',
            )
            hora_value = c2.time_input(
                "Hora da ocorrência",
                value=time.fromisoformat(row["hora_ocorrencia"]),
                key=f'edit-time-{row["id"]}',
            )
            c3, c4 = st.columns(2)
            local = c3.text_input("Local *", value=row["local"])
            setor = c4.text_input("Setor *", value=row["setor"])
            current_index = TIPOS.index(row["tipo_ocorrencia"]) if row["tipo_ocorrencia"] in TIPOS else len(TIPOS) - 1
            tipo = st.selectbox("Tipo da ocorrência *", TIPOS, index=current_index)
            titulo = st.text_input("Título curto *", value=row["titulo"])
            descricao = st.text_area("Descrição detalhada *", value=row["descricao"], height=150)
            consequencias = st.text_area("Consequências / impacto", value=row["consequencias"], height=90)
            pessoas = st.text_area("Pessoas envolvidas", value=row["pessoas_envolvidas"], height=90)
            imediatas = st.text_area("Ações imediatas tomadas", value=row["acoes_imediatas"], height=90)
            preventivas = st.text_area("Ações preventivas / recomendações", value=row["acoes_preventivas"], height=90)
            submit = st.form_submit_button("Salvar alterações", type="primary", use_container_width=True)
        if submit:
            try:
                if not all([local.strip(), setor.strip(), tipo.strip(), titulo.strip(), descricao.strip()]):
                    raise ValueError("Preencha todos os campos obrigatórios.")
                update_draft(
                    conn,
                    row["id"],
                    {
                        "data_ocorrencia": data_value.isoformat(),
                        "hora_ocorrencia": hora_value.strftime("%H:%M"),
                        "local": local.strip(),
                        "setor": setor.strip(),
                        "tipo_ocorrencia": tipo.strip(),
                        "titulo": titulo.strip(),
                        "descricao": descricao.strip(),
                        "consequencias": consequencias.strip(),
                        "pessoas_envolvidas": pessoas.strip(),
                        "acoes_imediatas": imediatas.strip(),
                        "acoes_preventivas": preventivas.strip(),
                    },
                )
                st.success("Rascunho atualizado.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def render(st, conn, paths):
    bulletin_id = st.session_state.get("selected_boletim_id")
    row = get_boletim(conn, bulletin_id) if bulletin_id else None
    if row is None:
        st.warning("Boletim não encontrado.")
        return

    header(st, row["codigo"], row["titulo"])
    attachments = list_attachments(conn, row["id"])

    st.caption(
        f'Autor: {row["autor_original"]} · Origem: {row["origem"]} · '
        f'Status: {row["status"]}'
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Data", row["data_ocorrencia"])
    c2.metric("Hora", row["hora_ocorrencia"])
    c3.metric("Tipo", row["tipo_ocorrencia"])

    sections = [
        ("Local / Setor", f'{row["local"]} · {row["setor"]}'),
        ("Descrição", row["descricao"]),
        ("Consequências / impacto", row["consequencias"]),
        ("Pessoas envolvidas", row["pessoas_envolvidas"]),
        ("Ações imediatas", row["acoes_imediatas"]),
        ("Ações preventivas", row["acoes_preventivas"]),
    ]
    for title, value in sections:
        st.markdown(f"#### {title}")
        st.write(value or "—")

    st.markdown("#### Anexos")
    if not attachments:
        st.caption("Nenhum anexo.")
    for att in attachments:
        file_path = resolve_attachment_path(paths, att)
        st.download_button(
            f'Baixar {att["nome_original"]}',
            data=file_path.read_bytes(),
            file_name=att["nome_original"],
            mime=att["mime_type"],
            key=f'att-{att["id"]}',
        )

    if row["origem"] == "local" and row["status"] == "rascunho":
        _edit_form(st, conn, row)
        if st.button("Finalizar boletim", type="primary"):
            finalize_boletim(conn, row["id"], attachments)
            st.rerun()

    row = get_boletim(conn, row["id"])
    if row["status"] == "finalizado":
        pdf = export_pdf_file(paths, row, attachments)
        package = export_zip(paths, row, attachments)
        d1, d2 = st.columns(2)
        d1.download_button(
            "Baixar PDF",
            pdf.read_bytes(),
            file_name=pdf.name,
            mime="application/pdf",
            use_container_width=True,
        )
        d2.download_button(
            "Baixar ZIP completo",
            package.read_bytes(),
            file_name=package.name,
            mime="application/zip",
            use_container_width=True,
        )

    if row["origem"] == "recebido" or row["status"] == "finalizado":
        st.info("Este boletim está em modo somente leitura.")
