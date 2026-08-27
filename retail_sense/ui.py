"""RetailSense Stitch design-system helpers for the Streamlit front end."""

from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UI_THEMES = ("薄荷青灰", "手帐风格")

_THEME_TOKENS = {
    "手帐风格": {
        "bg": "#fdf6ec",
        "font": "\"ZCOOL KuaiLe\", \"Nunito\"",
        "font_display": "\"ZCOOL KuaiLe\", \"Nunito\"",
        "surface_lowest": "#fffdf8",
        "surface_low": "#f8f0e3",
        "surface": "#ffffff",
        "surface_high": "#f3e8d8",
        "surface_highest": "#eadcc8",
        "text": "#5c4a3a",
        "muted": "#a08b78",
        "coral": "#e2534f",
        "coral_soft": "#c0392b",
        "green": "#65a30d",
        "purple": "#b8a5d6",
        "danger": "#e2534f",
        "glass": "rgba(255,255,255,.72)",
        "glass_strong": "rgba(255,255,255,.88)",
        "background": "radial-gradient(circle at 12% 20%, rgba(233,179,76,.10) 0, transparent 45%), radial-gradient(circle at 88% 80%, rgba(226,83,79,.08) 0, transparent 45%), linear-gradient(145deg, #fdf6ec 0%, #faf0e2 55%, #f7ecdc 100%)",
        "header": "rgba(255,249,238,.88)",
        "sidebar": "rgba(255,249,238,.92)",
        "panel": "rgba(255,253,248,.90)",
        "popover": "rgba(255,253,248,.97)",
    },
    "薄荷青灰": {
        "bg": "#d3dfdc",
        "font": "Hanken Grotesk",
        "font_display": "Manrope",
        "surface_lowest": "#f5faf8",
        "surface_low": "#e6f0ed",
        "surface": "#fbfefd",
        "surface_high": "#d1e2dd",
        "surface_highest": "#c2d4cf",
        "text": "#263c3b",
        "muted": "#495f5d",
        "coral": "#dc6c5d",
        "coral_soft": "#ad493e",
        "green": "#167f63",
        "purple": "#656ba0",
        "danger": "#c04c55",
        "glass": "rgba(247,255,252,.48)",
        "glass_strong": "rgba(249,255,253,.70)",
        "background": "radial-gradient(circle at 12% 40%, rgba(112,188,168,.32) 0, transparent 42%), radial-gradient(circle at 88% 18%, rgba(149,163,214,.26) 0, transparent 40%), radial-gradient(circle at 72% 100%, rgba(255,161,145,.20) 0, transparent 38%), linear-gradient(145deg, #e9f3f0 0%, #d3dfdc 54%, #d8dfe7 100%)",
        "header": "rgba(234,245,241,.74)",
        "sidebar": "rgba(223,237,233,.84)",
        "panel": "rgba(242,250,247,.74)",
        "popover": "rgba(244,251,249,.97)",
    },
}


