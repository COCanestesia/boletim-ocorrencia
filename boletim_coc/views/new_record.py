from datetime import datetime

from boletim_coc.attachments import save_attachment
from boletim_coc.models import BoletimDraft
from boletim_coc.repository import create_boletim, finalize_boletim
from boletim_coc.theme import header


TIPOS = [
    "Assistencial", "Segurança", "Administrativa",
    "Equipamento", "Documentação", "Outro",
]


def render(st, conn, paths, windows_user):
    header(st, "Boletim de Ocorrência", "Novo registro · segurança e melhoria contínua")
    with st.form("novo_boletim", clear_on_submit=False):
        autor = st.text_input(
            "Nome do autor *",
            placeholder="Digite o nome completo de quem está registrando a ocorrência",
        )
        st.caption("O nome acima será exibido no boletim e no PDF. A conta do Windows é usada apenas internamente.")
        c1, c2 = st.columns(2)
        data = c1.date_input("Data da ocorrência", value=datetime.now().date())
        hora = c2.time_input("Hora da ocorrência", value=datetime.now().time().replace(second=0, microsecond=0))
        c3, c4 = st.columns(2)
        local = c3.text_input("Local *")
        setor = c4.text_input("Setor *")
        tipo = st.selectbox("Tipo da ocorrência *", TIPOS)
        titulo = st.text_input("Título curto *")
        descricao = st.text_area("Descrição detalhada *", height=150)
        consequencias = st.text_area("Consequências / impacto", height=90)
        pessoas = st.text_area("Pessoas envolvidas", height=90)
        imediatas = st.text_area("Ações imediatas tomadas", height=90)
        preventivas = st.text_area("Ações preventivas / recomendações", height=90)
        uploads = st.file_uploader(
            "Anexos",
            type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx"],
            accept_multiple_files=True,
        )
        c5, c6 = st.columns(2)
        save = c5.form_submit_button("Salvar rascunho", use_container_width=True)
        finish = c6.form_submit_button("Salvar e finalizar", type="primary", use_container_width=True)

    if save or finish:
        try:
            if not autor.strip():
                raise ValueError("Informe o nome do autor.")
            draft = BoletimDraft(
                data, hora, local, setor, tipo, titulo, descricao,
                consequencias, pessoas, imediatas, preventivas,
            )
            row = create_boletim(conn, draft, windows_user, author_name=autor)
            attachment_rows = []
            for upload in uploads or []:
                attachment_rows.append(
                    save_attachment(
                        conn, paths, row["id"], upload.name,
                        upload.getvalue(), upload.type or "application/octet-stream",
                    )
                )
            if finish:
                row = finalize_boletim(conn, row["id"], attachment_rows)
            st.success(f'{row["codigo"]} salvo com sucesso.')
            st.session_state.selected_boletim_id = row["id"]
            st.session_state.coc_section = "detail"
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
