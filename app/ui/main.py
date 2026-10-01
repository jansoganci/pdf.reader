import html

import streamlit as st

from app.models import DocumentRecord, Dossier
from app.pdf.render import PdfRejected
from app.service import (
    correct_field,
    export_dossier,
    get_dossier,
    mark_export_with_errors,
    merge_document,
    page_image,
    process_upload,
    set_manual,
    split_document,
)
from app.ui.words import (
    FILE_MANUAL,
    LINE_MANUAL,
    PAPER_MANUAL,
    check_sentence,
    field_name,
    issued_by,
    money_text,
    pages_text,
    paper_name,
    shown_keys,
    shown_value,
)

@st.cache_data(show_spinner=False)
def _cached_page_image(dossier_id: str, page_number: int) -> bytes | None:
    return page_image(dossier_id, page_number)


st.set_page_config(page_title="Import file", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Design tokens — see docs/DESIGN_SYSTEM.md. Light values on :root; dark
       values repeated under both the OS media query and a [data-theme]
       attribute, so a manual theme toggle can be wired in later without
       touching a single color value anywhere else. */
    :root {
        --bg: #fafafa;
        --surface: #ffffff;
        --surface-sunken: #f4f4f5;
        --border: #e4e4e7;

        --ink: #18181b;
        --ink-secondary: #52525b;
        --ink-muted: #a1a1aa;

        --accent: #4f46e5;
        --accent-hover: #4338ca;
        --accent-text: #4f46e5;
        --accent-soft: #eef2ff;

        --good-text: #166534; --good-bg: #dcfce7; --good-strong: #16a34a;
        --warn-text: #92400e; --warn-bg: #fef3c7; --warn-strong: #f59e0b;
        --crit-text: #991b1b; --crit-bg: #fee2e2; --crit-strong: #dc2626;

        --radius-sm: 10px;
        --radius-md: 14px;
        --radius-lg: 20px;
        --shadow-sm: 0 1px 3px rgba(16,24,40,.08), 0 1px 2px rgba(16,24,40,.04);
        --shadow-md: 0 4px 12px rgba(16,24,40,.08), 0 2px 4px rgba(16,24,40,.04);
    }
    @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) {
            --bg: #0f0f12;
            --surface: #18181b;
            --surface-sunken: #0f0f12;
            --border: #2a2a2e;
            --ink: #f4f4f5;
            --ink-secondary: #a1a1aa;
            --ink-muted: #71717a;
            --accent-text: #a5b4fc;
            --accent-soft: #1e1b4b;
            --good-text: #4ade80; --good-bg: #14281d; --good-strong: #22c55e;
            --warn-text: #fbbf24; --warn-bg: #2b2111; --warn-strong: #f59e0b;
            --crit-text: #f87171; --crit-bg: #2c1515; --crit-strong: #ef4444;
            --shadow-sm: none;
            --shadow-md: none;
        }
    }
    :root[data-theme="dark"] {
        --bg: #0f0f12;
        --surface: #18181b;
        --surface-sunken: #0f0f12;
        --border: #2a2a2e;
        --ink: #f4f4f5;
        --ink-secondary: #a1a1aa;
        --ink-muted: #71717a;
        --accent-text: #a5b4fc;
        --accent-soft: #1e1b4b;
        --good-text: #4ade80; --good-bg: #14281d; --good-strong: #22c55e;
        --warn-text: #fbbf24; --warn-bg: #2b2111; --warn-strong: #f59e0b;
        --crit-text: #f87171; --crit-bg: #2c1515; --crit-strong: #ef4444;
        --shadow-sm: none;
        --shadow-md: none;
    }

    header, [data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
    [data-testid="stHeaderActionElements"], [data-testid="stHeadingWithActionElements"] a { display: none !important; }

    /* Base: color, ground, and type family. */
    .stApp {
        background: var(--bg);
        color: var(--ink);
        font-family: "Inter", -apple-system, "Segoe UI", sans-serif;
    }
    .stApp, .stApp input, .stApp textarea {
        font-variant-numeric: tabular-nums;
    }
    [data-testid="stWidgetLabel"] p { color: var(--ink) !important; }
    .block-container { padding: 1.25rem clamp(20px, 2.2vw, 48px) 3rem; max-width: none; }

    /* Equal-width tabs across the full row. The active underline is
       [data-baseweb="tab-highlight"]; live check showed it tracks the
       active tab with this flex rule, so it needs no extra offset. */
    [data-baseweb="tab-list"] { width: 100%; }
    [data-baseweb="tab"] { flex: 1 1 0; min-width: 0; color: var(--ink-secondary) !important; }
    [data-baseweb="tab"] p { color: inherit !important; }
    [data-baseweb="tab"][aria-selected="true"] { color: var(--accent-text) !important; }
    [data-baseweb="tab-highlight"] { background-color: var(--accent) !important; }

    /* The preview column sticks while the field column scrolls. Sticky on an
       inner div does not: Streamlit wraps that div in a short element box.
       The column itself is the box that has room to stick. top is small
       because this screen's header scrolls away (the Streamlit header is
       hidden). */
    .sticky-preview { display: none; }
    [data-testid="stColumn"]:has(.sticky-preview) {
        position: sticky;
        top: 16px;
        align-self: flex-start;
        height: fit-content;
        z-index: 2;
    }
    button { white-space: nowrap !important; }
    div[data-testid="stCaptionContainer"] { color: var(--ink-secondary) !important; }

    /* Buttons — full ownership of the three variants. Streamlit's API only
       exposes primary/secondary as button types; "ghost" from the design
       doc is merged into secondary here rather than hacked in per-button. */
    .stApp [data-testid="stBaseButton-primary"],
    .stApp [data-testid="stBaseButton-primaryFormSubmit"] {
        background: var(--accent) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 18px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stApp [data-testid="stBaseButton-primary"] *,
    .stApp [data-testid="stBaseButton-primaryFormSubmit"] * { color: #ffffff !important; }
    .stApp [data-testid="stBaseButton-primary"]:hover,
    .stApp [data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--accent-hover) !important; }

    .stApp [data-testid="stBaseButton-secondary"] {
        background: var(--surface) !important;
        color: var(--ink) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 18px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stApp [data-testid="stBaseButton-secondary"] * { color: var(--ink) !important; }
    .stApp [data-testid="stBaseButton-secondary"]:hover {
        border-color: var(--accent) !important;
        color: var(--accent-text) !important;
    }
    .stApp [data-testid="stBaseButton-secondary"]:hover * { color: var(--accent-text) !important; }
    .stApp button:disabled { opacity: .5 !important; }

    /* The dropzone does not follow data-theme on its own, so give it our
       surface and ink. Light text on that box was invisible in both themes. */
    .stApp [data-testid="stFileUploaderDropzone"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        color: var(--ink) !important;
    }
    .stApp [data-testid="stFileUploaderDropzone"] span { color: var(--ink-secondary) !important; }
    .stApp [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--ink) !important;
    }
    .stApp [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] * { color: var(--ink) !important; }

    /* Text inputs */
    .stApp [data-testid="stTextInputRootElement"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: none !important;
    }
    .stApp [data-testid="stTextInputRootElement"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(79,70,229,.35) !important;
    }
    .stApp [data-testid="stTextInput"] input {
        color: var(--ink) !important;
        padding: 10px 12px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
    }
    .stApp [data-testid="stTextInput"] input::placeholder { color: var(--ink-muted) !important; }
    /* An unnamed wrapper div inside the root still carries Streamlit's own
       dark fill — make it transparent so the root's background (above)
       actually shows instead of being hidden under it. */
    .stApp [data-testid="stTextInputRootElement"] > div { background: transparent !important; }

    /* Checkbox box (resting state only — the checked-mark keeps Streamlit's
       own rendering, this is a single lightly-used control). */
    .stApp [data-testid="stCheckbox"] span:first-of-type {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
    }

    [data-testid="stHeading"] h2 { font-size: 26px; line-height: 32px; font-weight: 700; letter-spacing: -0.01em; }
    [data-testid="stHeading"] h3 { font-size: 20px; line-height: 28px; font-weight: 600; }

    .banner { border-radius: var(--radius-lg); padding: 12px 16px 12px 18px; margin: 8px 0 16px;
              border-left: 4px solid; font-size: 15px; font-weight: 500;
              display: flex; align-items: center; gap: 10px; }
    .banner svg { flex: none; }
    .banner.good { background: var(--good-bg); color: var(--good-text); border-left-color: var(--good-strong); }
    .banner.warn { background: var(--warn-bg); color: var(--warn-text); border-left-color: var(--warn-strong); }
    .banner.crit { background: var(--crit-bg); color: var(--crit-text); border-left-color: var(--crit-strong); }

    .tag { display: inline-flex; align-items: center; gap: 6px; border-radius: var(--radius-sm);
           padding: 3px 10px; font-size: 12px; font-weight: 600; }
    .tag::before { content: ""; width: 6px; height: 6px; border-radius: 50%; flex: none; }
    .tag.warn { background: var(--warn-bg); color: var(--warn-text); }
    .tag.warn::before { background: var(--warn-strong); }
    .tag.crit { background: var(--crit-bg); color: var(--crit-text); }
    .tag.crit::before { background: var(--crit-strong); }

    .brand-mark-inline { width: 40px; height: 40px; flex: none; border-radius: var(--radius-sm);
                         background: var(--accent-soft); color: var(--accent-text);
                         display: flex; align-items: center; justify-content: center; font-size: 20px; }
    .status-pill { display: inline-flex; align-items: center; gap: 5px; border-radius: 999px;
                   padding: 2px 9px 2px 8px; font-size: 11.5px; font-weight: 600; }
    .status-pill::before { content: ""; width: 6px; height: 6px; border-radius: 50%; }
    .status-pill.crit { background: var(--crit-bg); color: var(--crit-text); }
    .status-pill.crit::before { background: var(--crit-strong); }
    .status-pill.warn { background: var(--warn-bg); color: var(--warn-text); }
    .status-pill.warn::before { background: var(--warn-strong); }
    .status-pill.good { background: var(--good-bg); color: var(--good-text); }
    .status-pill.good::before { background: var(--good-strong); }
    .strip-info { width: 18px; height: 18px; flex: none; border-radius: 50%; border: 1px solid var(--border);
                  color: var(--ink-muted); display: inline-flex; align-items: center; justify-content: center;
                  font-size: 11px; font-weight: 600; }
    .topbar-strip-marker { display: none; }
    [data-testid="stElementContainer"]:has(.topbar-strip-marker) + [data-testid="stElementContainer"] {
        background: var(--surface-sunken);
        border-top: 1px solid var(--border);
        padding: 9px 0;
    }
    [data-testid="stElementContainer"]:has(.topbar-strip-marker) + [data-testid="stElementContainer"] [data-testid="stHorizontalBlock"] {
        align-items: flex-end;
    }

    .group-title { font-weight: 600; font-size: 12px; text-transform: uppercase;
                   letter-spacing: 0.06em; color: var(--ink-secondary); margin: 12px 0 4px; }

    /* Summary cards */
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm); padding: 16px 18px; min-height: 108px; }
    .card-label { font-size: 13px; font-weight: 600; color: var(--ink-secondary); margin-bottom: 6px; }
    .card-amount { font-size: 22px; font-weight: 700; color: var(--ink); letter-spacing: -0.01em; }
    .card-sub { font-size: 13px; color: var(--ink-secondary); margin: 4px 0 8px; }

    /* The two-group form panel — own surface, lifted above the page */
    .stApp [data-testid="stForm"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-md) !important;
        padding: 24px !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

