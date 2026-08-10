import streamlit as st
import requests
import aiohttp
import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# ─── Bootstrap ───────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
load_dotenv(os.path.join(ROOT, ".env"))

APP_PORT = int(os.getenv("APP_PORT", 8058))
API_URL  = os.getenv("API_URL", f"http://localhost:{APP_PORT}")

st.set_page_config(
    page_title="Agentic RAG Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS (no external font imports = instant render) ─────────────────────────
st.markdown("""
<style>
/* ── Base ── */
.stApp {
  background:
    radial-gradient(circle at 12% 12%, rgba(99,102,241,.13) 0%, transparent 40%),
    radial-gradient(circle at 88% 80%, rgba(168,85,247,.13) 0%, transparent 40%),
    #0b0f19;
  color: #f1f5f9;
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
}

/* ── Layout ── */
.main .block-container { padding: 1.8rem 2.4rem 3rem; max-width: 1100px; }

/* ── Hero ── */
.hero-title {
  font-size: 2.4rem; font-weight: 800;
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 50%, #38bdf8 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  letter-spacing: -.02em; line-height: 1.15; margin-bottom: .3rem;
}
.hero-sub { color: #64748b; font-size: .92rem; margin-bottom: 1.4rem; }

/* ── Badges ── */
.badge { display:inline-flex; align-items:center; padding:3px 10px;
  border-radius:20px; font-size:.72rem; font-weight:700;
  letter-spacing:.04em; margin-right:5px; }
.bp { background:rgba(168,85,247,.14); color:#c084fc; border:1px solid rgba(168,85,247,.3); }
.bb { background:rgba(56,189,248,.12); color:#38bdf8; border:1px solid rgba(56,189,248,.28); }
.bg { background:rgba(34,197,94,.13); color:#4ade80; border:1px solid rgba(34,197,94,.28); }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: rgba(8,16,32,.9) !important;
  border-right: 1px solid rgba(255,255,255,.07) !important;
}

/* ── Buttons ── */
.stButton > button {
  border-radius: 10px; font-weight: 600;
  border: 1px solid rgba(255,255,255,.1);
  background: rgba(99,102,241,.15);
  color: #e2e8f0; transition: all .2s ease;
}
.stButton > button:hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg,#6366f1,#a855f7);
  box-shadow: 0 6px 18px rgba(99,102,241,.35);
  border-color: transparent; color: #fff;
}
[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg,#6366f1,#a855f7) !important;
  border: none !important; color: #fff !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input {
  background: rgba(15,23,42,.65) !important;
  border: 1px solid rgba(255,255,255,.1) !important;
  border-radius: 8px !important; color: #f8fafc !important;
}
.stTextInput > div > div > input:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 2px rgba(99,102,241,.2) !important;
}

/* ── Chat ── */
.stChatMessage {
  background: rgba(22,35,55,.55) !important;
  border: 1px solid rgba(255,255,255,.06) !important;
  border-radius: 14px !important;
  margin-bottom: .7rem !important;
}
.stChatInputContainer {
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  background: rgba(10,18,34,.8) !important;
}

/* ── Misc ── */
hr { border-color: rgba(255,255,255,.07) !important; }
div.stAlert { border-radius: 10px !important; }
[data-testid="stFileUploader"] {
  border: 1px dashed rgba(99,102,241,.4) !important;
  border-radius: 10px !important;
  background: rgba(99,102,241,.05) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────────────
st.session_state.setdefault("session_id", None)
st.session_state.setdefault("messages",   [])
st.session_state.setdefault("ingest_log", [])

# ─── Helpers ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _health(url: str) -> bool:
    try:
        return requests.get(f"{url}/health", timeout=4).status_code == 200
    except Exception:
        return False


async def _stream(message: str, base_url: str, box) -> str:
    payload = {
        "message":    message,
        "session_id": st.session_state.session_id,
        "user_id":    "user",
        "search_type": "hybrid",
    }
    full = ""
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as sess:
        async with sess.post(f"{base_url}/chat/stream", json=payload) as resp:
            async for raw in resp.content:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                kind = data.get("type")
                if kind == "session":
                    st.session_state.session_id = data.get("session_id")
                elif kind == "text":
                    full += data.get("content", "")
                    box.markdown(full + "▌")
                elif kind == "tools":
                    for t in data.get("tools", []):
                        full += f"\n\n`⚡ {t.get('tool_name','')}`"
                    box.markdown(full)
                elif kind == "end":
                    break
    box.markdown(full)
    return full


def _run_stream(message: str, base_url: str, box) -> str:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_stream(message, base_url, box))
    finally:
        loop.close()


@st.cache_data(ttl=5, show_spinner=False)
def _get_documents(url: str):
    try:
        r = requests.get(f"{url}/documents", timeout=4)
        if r.status_code == 200:
            return r.json().get("documents", [])
    except Exception:
        pass
    return []

def _delete_all_docs(url: str) -> bool:
    try:
        r = requests.delete(f"{url}/documents", timeout=10)
        st.cache_data.clear()
        return r.status_code == 200
    except Exception:
        return False

def _delete_doc(url: str, doc_id: str) -> bool:
    try:
        r = requests.delete(f"{url}/documents/{doc_id}", timeout=5)
        st.cache_data.clear()
        return r.status_code == 200
    except Exception:
        return False


def _ingest_via_api(
    file_bytes: bytes,
    filename: str,
    base_url: str,
    clean: bool = False,
    include_tables: bool = False,
    include_images: bool = False,
):
    """
    Upload the PDF to the API's /ingest endpoint and let it run in-process
    against a warm Docling pipeline. Much faster than the old approach of
    spawning a fresh `python -m ingestion.ingest` subprocess per file, which
    reloaded Docling's layout/table models from scratch on every upload.
    """
    try:
        resp = requests.post(
            f"{base_url}/ingest",
            files={"file": (filename, file_bytes, "application/pdf")},
            data={
                "clean": str(clean).lower(),
                "include_tables": str(include_tables).lower(),
                "include_images": str(include_images).lower(),
            },
            timeout=300,
        )
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:1.3rem;font-weight:800;'
        'background:linear-gradient(135deg,#a855f7,#38bdf8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
        '⚡ Control Panel</p>',
        unsafe_allow_html=True,
    )

    base_url = st.text_input("API URL", value=API_URL, label_visibility="collapsed")

    # Live status dot
    ok = _health(base_url)
    st.caption(("🟢 API Online" if ok else "🔴 API Offline — start with `uvicorn agent.api:app --port 8058`"))

    c1, c2 = st.columns(2)
    with c1:
        if st.button("↺ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages   = []
            st.session_state.session_id = None
            st.rerun()

    st.divider()

    # ── Ingestion ──
    st.markdown(
        '<p style="font-size:1.05rem;font-weight:700;color:#f8fafc;">📁 Ingest Document</p>',
        unsafe_allow_html=True,
    )
    st.caption("Upload a PDF → Docling extracts text → vectors stored in Neon.")

    uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
    clean_option = st.checkbox("Wipe old documents before ingest", value=True, help="Replaces previous documents so the AI focuses on your newly uploaded PDF.")
    tables_option = st.checkbox(
        "Extract tables & images (slower)",
        value=False,
        help="Only needed for PDFs with data tables you want searchable. Loads Docling's table-structure model, which is much slower on CPU — leave off for plain-text PDFs.",
    )

    if uploaded:
        if st.button("🚀 Process & Ingest", type="primary", use_container_width=True):
            with st.spinner(f"Ingesting '{uploaded.name}'…"):
                ok, result = _ingest_via_api(
                    uploaded.getvalue(),
                    uploaded.name,
                    base_url,
                    clean=clean_option,
                    include_tables=tables_option,
                    include_images=tables_option,
                )

            if ok:
                st.cache_data.clear()
                chunks = sum(r.get("chunks_created", 0) for r in result) if isinstance(result, list) else 0
                st.success(f"✅ '{uploaded.name}' ingested successfully! ({chunks} chunks)")
                st.rerun()
            else:
                st.error(f"❌ Ingestion failed: {result}")

    st.divider()

    # ── Document Management ──
    st.markdown(
        '<p style="font-size:1.05rem;font-weight:700;color:#f8fafc;">📚 Ingested Documents</p>',
        unsafe_allow_html=True,
    )
    docs = _get_documents(base_url) if ok else []
    if docs:
        for d in docs:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"📄 **{d['title']}**\n<span style='font-size:0.75rem;color:#94a3b8;'>{d.get('chunk_count', 0)} chunks</span>", unsafe_allow_html=True)
            with col2:
                if st.button("❌", key=f"del_{d['id']}", help="Delete this document"):
                    _delete_doc(base_url, d['id'])
                    st.rerun()
        st.write("")
        if st.button("🔥 Delete All Documents", use_container_width=True):
            if _delete_all_docs(base_url):
                st.success("Cleared all documents!")
                st.rerun()
    else:
        st.caption("No documents in database.")

    st.divider()
    st.markdown(
        '<p style="font-size:.72rem;color:#475569;text-align:center;">'
        'Pydantic AI · Neon pgvector · Docling OCR</p>',
        unsafe_allow_html=True,
    )

# ─── Main ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Agentic RAG Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Document intelligence powered by &nbsp;'
    '<span class="badge bp">Pydantic AI</span>'
    '<span class="badge bb">pgvector · Neon</span>'
    '<span class="badge bg">Docling OCR</span></p>',
    unsafe_allow_html=True,
)

# ── Chat history ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# ── Input ──
if prompt := st.chat_input("Ask anything about your documents…"):
    if not ok:
        st.warning("⚠️ Backend API is offline. Start it first with `python -m uvicorn agent.api:app --port 8058`")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        box    = st.empty()
        box.markdown("_Searching knowledge base…_")
        answer = _run_stream(prompt, base_url, box)

    st.session_state.messages.append({"role": "assistant", "content": answer})
