import streamlit as st
import requests
from bs4 import BeautifulSoup
import ollama
import json
import re
from urllib.parse import urlparse

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🕸️",
    layout="wide",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #0d0d10;
    color: #e8e6e1;
}

.stApp {
    background-color: #0d0d10;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Hero header */
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 0.2rem;
    background: linear-gradient(135deg, #ff4d4d 0%, #f9a825 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 0.95rem;
    color: #666;
    margin-bottom: 2rem;
    font-family: 'JetBrains Mono', monospace;
}

/* URL Input */
.stTextInput > div > div > input {
    background: #16161a !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 8px !important;
    color: #e8e6e1 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    padding: 0.75rem 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #ff4d4d !important;
    box-shadow: 0 0 0 2px rgba(255, 77, 77, 0.15) !important;
}

/* Textarea */
.stTextArea > div > div > textarea {
    background: #16161a !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 8px !important;
    color: #e8e6e1 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: #ff4d4d !important;
    box-shadow: 0 0 0 2px rgba(255, 77, 77, 0.15) !important;
}

/* Buttons */
.stButton > button {
    background: #ff4d4d !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.6rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em !important;
}

.stButton > button:hover {
    background: #e03030 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(255, 77, 77, 0.3) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #16161a !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 8px !important;
    color: #ff4d4d !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
}

.streamlit-expanderContent {
    background: #16161a !important;
    border: 1px solid #2a2a35 !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* Code / pre */
.stCode, code, pre {
    background: #16161a !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    color: #aaa !important;
}

/* Status cards */
.status-card {
    background: #16161a;
    border: 1px solid #2a2a35;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}

.status-card.success { border-left: 3px solid #4caf50; }
.status-card.error   { border-left: 3px solid #ff4d4d; }
.status-card.info    { border-left: 3px solid #f9a825; }

.stat-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.stat-chip {
    background: #1e1e26;
    border: 1px solid #2a2a35;
    border-radius: 6px;
    padding: 0.4rem 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #888;
}

.stat-chip span {
    color: #ff4d4d;
    font-weight: 600;
}

/* AI result box */
.ai-result {
    background: #16161a;
    border: 1px solid #2a2a35;
    border-left: 3px solid #f9a825;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    font-size: 0.92rem;
    line-height: 1.7;
    color: #ccc;
    white-space: pre-wrap;
    font-family: 'Space Grotesk', sans-serif;
}

/* Section labels */
.section-label {
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: #ff4d4d;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.5rem;
}

/* Select */
.stSelectbox > div > div {
    background: #16161a !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 8px !important;
    color: #e8e6e1 !important;
}

/* Divider */
hr {
    border-color: #2a2a35 !important;
    margin: 1.5rem 0 !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #ff4d4d !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def scrape_website(url: str) -> dict:
    """Fetch a URL and return raw HTML + cleaned text."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise tags
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript", "svg"]):
            tag.decompose()

        raw_html = resp.text
        clean_text = soup.get_text(separator="\n", strip=True)

        # Deduplicate blank lines
        lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
        clean_text = "\n".join(lines)

        title = soup.title.string.strip() if soup.title else "No title"

        return {
            "ok": True,
            "title": title,
            "raw_html": raw_html,
            "clean_text": clean_text,
            "char_count": len(clean_text),
            "status_code": resp.status_code,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def chunk_text(text: str, max_chars: int = 6000) -> list[str]:
    """Split text into chunks so it fits the LLM context."""
    words = text.split()
    chunks, current = [], []
    total = 0
    for word in words:
        wl = len(word) + 1
        if total + wl > max_chars and current:
            chunks.append(" ".join(current))
            current, total = [], 0
        current.append(word)
        total += wl
    if current:
        chunks.append(" ".join(current))
    return chunks


def get_ollama_models() -> list[str]:
    """Return available local Ollama model names."""
    try:
        result = ollama.list()
        # Handle both dict-style and object-style responses
        if hasattr(result, 'models'):
            models_list = result.models
        elif isinstance(result, dict):
            models_list = result.get('models', [])
        else:
            return ["llama3.2", "mistral", "llama3", "qwen2.5"]

        names = []
        for m in models_list:
            if hasattr(m, 'model'):
                names.append(m.model)
            elif hasattr(m, 'name'):
                names.append(m.name)
            elif isinstance(m, dict):
                names.append(m.get('model') or m.get('name', ''))
        return [n for n in names if n] or ["llama3.2"]
    except Exception:
        return ["llama3.2", "mistral", "llama3", "qwen2.5"]


def ask_ollama(model: str, prompt: str, context: str, max_chunk_chars: int = 5000) -> str:
    """Send prompt + page context to Ollama, chunking if needed."""
    chunks = chunk_text(context, max_chunk_chars)

    if len(chunks) == 1:
        full_prompt = (
            f"You are a web scraping AI assistant. "
            f"Analyse the following webpage content and answer the user's request.\n\n"
            f"PAGE CONTENT:\n{chunks[0]}\n\n"
            f"USER REQUEST: {prompt}\n\n"
            f"Provide a clear, structured answer."
        )
        resp = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": full_prompt}]
        )
        return resp['message']['content']

    # Multi-chunk: summarise each chunk then synthesise
    summaries = []
    for i, chunk in enumerate(chunks[:5]):   # cap at 5 chunks
        chunk_prompt = (
            f"Summarise the key information in this webpage section (chunk {i+1}/{len(chunks)}) "
            f"relevant to: '{prompt}'\n\nCONTENT:\n{chunk}"
        )
        r = ollama.chat(model=model, messages=[{"role": "user", "content": chunk_prompt}])
        summaries.append(r['message']['content'])

    synthesis_prompt = (
        f"You have analysed {len(summaries)} sections of a webpage. "
        f"Below are the section summaries. Answer the user request based on them.\n\n"
        f"SUMMARIES:\n" + "\n---\n".join(summaries) +
        f"\n\nUSER REQUEST: {prompt}\n\nProvide a clear, structured answer."
    )
    resp = ollama.chat(model=model, messages=[{"role": "user", "content": synthesis_prompt}])
    return resp['message']['content']


# ─── UI ─────────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-title">AI Web Scraper</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">// powered by ollama · beautifulsoup · streamlit</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([2, 1])

with col_left:
    url = st.text_input(
        "Enter a Website URL:",
        placeholder="https://example.com",
        label_visibility="visible",
    )

with col_right:
    models = get_ollama_models()
    selected_model = st.selectbox("Ollama Model:", models)

scrape_btn = st.button("🔍 Scrape Site", use_container_width=False)

# ─── State ──────────────────────────────────────────────────────────────────
if "scraped" not in st.session_state:
    st.session_state.scraped = None

# ─── Scrape ─────────────────────────────────────────────────────────────────
if scrape_btn:
    if not url or not url.startswith("http"):
        st.error("⚠️ Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("Scraping the website…"):
            result = scrape_website(url)
            st.session_state.scraped = result

        if result["ok"]:
            st.markdown(
                f'<div class="status-card success">✅ &nbsp;<b>{result["title"]}</b> — scraped successfully</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="stat-row">'
                f'<div class="stat-chip">Status <span>{result["status_code"]}</span></div>'
                f'<div class="stat-chip">Characters <span>{result["char_count"]:,}</span></div>'
                f'<div class="stat-chip">Words <span>{len(result["clean_text"].split()):,}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-card error">❌ Scrape failed: {result["error"]}</div>',
                unsafe_allow_html=True,
            )

# ─── Show scraped content ───────────────────────────────────────────────────
if st.session_state.scraped and st.session_state.scraped.get("ok"):
    data = st.session_state.scraped

    with st.expander("📄 View DOM Content", expanded=False):
        tab1, tab2 = st.tabs(["Clean Text", "Raw HTML"])
        with tab1:
            st.text_area("Cleaned page text:", data["clean_text"], height=300, label_visibility="collapsed")
        with tab2:
            st.code(data["raw_html"][:8000] + ("\n…[truncated]" if len(data["raw_html"]) > 8000 else ""), language="html")

    st.markdown("---")

    # ─── AI Query ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Ask the AI</div>', unsafe_allow_html=True)

    prompt = st.text_area(
        "What do you want to extract or know from this page?",
        placeholder=(
            "e.g. Extract all property listings with price and location\n"
            "e.g. Summarise the main content of this page\n"
            "e.g. List all links or product names"
        ),
        height=100,
        label_visibility="collapsed",
    )

    ask_btn = st.button("🤖 Analyse with Ollama", use_container_width=False)

    if ask_btn:
        if not prompt.strip():
            st.warning("Enter a prompt to ask the AI.")
        else:
            with st.spinner(f"Asking {selected_model}…"):
                try:
                    answer = ask_ollama(selected_model, prompt, data["clean_text"])
                    st.markdown('<div class="section-label">AI Response</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="ai-result">{answer}</div>', unsafe_allow_html=True)

                    # Download option
                    st.download_button(
                        label="⬇️ Download Result",
                        data=answer,
                        file_name="scrape_result.txt",
                        mime="text/plain",
                    )
                except Exception as e:
                    err = str(e)
                    if "connection" in err.lower() or "refused" in err.lower():
                        st.markdown(
                            '<div class="status-card error">'
                            '❌ <b>Ollama not running.</b> Start it with: <code>ollama serve</code><br>'
                            'Then pull a model: <code>ollama pull llama3.2</code>'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error(f"Ollama error: {err}")