MONEY_KEYS = {
    "net_amount", "tax_amount", "total_amount", "fob_amount",
    "freight_amount", "customs_value", "insurance_amount",
}

_SVG_ATTRS = 'width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
_BANNER_ICONS = {
    "good": f'<svg {_SVG_ATTRS}><circle cx="8" cy="8" r="6.25"/><path d="M5.3 8.2l1.8 1.8 3.6-3.8"/></svg>',
    "warn": (
        f'<svg {_SVG_ATTRS}><path d="M8 2.2l6.3 11A1 1 0 0 1 13.4 15H2.6a1 1 0 0 1-.9-1.8z"/>'
        '<path d="M8 6.3v3"/><circle cx="8" cy="11.4" r="0.7" fill="currentColor" stroke="none"/></svg>'
    ),
    "crit": f'<svg {_SVG_ATTRS}><circle cx="8" cy="8" r="6.25"/><path d="M5.8 5.8l4.4 4.4M10.2 5.8l-4.4 4.4"/></svg>',
}


def _banner(tier: str, message: str) -> str:
    return f'<div class="banner {tier}">{_BANNER_ICONS[tier]}<span>{message}</span></div>'


def _currency(document: DocumentRecord, key: str) -> str | None:
    if key == "customs_value":
        return "MAD"
    if document.document_type == "customs_liquidation" and key in MONEY_KEYS:
        field = document.fields.get("currency")
        value = None if field is None else shown_value(field)
        return str(value) if value not in (None, "") else "MAD"
    field = document.fields.get("currency")
    if field is None:
        return None
    value = shown_value(field)
    return None if value in (None, "") else str(value)


def _display(document: DocumentRecord, key: str) -> str:
    field = document.fields.get(key)
    if field is None:
        return ""
    value = shown_value(field)
    if value in (None, ""):
        return ""
    if key in MONEY_KEYS:
        return money_text(value, _currency(document, key))
    if key == "exchange_rate":
        return str(value)
    return str(value)


def _headline_amount(document: DocumentRecord) -> str:
    for key in ("total_amount", "customs_value"):
        text = _display(document, key)
        if text:
            return text
    return ""


def _check_sentence(dossier: Dossier, item) -> str:
    names = []
    for document_id in item.fields:
        found = next((doc for doc in dossier.documents if doc.id == document_id), None)
        if found is not None:
            names.append(paper_name(found.document_type))
    paper = names[0] if len(names) == 1 else None
    if item.status == "passed":
        return f"{paper}: {item.message}" if paper else item.message
    return check_sentence(item.rule_id, item.message, paper)


def _tab_label(document: DocumentRecord) -> str:
    name = paper_name(document.document_type)
    needs_check = any(field.status == "review" for field in document.fields.values())
    return f"• {name}" if needs_check else name


def _default_page(document: DocumentRecord) -> int | None:
    """Open on the page a flagged field was actually read from. Fall back to
    the paper's first page when nothing needs a check."""
    if not document.page_numbers:
        return None
    for key in shown_keys(document):
        field = document.fields[key]
        if field.status == "review" and field.source_page in document.page_numbers:
            return field.source_page
    return document.page_numbers[0]


def _start_home() -> None:
    st.session_state.pop("dossier_id", None)
    st.rerun()


def _paper_manual_fields(document_type: str) -> list[tuple[str, str]]:
    fields = list(PAPER_MANUAL)
    if document_type == "broker_invoice":
        # Each service line gets its own tax code and reason code instead.
        fields = [(key, label) for key, label in fields if key not in ("tax_code", "reason_code")]
    if document_type in ("customs_declaration", "customs_liquidation"):
        fields = fields + [("sap_reference", "SAP reference")]
    return fields


if "show_passed" not in st.session_state:
    st.session_state["show_passed"] = False

pending = st.session_state.get("pending")
if pending:
    st.header("Reading the PDF")
    st.write(f"{pending['name']} is being read now.")
    st.write("Please wait. This takes about a minute. Do not close this page.")
    with st.status("Sending the PDF to be read…", expanded=True) as status:
        try:
            dossier = process_upload(pending["data"], pending["name"], use_cache=False)
        except PdfRejected as exc:
            st.session_state.pop("pending", None)
            st.error(exc.message)
            if st.button("Back"):
                _start_home()
            st.stop()
        except RuntimeError as exc:
            st.session_state.pop("pending", None)
            st.error(str(exc))
            if st.button("Back"):
                _start_home()
            st.stop()
        status.update(label="Reading finished", state="complete")
    st.session_state.pop("pending", None)
    st.session_state["dossier_id"] = dossier.id
    st.rerun()

