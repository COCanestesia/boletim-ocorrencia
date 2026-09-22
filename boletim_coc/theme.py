from html import escape

CSS = """
<style>
.stApp{background:#f5f8fb}
.block-container{max-width:1320px;padding-top:1.5rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#eef4fb;border-right:1px solid #d8e3ef}
.coc-head{background:linear-gradient(120deg,#0b5ea8,#1879c6);padding:24px 28px;
border-radius:18px;color:#fff;margin-bottom:18px;box-shadow:0 10px 26px rgba(11,94,168,.16)}
.coc-head h1{margin:0;font-size:1.85rem}
.coc-head p{margin:.35rem 0 0;color:#e8f3ff}
.coc-card{background:#fff;border:1px solid #dce6f0;border-radius:16px;
padding:18px 20px;margin-bottom:12px;box-shadow:0 4px 14px rgba(35,71,103,.05)}
.coc-code{font-weight:800;color:#0b5ea8}
.coc-muted{color:#718096;font-size:.86rem}
[data-testid="stForm"]{background:#fff;border:1px solid #dce6f0;border-radius:16px;padding:16px}
.stButton>button{border-radius:10px}
</style>
"""


def apply_theme(st):
    st.markdown(CSS, unsafe_allow_html=True)


def header(st, title: str, subtitle: str):
    st.markdown(
        f'<div class="coc-head"><h1>{escape(str(title))}</h1><p>{escape(str(subtitle))}</p></div>',
        unsafe_allow_html=True,
    )