def _image_data_uri(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    if not path.is_file():
        return ""
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inject_design_system(base_font_px: int = 13, theme: str = UI_THEMES[0]) -> None:
    """Apply the Stitch glassmorphism tokens to native Streamlit widgets."""
    tokens = _THEME_TOKENS.get(theme, _THEME_TOKENS[UI_THEMES[0]])

    # 各主题的选中态样式（对齐各自模拟页）
    if theme == "手帐风格":
        nav_active = "background: rgba(246,227,200,.75) !important; box-shadow: none !important; border-radius: 14px;"
    else:
        nav_active = "background: linear-gradient(rgba(255,127,110,.14), rgba(255,127,110,.14)) padding-box, var(--rs-glass-edge) border-box; box-shadow: inset 3px 0 0 var(--rs-coral), inset 0 1px 0 rgba(255,255,255,.14);"

    # 手帐风 · 可爱便签质感（更大圆角 + 胶囊按钮 + 虚线便签边）
    journal_extra = ""
    if theme == "手帐风格":
        journal_extra = """
        /* ── 手帐风 · 可爱便签感 ── */
        [data-testid="stVerticalBlockBorderWrapper"] > div,
        [data-testid="stMetric"],
        .rs-welcome-panel {
            border-radius: 20px !important;
        }
        [data-testid="stButton"] button,
        [data-testid="stFormSubmitButton"] button {
            border-radius: 999px !important;
        }
        [data-testid="stMetric"] {
            border: 1px dashed rgba(194,57,43,.28) !important;
        }
        """
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Hanken+Grotesk:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&family=Inter:wght@400;500;600;700;800&family=Nunito:wght@400;600;700;800;900&family=JetBrains+Mono:wght@600;700&family=ZCOOL+KuaiLe&family=Noto+Sans+SC:wght@400;500;600;700&family=Material+Symbols+Outlined:wght@300;400;500&display=swap');

        :root {{
            --rs-bg: {tokens["bg"]};
            --rs-surface-lowest: {tokens["surface_lowest"]};
            --rs-surface-low: {tokens["surface_low"]};
            --rs-surface: {tokens["surface"]};
            --rs-surface-high: {tokens["surface_high"]};
            --rs-surface-highest: {tokens["surface_highest"]};
            --rs-text: {tokens["text"]};
            --rs-muted: {tokens["muted"]};
            --rs-outline: rgba(255,255,255,.18);
            --rs-outline-strong: rgba(255,255,255,.34);
            --rs-glass: {tokens["glass"]};
            --rs-glass-strong: {tokens["glass_strong"]};
            --rs-glass-edge: linear-gradient(135deg, rgba(255,255,255,.75), rgba(255,255,255,.35) 45%, rgba(255,255,255,.60));
            --rs-coral: {tokens["coral"]};
            --rs-coral-soft: {tokens["coral_soft"]};
            --rs-green: {tokens["green"]};
            --rs-purple: {tokens["purple"]};
            --rs-danger: {tokens["danger"]};
            --rs-radius: 16px;
            --rs-font-size: {base_font_px}px;
            --rs-font: {tokens["font"]}, sans-serif;
            --rs-font-display: {tokens["font_display"]}, sans-serif;
            --rs-warn: #e6a23c;
        }}

        html, body, [class*="css"] {{
            font-family: {tokens["font"]}, sans-serif;
            font-size: var(--rs-font-size);
            color: var(--rs-text);
        }}
        .stApp {{
            color: var(--rs-text);
            color-scheme: light;
            background-color: var(--rs-bg);
            background-image: {tokens["background"]};
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background: {tokens["header"]};
            backdrop-filter: blur(12px) saturate(1.3);
            border-bottom: 1px solid rgba(255,255,255,.16);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
        }}
        [data-testid="stToolbar"], #MainMenu, footer {{ visibility: hidden; }}
        .block-container {{
            max-width: 1280px;
            padding: 2.2rem 2.5rem 4rem;
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: {tokens["font_display"]}, sans-serif !important;
            color: var(--rs-text) !important;
            letter-spacing: -.015em;
        }}
        h1 {{ font-size: {base_font_px + 18}px !important; font-weight: 700 !important; }}
        h2 {{ font-size: {base_font_px + 10}px !important; font-weight: 650 !important; }}
        h3 {{ font-size: {base_font_px + 4}px !important; font-weight: 650 !important; }}
        h4 {{ font-size: {base_font_px + 2}px !important; font-weight: 650 !important; }}
        p, label, .stCaption {{ color: var(--rs-muted); }}
        a {{ color: var(--rs-green); }}
        hr {{ border-color: rgba(255,255,255,.07) !important; }}

        [data-testid="stSidebar"] {{
            width: 240px !important;
            min-width: 240px !important;
            background: {tokens["sidebar"]};
            border-right: 1px solid rgba(255,255,255,.20);
            backdrop-filter: blur(14px) saturate(1.35);
            box-shadow: inset -1px 0 0 rgba(255,255,255,.06), 12px 0 42px rgba(16,14,20,.16);
        }}
        [data-testid="stSidebarContent"] {{ padding: 1.3rem .8rem 1rem; }}
        [data-testid="stSidebar"] h1 {{ color: var(--rs-green) !important; }}
        [data-testid="stSidebar"] [data-testid="stImage"] img {{
            max-height: 86px;
            object-fit: cover;
            opacity: .64;
            border-radius: var(--rs-radius);
            filter: saturate(.7) contrast(1.05);
        }}
        .rs-sidebar-brand {{ padding: .3rem .55rem 1rem; }}
        .rs-sidebar-brand__name {{
            font: 800 22px/1 {tokens["font_display"]}, sans-serif;
            color: var(--rs-green);
            letter-spacing: -.04em;
        }}
        .rs-sidebar-brand__sub {{
            margin-top: 7px;
            color: var(--rs-muted);
            font: 600 10px/1 {tokens["font"]}, sans-serif;
            text-transform: uppercase;
            letter-spacing: .12em;
        }}
        .rs-nav-group {{
            padding: 12px 10px 4px;
            color: var(--rs-muted);
            opacity: .72;
            font: 600 9px/1 {tokens["font"]}, sans-serif;
            text-transform: uppercase;
            letter-spacing: .16em;
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] button {{
            min-height: 38px;
            justify-content: flex-start;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid transparent;
            color: var(--rs-muted);
            background: transparent;
            box-shadow: none;
            font: 500 .86rem/1 {tokens["font"]}, sans-serif;
            transition: .18s ease;
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
            color: var(--rs-text);
            background: rgba(255,255,255,.10);
            border-color: rgba(255,255,255,.18);
            transform: none;
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {{
            color: var(--rs-coral-soft);
            {nav_active}
            border-color: transparent;
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {{
            color: var(--rs-text) !important;
            background: rgba(255,255,255,.22) !important;
            border: 1px solid rgba(255,255,255,.46) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.38), 0 7px 20px rgba(55,43,48,.07) !important;
        }}

        [data-testid="stButton"] button,
        [data-testid="stFormSubmitButton"] button,
        [data-testid="stDownloadButton"] button,
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"] {{
            min-height: 42px;
            border-radius: 8px !important;
            border: 1px solid transparent !important;
            background: linear-gradient(rgba(255,255,255,.08), rgba(255,255,255,.08)) padding-box, var(--rs-glass-edge) border-box !important;
            color: var(--rs-text) !important;
            font: 600 .83rem/1 {tokens["font"]}, sans-serif !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.14), 0 8px 24px rgba(13,12,16,.10) !important;
            backdrop-filter: blur(9px) saturate(1.3);
            transition: transform .18s ease, border-color .18s ease, background .18s ease !important;
        }}
        [data-testid="stButton"] button:hover,
        [data-testid="stFormSubmitButton"] button:hover,
        [data-testid="stDownloadButton"] button:hover {{
            transform: translateY(-1px);
            border-color: transparent !important;
            background: linear-gradient(rgba(255,255,255,.14), rgba(255,255,255,.14)) padding-box, var(--rs-glass-edge) border-box !important;
        }}
        [data-testid="stButton"] button[kind="primary"],
        [data-testid="stFormSubmitButton"] button[kind="primary"],
        [data-testid="stDownloadButton"] button[kind="primary"] {{
            border-color: rgba(255,255,255,.28) !important;
            background: linear-gradient(135deg, var(--rs-coral), var(--rs-coral-soft)) !important;
            color: #ffffff !important;
            box-shadow: 0 10px 28px rgba(255,127,110,.16) !important;
        }}
        [data-testid="stButton"] button:focus-visible,
        input:focus-visible, textarea:focus-visible, [role="combobox"]:focus-visible {{
            outline: 2px solid var(--rs-coral) !important;
            outline-offset: 2px;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] > div,
        [data-testid="stExpander"],
        [data-testid="stMetric"] {{
            background: linear-gradient(var(--rs-glass), var(--rs-glass)) padding-box, var(--rs-glass-edge) border-box !important;
            border: 1px solid transparent !important;
            border-radius: var(--rs-radius) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.50), 0 1px 2px rgba(0,0,0,.03), 0 2px 6px rgba(0,0,0,.03), 0 8px 20px rgba(0,0,0,.05) !important;
            backdrop-filter: blur(12px) saturate(1.35);
            transition: border-color .2s ease, background .2s ease;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] > div:hover,
        [data-testid="stMetric"]:hover {{
            border-color: transparent !important;
            background: linear-gradient(var(--rs-glass-strong), var(--rs-glass-strong)) padding-box, var(--rs-glass-edge) border-box !important;
        }}
        [data-testid="stMetric"] {{ padding: 16px 18px; min-height: 112px; }}
        [data-testid="stMetricLabel"] {{
            color: var(--rs-muted);
            font: 600 10px/1 {tokens["font"]}, sans-serif;
            text-transform: uppercase;
            letter-spacing: .10em;
        }}
        [data-testid="stMetricValue"] {{
            color: var(--rs-text);
            font: 650 1.65rem/1.2 {tokens["font_display"]}, sans-serif;
        }}
        [data-testid="stMetricDelta"] {{ font-size: .72rem; }}

        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        [data-baseweb="select"] > div {{
            color: #332f37 !important;
            -webkit-text-fill-color: #332f37 !important;
            background: linear-gradient(rgba(255,255,255,.72), rgba(255,255,255,.72)) padding-box, var(--rs-glass-edge) border-box !important;
            background-color: rgba(255,255,255,.62) !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12) !important;
            backdrop-filter: blur(8px) saturate(1.25);
        }}
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: rgba(51,47,55,.48); -webkit-text-fill-color: rgba(51,47,55,.48); }}
        .stTextInput [data-baseweb="input"],
        .stNumberInput [data-baseweb="input"] {{
            min-height: 56px;
            overflow: hidden;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            background: linear-gradient(rgba(255,250,249,.76), rgba(250,246,250,.72)) padding-box, linear-gradient(135deg, rgba(255,255,255,.86), rgba(255,127,110,.30), rgba(206,189,255,.42)) border-box !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.82), 0 8px 24px rgba(27,22,30,.10) !important;
            backdrop-filter: blur(9px) saturate(1.25);
            transition: transform .18s ease, box-shadow .18s ease;
        }}
        .stTextInput [data-baseweb="input"]:focus-within,
        .stNumberInput [data-baseweb="input"]:focus-within {{
            transform: translateY(-1px);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.90), 0 0 0 3px rgba(255,127,110,.16), 0 12px 28px rgba(27,22,30,.13) !important;
        }}
        .stTextInput [data-baseweb="input"] input,
        .stNumberInput [data-baseweb="input"] input {{
            min-height: 52px;
            padding-left: 16px !important;
            background: transparent !important;
            background-color: transparent !important;
            border: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
        }}
        .stTextInput label, .stNumberInput label, .stTextArea label, .stSelectbox label {{
            margin-bottom: 7px;
            color: var(--rs-muted) !important;
            font: 600 11px/1.2 {tokens["font"]}, sans-serif !important;
            letter-spacing: .02em;
        }}
        [data-baseweb="select"] > div {{
            min-height: 50px;
            padding-left: 7px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.82), 0 8px 24px rgba(27,22,30,.10) !important;
        }}
        [data-baseweb="popover"], [role="listbox"] {{ background: {tokens["popover"]} !important; backdrop-filter: blur(10px); }}
        [role="option"] {{ color: var(--rs-text) !important; }}
        .stSlider [data-baseweb="slider"] [role="slider"] {{ background: var(--rs-coral) !important; }}
        .stSlider [data-testid="stThumbValue"] {{ color: var(--rs-coral-soft) !important; }}
        [data-testid="stCheckbox"] svg, [data-testid="stRadio"] svg {{ color: var(--rs-coral) !important; }}

        [data-testid="stTabs"] [role="tablist"] {{
            gap: 18px;
            border-bottom: 1px solid rgba(255,255,255,.18);
        }}
        [data-testid="stTabs"] [role="tab"] {{
            color: var(--rs-muted);
            font-family: {tokens["font"]}, sans-serif;
        }}
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
            color: var(--rs-coral-soft);
            border-bottom-color: var(--rs-coral) !important;
        }}
        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            border: 1px solid rgba(255,255,255,.22);
            border-radius: var(--rs-radius);
            overflow: hidden;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 12px 30px rgba(12,11,15,.12);
        }}
        [data-testid="stDataFrame"] canvas {{ filter: none; }}
        [data-testid="stChatMessage"] {{
            border: 1px solid transparent;
            background: linear-gradient(var(--rs-glass), var(--rs-glass)) padding-box, var(--rs-glass-edge) border-box;
            border-radius: 10px;
            backdrop-filter: blur(10px) saturate(1.3);
        }}
        [data-testid="stAlert"] {{
            background: linear-gradient(var(--rs-glass), var(--rs-glass)) padding-box, var(--rs-glass-edge) border-box;
            border: 1px solid transparent;
            border-radius: var(--rs-radius);
            color: var(--rs-text);
            backdrop-filter: blur(10px) saturate(1.3);
        }}

        .card-hover {{
            border: 1px solid transparent !important;
            border-radius: var(--rs-radius) !important;
            padding: 16px !important;
            background: linear-gradient(var(--rs-glass), var(--rs-glass)) padding-box, var(--rs-glass-edge) border-box !important;
            color: var(--rs-text) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.50), 0 1px 2px rgba(0,0,0,.03), 0 2px 6px rgba(0,0,0,.03), 0 8px 20px rgba(0,0,0,.05);
            backdrop-filter: blur(12px) saturate(1.35);
            transition: .2s ease;
        }}
        .card-hover:hover {{
            transform: translateY(-2px);
            border-color: transparent !important;
            background: linear-gradient(var(--rs-glass-strong), var(--rs-glass-strong)) padding-box, var(--rs-glass-edge) border-box !important;
        }}
        .card-hover.ok {{ border-left: 3px solid var(--rs-green) !important; }}
        .card-hover.warn {{ border-left: 3px solid #ffd166 !important; }}
        .card-hover.danger {{ border-left: 3px solid var(--rs-danger) !important; }}
        .rs-case-feedback {{
            max-width: 100%;
            margin: 10px 0 0;
            padding: 14px 15px;
            border-left: 3px solid var(--rs-coral);
            border-radius: 0 10px 10px 0;
            background: rgba(255,255,255,.26);
            color: var(--rs-muted);
            font-style: italic;
            line-height: 1.75;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: break-word;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] .stMarkdown,
        [data-testid="stExpander"] .stMarkdown {{
            min-width: 0;
            max-width: 100%;
            overflow-wrap: anywhere;
        }}

        .rs-page-header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 24px;
            margin: 0 0 24px;
        }}
        .rs-page-header__code {{
            color: var(--rs-coral-soft);
            font: 700 10px/1 {tokens["font"]}, sans-serif;
            letter-spacing: .14em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .rs-page-header h1 {{ margin: 0 0 8px; }}
        .rs-page-header p {{ margin: 0; max-width: 720px; color: var(--rs-muted); }}
        .rs-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
            padding: 7px 10px;
            border: 1px solid rgba(74,225,131,.25);
            border-radius: 999px;
            background: rgba(74,225,131,.08);
            color: var(--rs-green);
            font: 600 10px/1 {tokens["font"]}, sans-serif;
            letter-spacing: .04em;
        }}
        .rs-badge--coral {{
            color: var(--rs-coral-soft);
            border-color: rgba(255,127,110,.28);
            background: rgba(255,127,110,.08);
        }}
        .rs-badge--purple {{
            color: var(--rs-purple);
            border-color: rgba(206,189,255,.26);
            background: rgba(206,189,255,.08);
        }}
        .rs-section-label {{
            margin: 22px 0 12px;
            color: var(--rs-muted);
            font: 650 10px/1 {tokens["font"]}, sans-serif;
            text-transform: uppercase;
            letter-spacing: .13em;
        }}
        .rs-info-strip {{
            display: flex;
            align-items: center;
            gap: 9px;
            margin: 0 0 18px;
            padding: 10px 12px;
            border: 1px solid transparent;
            border-radius: 8px;
            background: linear-gradient(rgba(255,127,110,.10), rgba(255,127,110,.10)) padding-box, var(--rs-glass-edge) border-box;
            color: var(--rs-coral-soft);
            font: 600 11px/1.4 {tokens["font"]}, sans-serif;
            backdrop-filter: blur(9px) saturate(1.3);
        }}
        .material-symbols-outlined {{
            font-family: "Material Symbols Outlined";
            font-size: 18px;
            font-weight: normal;
            line-height: 1;
        }}

        [data-testid="stHorizontalBlock"]:has(.rs-login-hero) {{
            max-width: 1220px;
            min-height: 640px;
            margin: 3vh auto 0;
            gap: 24px;
            overflow: visible;
            border: 0;
            border-radius: 0;
            background: transparent;
            box-shadow: none;
            backdrop-filter: none;
        }}
        [data-testid="stHorizontalBlock"]:has(.rs-login-hero) > [data-testid="column"] {{
            padding: 0;
        }}
        [data-testid="column"]:has(.rs-login-form-title) {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 46px 54px !important;
            background: {tokens["panel"]};
            border: 1px solid transparent;
            border-radius: 16px;
            background: linear-gradient({tokens["panel"]}, {tokens["panel"]}) padding-box, var(--rs-glass-edge) border-box;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 1px 2px rgba(0,0,0,.03), 0 2px 6px rgba(0,0,0,.03), 0 12px 28px rgba(0,0,0,.05);
            backdrop-filter: blur(14px) saturate(1.3);
        }}
        .rs-login-hero {{
            min-height: 640px;
            padding: 34px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background-size: cover;
            background-position: center;
            position: relative;
            isolation: isolate;
            overflow: hidden;
            border: 1px solid transparent;
            border-radius: 16px;
            background-clip: padding-box;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.22), 0 1px 2px rgba(0,0,0,.03), 0 2px 6px rgba(0,0,0,.03), 0 12px 28px rgba(0,0,0,.05);
        }}
        .rs-login-hero::before {{
            content: "";
            position: absolute;
            inset: 0;
            z-index: -1;
            background: linear-gradient(180deg, rgba(35,30,27,.01), rgba(32,27,28,.32));
        }}
        .rs-login-hero > div:first-child {{
            width: fit-content;
            max-width: 410px;
            padding: 16px 18px;
            border: 1px solid transparent;
            border-radius: 12px;
            background: linear-gradient(rgba(44,38,40,.36), rgba(44,38,40,.36)) padding-box, linear-gradient(135deg, rgba(255,255,255,.74), rgba(255,255,255,.14), var(--rs-coral)) border-box;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 14px 38px rgba(38,23,20,.12);
            backdrop-filter: blur(9px) saturate(1.3);
        }}
        .rs-login-brand {{
            color: #ffffff;
            font: 800 2rem/1 {tokens["font_display"]}, sans-serif;
            letter-spacing: -.04em;
            text-shadow: 0 2px 18px rgba(26,17,18,.34);
        }}
        .rs-login-tagline {{ margin-top: 9px; color: #fff; font-size: 1rem; text-shadow: 0 2px 14px rgba(26,17,18,.36); }}
        .rs-login-quote {{
            max-width: 400px;
            padding: 17px 18px;
            border: 1px solid transparent;
            border-radius: 9px;
            background: linear-gradient(rgba(40,34,36,.42), rgba(40,34,36,.42)) padding-box, linear-gradient(135deg, rgba(255,255,255,.70), rgba(255,255,255,.16), var(--rs-coral)) border-box;
            color: #fff;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 14px 40px rgba(38,23,20,.14);
            backdrop-filter: blur(10px) saturate(1.25);
        }}
        .rs-login-capabilities {{ display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }}
        .rs-login-capabilities span {{
            padding: 6px 9px;
            border-radius: 999px;
            background: linear-gradient(rgba(74,225,131,.13), rgba(74,225,131,.13)) padding-box, linear-gradient(135deg, rgba(255,255,255,.42), rgba(74,225,131,.26)) border-box;
            border: 1px solid transparent;
            color: var(--rs-green);
            font: 600 10px/1 {tokens["font"]}, sans-serif;
        }}
        .rs-login-form-title h2 {{ margin: 0 0 6px; font-size: 1.55rem !important; }}
        .rs-login-form-title p {{ margin: 0 0 20px; }}
        .login-footer-text {{
            margin-top: 24px;
            color: var(--rs-muted);
            font-size: .72rem;
            line-height: 1.55;
            text-align: center;
        }}

        .rs-welcome-panel {{
            position: relative;
            overflow: hidden;
            padding: 28px 30px;
            border: 1px solid transparent;
            border-radius: 12px;
            background: linear-gradient(var(--rs-glass), var(--rs-glass)) padding-box, var(--rs-glass-edge) border-box;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.16), 0 16px 38px rgba(12,11,15,.13);
            backdrop-filter: blur(12px) saturate(1.35);
        }}
        .rs-welcome-panel::after {{
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            right: -40px;
            top: -70px;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(255,127,110,.22), rgba(174,148,255,.18));
            filter: blur(35px);
        }}
        .rs-welcome-panel h2 {{ margin: 10px 0 6px; font-size: 2.25rem !important; }}
        .rs-welcome-panel p {{ max-width: 680px; margin: 0; }}

        .rs-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin: 6px 0 12px;
        }}
        .rs-kpi {{
            padding: 20px 22px;
            border-radius: var(--rs-radius);
            background: linear-gradient(var(--rs-glass), var(--rs-glass)) padding-box, var(--rs-glass-edge) border-box;
            border: 1px solid transparent;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.50), 0 1px 2px rgba(0,0,0,.03), 0 2px 6px rgba(0,0,0,.03), 0 8px 20px rgba(0,0,0,.05);
            backdrop-filter: blur(12px) saturate(1.35);
        }}
        .rs-kpi__label {{
            font: 600 10px/1 {tokens["font"]}, sans-serif;
            color: var(--rs-muted);
            text-transform: uppercase;
            letter-spacing: .1em;
            margin-bottom: 10px;
        }}
        .rs-kpi__value {{
            font: 800 27px/1.1 {tokens["font_display"]}, sans-serif;
            color: var(--rs-text);
            letter-spacing: -.02em;
        }}
        .rs-kpi__sub {{
            margin-top: 9px;
            font: 600 11px/1 {tokens["font"]}, sans-serif;
        }}
        .rs-kpi--coral .rs-kpi__sub {{ color: var(--rs-coral-soft); }}
        .rs-kpi--green .rs-kpi__sub {{ color: var(--rs-green); }}
        .rs-kpi--purple .rs-kpi__sub {{ color: var(--rs-purple); }}
        .rs-kpi--warn .rs-kpi__sub {{ color: var(--rs-warn); }}

        .export-download-area {{
            padding: 24px 20px !important;
            border: 1px solid transparent !important;
            border-radius: 12px !important;
            background: linear-gradient(rgba(255,127,110,.10), rgba(255,127,110,.10)) padding-box, var(--rs-glass-edge) border-box !important;
            backdrop-filter: blur(10px) saturate(1.3);
        }}
        .export-title {{ color: var(--rs-coral-soft) !important; }}

        @media (max-width: 900px) {{
            .block-container {{ padding: 1.5rem 1.15rem 3rem; }}
            [data-testid="stSidebar"] {{ width: 240px !important; min-width: 240px !important; }}
            [data-testid="stHorizontalBlock"]:has(.rs-login-hero) {{ min-height: auto; margin-top: 1vh; }}
            [data-testid="column"]:has(.rs-login-hero) {{ display: none; }}
            [data-testid="column"]:has(.rs-login-form-title) {{ padding: 38px 26px !important; border-left: 0; }}
            .rs-page-header {{ align-items: flex-start; flex-direction: column; gap: 12px; }}
        }}
        @media (max-width: 560px) {{
            .block-container {{ padding: 1rem .85rem 2.5rem; }}
            h1 {{ font-size: 1.65rem !important; }}
            [data-testid="stMetric"] {{ min-height: 96px; padding: 13px; }}
            [data-testid="stMetricValue"] {{ font-size: 1.35rem; }}
            [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {{ min-width: calc(50% - 8px) !important; flex: 1 1 calc(50% - 8px) !important; }}
            [data-testid="stHorizontalBlock"]:has(.rs-login-hero) > [data-testid="column"] {{ min-width: 100% !important; flex-basis: 100% !important; }}
            [data-testid="column"]:has(.rs-login-form-title) {{ padding: 30px 18px !important; }}
        }}
        {journal_extra}
        </style>
        """,
        unsafe_allow_html=True,
    )


def login_hero(is_english: bool = False) -> None:
    image = _image_data_uri("images/login-pet-hero-v2.png")
    title = "Retail selection, pricing and inventory decisions" if is_english else "零售选品、定价与库存决策工作台"
    quote = (
        "Turn retail experience into explainable decisions, from product selection to fulfillment."
        if is_english
        else "把零售经验转化为可解释的决策，从选品一路走到履约。"
    )
    st.markdown(
        f"""
        <div class="rs-login-hero" style="background-image:url('{image}')">
          <div>
            <div class="rs-login-brand">RetailSense</div>
            <div class="rs-login-tagline">{html.escape(title)}</div>
            <div class="rs-login-capabilities"><span>选品评分</span><span>利润红线</span><span>库存预警</span></div>
          </div>
          <div class="rs-login-quote">“{html.escape(quote)}”</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand(role_label: str) -> None:
    st.markdown(
        f"""
        <div class="rs-sidebar-brand">
          <div class="rs-sidebar-brand__name">RetailSense</div>
          <div class="rs-sidebar-brand__sub">{html.escape(role_label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_group(label: str) -> None:
    st.markdown(f'<div class="rs-nav-group">{html.escape(label)}</div>', unsafe_allow_html=True)


def page_header(code: str, title: str, subtitle: str, badge: str, tone: str = "green") -> None:
    tone_class = "" if tone == "green" else f" rs-badge--{tone}"
    st.markdown(
        f"""
        <div class="rs-page-header">
          <div>
            <div class="rs-page-header__code">{html.escape(code)}</div>
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
          </div>
          <span class="rs-badge{tone_class}"><span class="material-symbols-outlined">verified</span>{html.escape(badge)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(label: str) -> None:
    st.markdown(f'<div class="rs-section-label">{html.escape(label)}</div>', unsafe_allow_html=True)


def info_strip(message: str) -> None:
    st.markdown(
        f'<div class="rs-info-strip"><span class="material-symbols-outlined">info</span>{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )
