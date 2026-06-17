import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import os
import csv
import io
import time
from datetime import datetime
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🕸️",
    layout="wide",
)

# ─── Theme definitions ────────────────────────────────────────────────────────
LIGHT_THEME = {
    "bg": "#f5f4ef",
    "surface": "#ffffff",
    "border": "#e0ddd5",
    "text": "#1a1a1a",
    "text_muted": "#888",
    "accent": "#e63946",
    "accent2": "#f4a261",
    "chip_bg": "#f5f4ef",
    "code_bg": "#f0ede6",
    "summary_bg": "#fff9f0",
    "summary_border": "#f4d5b0",
}

DARK_THEME = {
    "bg": "#0f0a1e",
    "surface": "#1a1530",
    "border": "#2a2040",
    "text": "#e8e6f0",
    "text_muted": "#6b6880",
    "accent": "#e63946",
    "accent2": "#f4a261",
    "chip_bg": "#16122a",
    "code_bg": "#16122a",
    "summary_bg": "#1e1530",
    "summary_border": "#3a2a10",
}

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

T = DARK_THEME if st.session_state.dark_mode else LIGHT_THEME

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif;
    color: {T['text']};
}}
.stApp {{ background-color: {T['bg']}; }}
#MainMenu, footer, header {{ visibility: hidden; }}

.hero-title {{
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 0.2rem;
    background: linear-gradient(135deg, {T['accent']} 0%, {T['accent2']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.hero-sub {{
    font-size: 0.95rem;
    color: {T['text_muted']};
    margin-bottom: 2rem;
    font-family: 'JetBrains Mono', monospace;
}}
.stTextInput > div > div > input {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    color: {T['text']} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    padding: 0.75rem 1rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {T['accent']} !important;
    box-shadow: 0 0 0 3px rgba(230,57,70,0.1) !important;
}}
.stTextArea > div > div > textarea {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    color: {T['text']} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}}
.stTextArea > div > div > textarea:focus {{
    border-color: {T['accent']} !important;
    box-shadow: 0 0 0 3px rgba(230,57,70,0.1) !important;
}}
.stButton > button {{
    background: {T['accent']} !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.6rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(230,57,70,0.25) !important;
}}
.stButton > button:hover {{
    background: #c1121f !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(230,57,70,0.35) !important;
}}
.streamlit-expanderHeader {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    color: {T['accent']} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
}}
.streamlit-expanderContent {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}}
.stCode, code, pre {{
    background: {T['code_bg']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    color: {T['text_muted']} !important;
}}
.status-card {{
    background: {T['surface']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    color: {T['text']};
}}
.status-card.success {{ border-left: 3px solid #2d9a4e; }}
.status-card.error   {{ border-left: 3px solid {T['accent']}; }}
.status-card.info    {{ border-left: 3px solid {T['accent2']}; }}
.stat-row {{ display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }}
.stat-chip {{
    background: {T['chip_bg']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    padding: 0.4rem 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: {T['text_muted']};
}}
.stat-chip span {{ color: {T['accent']}; font-weight: 600; }}
.section-label {{
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: {T['accent']};
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.5rem;
}}
.stSelectbox > div > div {{
    background: {T['surface']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 10px !important;
    color: {T['text']} !important;
}}
hr {{ border-color: {T['border']} !important; margin: 1.5rem 0 !important; }}
.stSpinner > div {{ border-top-color: {T['accent']} !important; }}

/* ── Metadata card ── */
.meta-card {{
    background: {T['surface']};
    border: 1px solid {T['border']};
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    display: flex;
    gap: 1.5rem;
    align-items: flex-start;
    flex-wrap: wrap;
}}
.meta-favicon {{
    width: 40px; height: 40px;
    border-radius: 8px;
    object-fit: contain;
    border: 1px solid {T['border']};
    background: {T['chip_bg']};
    flex-shrink: 0;
}}
.meta-info {{ flex: 1; min-width: 200px; }}
.meta-title {{
    font-size: 1rem; font-weight: 600;
    color: {T['text']};
    margin-bottom: 4px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.meta-desc {{ font-size: 0.82rem; color: {T['text_muted']}; line-height: 1.5; margin-bottom: 8px; }}
.meta-chips {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.meta-chip {{
    background: {T['chip_bg']};
    border: 1px solid {T['border']};
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    color: {T['text_muted']};
}}
.meta-chip b {{ color: {T['accent']}; }}

/* ── Summary box ── */
.summary-box {{
    background: {T['summary_bg']};
    border: 1px solid {T['summary_border']};
    border-left: 3px solid {T['accent2']};
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1.2rem;
    font-size: 0.9rem;
    line-height: 1.75;
    color: {T['text']};
    white-space: pre-wrap;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}}
.summary-label {{
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    color: {T['accent2']};
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}}

/* ── Token counter ── */
.token-bar-wrap {{
    background: {T['border']};
    border-radius: 6px;
    height: 6px;
    margin: 6px 0 2px;
    overflow: hidden;
}}
.token-bar-fill {{
    height: 6px;
    border-radius: 6px;
    background: linear-gradient(90deg, #2d9a4e, {T['accent2']}, {T['accent']});
    transition: width 0.4s ease;
}}
.token-label {{
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    color: {T['text_muted']};
}}

/* ── Chat UI ── */
.chat-wrapper {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 1.5rem;
    max-height: 480px;
    overflow-y: auto;
    padding: 0.5rem 0;
}}
.chat-bubble {{
    padding: 0.85rem 1.1rem;
    border-radius: 14px;
    font-size: 0.92rem;
    line-height: 1.7;
    max-width: 85%;
    white-space: pre-wrap;
    word-wrap: break-word;
    position: relative;
}}
.bubble-user {{
    background: {T['accent']};
    color: #ffffff;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
    margin-left: auto;
}}
.bubble-ai {{
    background: {T['surface']};
    color: {T['text']};
    border: 1px solid {T['border']};
    align-self: flex-start;
    border-bottom-left-radius: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
.bubble-label {{
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
    color: {T['text_muted']};
}}
.bubble-label.user-label {{ text-align: right; color: {T['accent']}; }}
.copy-btn {{
    position: absolute;
    top: 8px; right: 8px;
    background: {T['chip_bg']};
    border: 1px solid {T['border']};
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: {T['text_muted']};
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s;
}}
.bubble-ai:hover .copy-btn {{ opacity: 1; }}

/* ── History sidebar ── */
.history-item {{
    background: {T['surface']};
    border: 1px solid {T['border']};
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 8px;
}}
.history-domain {{
    font-size: 0.82rem; font-weight: 600;
    color: {T['text']};
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.history-time {{
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    color: {T['text_muted']};
    margin-top: 2px;
}}
</style>
""", unsafe_allow_html=True)


# ─── Constants ───────────────────────────────────────────────────────────────
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

SUGGESTED_PROMPTS = [
    "Summarise in 3 bullet points",
    "Extract all links",
    "List all products/prices",
    "Who wrote this?",
    "What is the main topic?",
]

MAX_CONTEXT_CHARS = 5000


# ─── Helpers ─────────────────────────────────────────────────────────────────

def scrape_website(url: str) -> dict:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        description = ""
        desc_tag = (soup.find("meta", attrs={"name": "description"}) or
                    soup.find("meta", attrs={"property": "og:description"}))
        if desc_tag:
            description = desc_tag.get("content", "")[:200]

        favicon_url = ""
        icon_tag = soup.find("link", rel=lambda r: r and "icon" in r)
        if icon_tag and icon_tag.get("href"):
            href = icon_tag["href"]
            parsed = urlparse(url)
            favicon_url = href if href.startswith("http") else f"{parsed.scheme}://{parsed.netloc}{href}"

        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript", "svg"]):
            tag.decompose()

        raw_html = resp.text
        clean_text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
        clean_text = "\n".join(lines)
        title = soup.title.string.strip() if soup.title else "No title"
        word_count = len(clean_text.split())
        read_time = max(1, round(word_count / 200))
        domain = urlparse(url).netloc
        token_estimate = len(clean_text) // 4

        return {
            "ok": True, "title": title, "description": description,
            "favicon_url": favicon_url, "domain": domain,
            "raw_html": raw_html, "clean_text": clean_text,
            "char_count": len(clean_text), "word_count": word_count,
            "read_time": read_time, "status_code": resp.status_code,
            "url": url, "scraped_at": datetime.now().strftime("%H:%M · %d %b %Y"),
            "token_estimate": token_estimate,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def chunk_text(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> list:
    words = text.split()
    chunks, current, total = [], [], 0
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


def build_system_prompt(page_context: str) -> str:
    chunks = chunk_text(page_context)
    snippet = chunks[0] if chunks else page_context
    return (
        "You are an expert web scraping AI assistant. "
        "Answer questions clearly and concisely based only on the page content below. "
        "If something isn't in the page content, say so honestly.\n\n"
        f"PAGE CONTENT:\n{snippet}"
    )


def get_auto_summary(api_key: str, model: str, text: str) -> str:
    client = Groq(api_key=api_key)
    chunks = chunk_text(text, max_chars=4000)
    prompt = (
        "Read the following webpage content and provide a concise summary in exactly "
        "3 bullet points. Each bullet should be one clear sentence. Start each with •\n\n"
        f"PAGE CONTENT:\n{chunks[0]}"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return resp.choices[0].message.content


def chat_with_groq(api_key: str, model: str, messages: list, system: str) -> str:
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}] + messages,
        max_tokens=2048,
    )
    return resp.choices[0].message.content


def export_chat_csv(messages: list) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Role", "Message"])
    for m in messages:
        writer.writerow([m["role"].capitalize(), m["content"]])
    return output.getvalue()


def export_chat_excel(messages: list, page_title: str) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Chat Export"
    ws.append(["Role", "Message"])
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 80
    for m in messages:
        ws.append([m["role"].capitalize(), m["content"]])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def token_bar_html(token_estimate: int, max_tokens: int = 8000) -> str:
    pct = min(100, round(token_estimate / max_tokens * 100))
    color = "#2d9a4e" if pct < 60 else ("#f4a261" if pct < 85 else "#e63946")
    bar_color = color
    return (
        f'<div class="token-label">Context used: ~{token_estimate:,} / {max_tokens:,} tokens ({pct}%)</div>'
        f'<div class="token-bar-wrap">'
        f'<div class="token-bar-fill" style="width:{pct}%; background:{bar_color};"></div>'
        f'</div>'
    )


# ─── Session state ───────────────────────────────────────────────────────────
for key, default in [
    ("scraped", None), ("chat_messages", []),
    ("chat_input", ""), ("scrape_history", []),
    ("auto_summary", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Dark/light mode toggle
    mode_label = "☀️ Light mode" if st.session_state.dark_mode else "🌙 Dark mode"
    if st.button(mode_label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("---")
    st.markdown("### 🕘 Scrape History")

    if not st.session_state.scrape_history:
        st.markdown(
            f"<p style='font-size:0.82rem;color:{T['text_muted']};'>No scrapes yet.</p>",
            unsafe_allow_html=True,
        )
    else:
        for i, item in enumerate(reversed(st.session_state.scrape_history)):
            idx = len(st.session_state.scrape_history) - 1 - i
            st.markdown(
                f'<div class="history-item">'
                f'<div class="history-domain">🌐 {item["domain"]}</div>'
                f'<div class="history-time">{item["scraped_at"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Load", key=f"load_{idx}"):
                st.session_state.scraped = item
                st.session_state.chat_messages = []
                st.session_state.auto_summary = item.get("summary", "")
                st.rerun()

        if st.button("🗑️ Clear history"):
            st.session_state.scrape_history = []
            st.rerun()

    # Token counter in sidebar when page is loaded
    if st.session_state.scraped and st.session_state.scraped.get("ok"):
        st.markdown("---")
        st.markdown("### 📊 Context Window")
        tok = st.session_state.scraped.get("token_estimate", 0)
        chat_tok = sum(len(m["content"]) // 4 for m in st.session_state.chat_messages)
        total_tok = tok + chat_tok
        st.markdown(token_bar_html(total_tok), unsafe_allow_html=True)


# ─── Main UI ─────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">AI Web Scraper</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">// powered by groq · beautifulsoup · streamlit</div>', unsafe_allow_html=True)

# ─── API Key ─────────────────────────────────────────────────────────────────
groq_api_key = os.environ.get("GROQ_API_KEY", "")
if not groq_api_key:
    groq_api_key = st.text_input(
        "Groq API Key:", type="password",
        placeholder="gsk_...", help="Get your free key at console.groq.com",
    )
if not groq_api_key:
    st.markdown(
        f'<div class="status-card info">ℹ️ Enter your Groq API key above. '
        f'Get a free key at <b>console.groq.com</b></div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ─── URL + Model ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])
with col_left:
    url = st.text_input("Enter a Website URL:", placeholder="https://quotes.toscrape.com")
with col_right:
    selected_model = st.selectbox("Groq Model:", GROQ_MODELS)

scrape_btn = st.button("🔍 Scrape Site")

# ─── Scrape ──────────────────────────────────────────────────────────────────
if scrape_btn:
    if not url or not url.startswith("http"):
        st.error("⚠️ Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("Scraping the website…"):
            result = scrape_website(url)

        if result["ok"]:
            with st.spinner("✨ Generating summary…"):
                try:
                    summary = get_auto_summary(groq_api_key, selected_model, result["clean_text"])
                    result["summary"] = summary
                    st.session_state.auto_summary = summary
                except Exception:
                    result["summary"] = ""
                    st.session_state.auto_summary = ""

            st.session_state.scraped = result
            st.session_state.chat_messages = []

            existing_urls = [h["url"] for h in st.session_state.scrape_history]
            if url not in existing_urls:
                st.session_state.scrape_history.append(result)

            st.markdown(
                f'<div class="status-card success">✅ &nbsp;<b>{result["title"]}</b> scraped successfully</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="stat-row">'
                f'<div class="stat-chip">Status <span>{result["status_code"]}</span></div>'
                f'<div class="stat-chip">Words <span>{result["word_count"]:,}</span></div>'
                f'<div class="stat-chip">Read time <span>~{result["read_time"]} min</span></div>'
                f'<div class="stat-chip">~Tokens <span>{result["token_estimate"]:,}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-card error">❌ Scrape failed: {result["error"]}</div>',
                unsafe_allow_html=True,
            )

# ─── Post-scrape UI ──────────────────────────────────────────────────────────
if st.session_state.scraped and st.session_state.scraped.get("ok"):
    data = st.session_state.scraped

    # ── Metadata card ─────────────────────────────────────────────────────
    favicon_html = (
        f'<img src="{data["favicon_url"]}" class="meta-favicon" onerror="this.style.display=\'none\'">'
        if data.get("favicon_url") else ""
    )
    desc_html = f'<div class="meta-desc">{data["description"]}</div>' if data.get("description") else ""
    st.markdown(
        f'<div class="meta-card">'
        f'{favicon_html}'
        f'<div class="meta-info">'
        f'<div class="meta-title">{data["title"]}</div>'
        f'{desc_html}'
        f'<div class="meta-chips">'
        f'<span class="meta-chip">🌐 {data["domain"]}</span>'
        f'<span class="meta-chip">🕐 {data["scraped_at"]}</span>'
        f'<span class="meta-chip">📖 ~{data["read_time"]} min read</span>'
        f'<span class="meta-chip"><b>{data["word_count"]:,}</b> words</span>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    # ── Auto summary ──────────────────────────────────────────────────────
    if st.session_state.auto_summary:
        st.markdown('<div class="summary-label">✨ AI Page Summary</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="summary-box">{st.session_state.auto_summary}</div>',
            unsafe_allow_html=True,
        )

    # ── DOM viewer ────────────────────────────────────────────────────────
    with st.expander("📄 View DOM Content", expanded=False):
        tab1, tab2 = st.tabs(["Clean Text", "Raw HTML"])
        with tab1:
            st.text_area("", data["clean_text"], height=280, label_visibility="collapsed")
        with tab2:
            st.code(
                data["raw_html"][:8000] + ("\n…[truncated]" if len(data["raw_html"]) > 8000 else ""),
                language="html",
            )

    st.markdown("---")

    # ── Chat section ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">💬 Chat with this page</div>', unsafe_allow_html=True)

    # Suggested prompts
    if not st.session_state.chat_messages:
        st.markdown(
            f"<p style='font-size:0.82rem;color:{T['text_muted']};margin-bottom:8px;'>Try asking:</p>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(SUGGESTED_PROMPTS))
        for i, suggestion in enumerate(SUGGESTED_PROMPTS):
            with cols[i]:
                if st.button(suggestion, key=f"suggest_{i}"):
                    st.session_state.chat_messages.append({"role": "user", "content": suggestion})
                    with st.spinner("Thinking…"):
                        try:
                            system = build_system_prompt(data["clean_text"])
                            reply = chat_with_groq(groq_api_key, selected_model,
                                                   st.session_state.chat_messages, system)
                            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                            st.session_state.chat_input = ""
                        except Exception as e:
                            st.error(f"Groq error: {e}")
                    st.rerun()

    # Chat bubbles - render each message individually to avoid HTML injection
    if st.session_state.chat_messages:
        for idx, msg in enumerate(st.session_state.chat_messages):
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="text-align:right;margin-bottom:12px;">'                    f'<div class="bubble-label user-label">You</div>'                    f'<div class="chat-bubble bubble-user">{msg["content"]}</div>'                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="margin-bottom:4px;">'                    '<div class="bubble-label">AI</div></div>',
                    unsafe_allow_html=True,
                )
                # Use st.chat_message style container for safe rendering
                with st.container():
                    st.markdown(
                        f'<div class="chat-bubble bubble-ai">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                col_copy, _ = st.columns([1, 5])
                with col_copy:
                    if st.button("📋 Copy", key=f"copy_{idx}"):
                        st.code(msg["content"])


    # Chat input
    chat_col, btn_col = st.columns([5, 1])
    with chat_col:
        user_input = st.text_input(
            "", value=st.session_state.chat_input,
            placeholder="Ask anything about this page…",
            label_visibility="collapsed", key="chat_text_input",
        )
    with btn_col:
        send_btn = st.button("Send ➤")

    # Actions row
    if st.session_state.chat_messages:
        a1, a2, a3, a4 = st.columns([1, 1, 1, 2])
        with a1:
            if st.button("🗑️ Clear"):
                st.session_state.chat_messages = []
                st.session_state.chat_input = ""
                st.rerun()
        with a2:
            st.download_button(
                "⬇️ CSV", export_chat_csv(st.session_state.chat_messages),
                "chat_export.csv", "text/csv", key="dl_csv",
            )
        with a3:
            if EXCEL_AVAILABLE:
                excel_data = export_chat_excel(
                    st.session_state.chat_messages, data.get("title", "page")
                )
                st.download_button(
                    "📊 Excel", excel_data,
                    "chat_export.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_excel",
                )

    # Handle send
    if send_btn and user_input.strip():
        st.session_state.chat_messages.append({"role": "user", "content": user_input.strip()})
        st.session_state.chat_input = ""
        with st.spinner("Thinking…"):
            try:
                system = build_system_prompt(data["clean_text"])
                reply = chat_with_groq(
                    groq_api_key, selected_model,
                    st.session_state.chat_messages, system,
                )
                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                st.rerun()
            except Exception as e:
                err = str(e)
                if "api_key" in err.lower() or "401" in err or "403" in err:
                    st.markdown(
                        '<div class="status-card error">❌ Invalid Groq API key.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(f"Groq error: {err}")