dossier_id = st.session_state.get("dossier_id")
if not dossier_id:
    st.header("Would you like to read a new import file?")
    st.write("Choose a PDF, then click Read. Nothing from an earlier file is shown here.")
    uploaded = st.file_uploader("Import PDF", type=["pdf"])
    if st.button("Read this PDF", type="primary"):
        if uploaded is None:
            st.warning("Choose a PDF first.")
        else:
            st.session_state["pending"] = {"name": uploaded.name, "data": uploaded.getvalue()}
            st.rerun()
    st.stop()

dossier = get_dossier(dossier_id)
if dossier is None or not dossier.documents:
    st.info("This file could not be opened.")
    st.stop()

failed = [item for item in dossier.validation if item.status == "failed"]
blocking = [item for item in failed if item.severity == "error"]

status_tier = "crit" if blocking else ("warn" if failed else "good")
status_text = {
    "crit": "Blocks download",
    "warn": "Needs a check",
    "good": "Ready to download",
}[status_tier]

head_left, head_right = st.columns([3, 1])
with head_left:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;">'
        f'<div class="brand-mark-inline">📄</div>'
        f'<div><strong style="font-size:20px;">Import file</strong>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-top:3px;">'
        f'<span style="font-size:13px;color:var(--ink-secondary);">{html.escape(dossier.filename)} · {len(dossier.documents)} papers read</span>'
        f'<span class="status-pill {status_tier}">{status_text}</span>'
        f"</div></div></div>",
        unsafe_allow_html=True,
    )
with head_right:
    if st.button("Read another file"):
        _start_home()

st.markdown('<div class="topbar-strip-marker"></div>', unsafe_allow_html=True)
strip_cols = st.columns([1, 1, 0.3, 4])
file_typed: dict[str, str] = {}
for index, (key, label) in enumerate(FILE_MANUAL):
    file_typed[key] = strip_cols[index].text_input(label, value=dossier.manual.get(key, ""), key=f"file-{key}")
strip_cols[2].markdown(
    '<span class="strip-info" title="Not on any page. Saved with the open paper\'s Save button below.">i</span>',
    unsafe_allow_html=True,
)

st.write("")
with st.container():
    st.caption("Export")
    if blocking and not dossier.export_with_errors:
        allow = st.checkbox("Download anyway — errors are not fixed yet", key="allow-export-with-errors")
        if allow:
            mark_export_with_errors(dossier.id, True)
            st.rerun()
    else:
        try:
            csv_path = export_dossier(dossier.id, "fields_csv")
            json_path = export_dossier(dossier.id, "json")
        except PermissionError:
            csv_path = json_path = None
        if csv_path and json_path:
            export_cols = st.columns([1, 1, 4])
            export_cols[0].download_button("Download CSV", csv_path.read_bytes(), file_name="fields.csv")
            export_cols[1].download_button(
                "Download JSON", json_path.read_bytes(), file_name="import-file.json", type="primary"
            )

if blocking:
    st.markdown(_banner("crit", f"{len(blocking)} item(s) block the download until you check them."), unsafe_allow_html=True)
elif failed:
    st.markdown(_banner("warn", f"{len(failed)} item(s) might need a second look before you download."), unsafe_allow_html=True)
else:
    st.markdown(_banner("good", "Ready to download."), unsafe_allow_html=True)
if st.button("Hide passed checks" if st.session_state["show_passed"] else "Show passed checks"):
    st.session_state["show_passed"] = not st.session_state["show_passed"]
    st.rerun()

summary = []
for kind, label, key in (
    ("supplier_invoice", "Supplier invoice", "total_amount"),
    ("customs_declaration", "Customs value", "customs_value"),
    ("customs_liquidation", "Customs payment", "total_amount"),
    ("carrier_invoice", "Shipping invoice", "total_amount"),
):
    found = next((item for item in dossier.documents if item.document_type == kind), None)
    if found is None:
        continue
    field = found.fields.get(key)
    summary.append((label, _display(found, key) or "Not read", found, field is not None and field.status == "review", kind))

if summary:
    cards = st.columns(len(summary))
    for column, (label, amount, found, needs, kind) in zip(cards, summary):
        who = issued_by(found)
        if kind == "customs_declaration":
            sub = "Copied from the customs papers"
        elif who:
            sub = f"Issued by {who}"
        else:
            sub = ""
        tag = '<span class="tag warn">Needs a check</span>' if needs else ""
        column.markdown(
            f'<div class="card">'
            f'<div class="card-label">{label}</div>'
            f'<div class="card-amount">{amount}</div>'
            f'<div class="card-sub">{sub}</div>{tag}'
            f"</div>",
            unsafe_allow_html=True,
        )

st.write("")
tabs = st.tabs([_tab_label(item) for item in dossier.documents])
for tab, document in zip(tabs, dossier.documents):
    with tab:
        st.subheader(paper_name(document.document_type))
        who = issued_by(document)
        amount = _headline_amount(document)
        st.caption(" · ".join(
            bit for bit in (
                pages_text(document.page_numbers),
                f"Issued by {who}" if who else "",
                amount,
            ) if bit
        ))

        page_state_key = f"page-{document.id}"
        current_page = st.session_state.get(page_state_key, _default_page(document))
        if current_page not in document.page_numbers:
            current_page = _default_page(document)

        preview, fields = st.columns([2, 1], gap="large")
        with preview:
            st.markdown('<div class="sticky-preview"></div>', unsafe_allow_html=True)
            if document.page_numbers:
                if len(document.page_numbers) > 1:
                    position = document.page_numbers.index(current_page)
                    nav_left, nav_label, nav_right = st.columns([1, 2, 1])
                    if nav_left.button(
                        "", icon=":material/chevron_left:", key=f"prev-{document.id}",
                        disabled=position == 0, width="stretch",
                    ):
                        st.session_state[page_state_key] = document.page_numbers[position - 1]
                        st.rerun()
                    nav_label.markdown(
                        f'<div style="text-align:center">Page {current_page} · '
                        f"{position + 1} of {len(document.page_numbers)} for this paper</div>",
                        unsafe_allow_html=True,
                    )
                    if nav_right.button(
                        "", icon=":material/chevron_right:", key=f"next-{document.id}",
                        disabled=position == len(document.page_numbers) - 1, width="stretch",
                    ):
                        st.session_state[page_state_key] = document.page_numbers[position + 1]
                        st.rerun()
                image = _cached_page_image(dossier.id, current_page)
                if image:
                    st.image(image, width="stretch")

        with fields:
            header = st.columns([1.3, 1.6, 1.5])
            header[0].caption("Field")
            header[1].caption("Value")
            header[2].caption("Printed text")

            with st.form(f"paper-{document.id}"):
                st.markdown('<div class="group-title">Copied from the page</div>', unsafe_allow_html=True)
                correction_inputs: dict[str, tuple[str, str]] = {}
                for key in shown_keys(document):
                    field = document.fields[key]
                    label, value_col, printed = st.columns([1.3, 1.6, 1.5])
                    tag = ' <span class="tag warn">Needs a check</span>' if field.status == "review" else ""
                    label.markdown(f"{field_name(document.document_type, key)}{tag}", unsafe_allow_html=True)
                    current_display = _display(document, key)
                    new_value = value_col.text_input(
                        field_name(document.document_type, key),
                        value=current_display,
                        key=f"value-{document.id}-{key}",
                        label_visibility="collapsed",
                    )
                    printed.caption(field.raw_text or "")
                    correction_inputs[key] = (current_display, new_value)

                line_typed: dict[str, str] = {}
                if document.lines:
                    st.write("")
                    st.caption("Lines copied from the page")
                    for index, line in enumerate(document.lines, start=1):
                        description = line.fields.get("description")
                        amount = line.fields.get("amount")
                        description_text = "" if description is None else str(shown_value(description) or "")
                        amount_text = "" if amount is None else str(shown_value(amount) or "")
                        line_label = f"{index}. {description_text} {amount_text}".strip()
                        if document.document_type == "broker_invoice":
                            line_left, line_tax, line_reason = st.columns([2.2, 1.15, 1.15])
                            line_left.write(line_label)
                            for lk, ll in LINE_MANUAL:
                                store_key = f"{document.id}:line:{index}:{lk}"
                                target = line_tax if lk == "tax_code" else line_reason
                                line_typed[store_key] = target.text_input(
                                    ll, value=dossier.manual.get(store_key, ""), key=f"line-{store_key}"
                                )
                        else:
                            st.write(line_label)

                st.write("")
                st.markdown('<div class="group-title">You type</div>', unsafe_allow_html=True)
                st.caption("Not on the PDF. Leave a box empty if you do not have it yet.")
                if document.document_type == "customs_liquidation":
                    st.caption("Payment number above is the liquidation number. SAP reference stays empty until you type it.")
                if document.document_type == "broker_invoice":
                    st.caption("Each service line above has its own Tax code and Reason code.")
                paper_typed: dict[str, str] = {}
                manual_cols = st.columns(2)
                for index, (key, label) in enumerate(_paper_manual_fields(document.document_type)):
                    store_key = f"{document.id}:{key}"
                    paper_typed[store_key] = manual_cols[index % 2].text_input(
                        label, value=dossier.manual.get(store_key, ""), key=f"paper-{store_key}"
                    )

                submitted = st.form_submit_button("Save", type="primary")
                if submitted:
                    set_manual(dossier.id, {**file_typed, **paper_typed, **line_typed})
                    for field_key, (before, after) in correction_inputs.items():
                        if after != before:
                            correct_field(dossier.id, document.id, field_key, after)
                    st.rerun()

        relevant = [item for item in failed if not item.fields or document.id in item.fields]
        for item in relevant:
            tier = "crit" if item.severity == "error" else "warn"
            st.markdown(_banner(tier, _check_sentence(dossier, item)), unsafe_allow_html=True)
        if st.session_state["show_passed"]:
            for item in dossier.validation:
                if item.status == "passed" and (not item.fields or document.id in item.fields):
                    st.caption(_check_sentence(dossier, item))

        position = next(index for index, item in enumerate(dossier.documents) if item.id == document.id)
        if position > 0 and st.button("Join with the paper above", key=f"join-{document.id}"):
            merge_document(dossier.id, document.id)
            st.rerun()
        if len(document.page_numbers) > 1:
            after = st.selectbox(
                "Split after",
                document.page_numbers[:-1],
                format_func=lambda page: f"Page {page}",
                key=f"split-after-{document.id}",
            )
            if st.button("Split after this page", key=f"split-{document.id}"):
                split_document(dossier.id, document.id, int(after))
                st.rerun()
