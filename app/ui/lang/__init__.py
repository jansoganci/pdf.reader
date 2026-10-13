"""Which language the screen speaks, and the one function that looks a word up.

Every sentence the person reads lives in `en.py` and `fr.py`, under the same keys. The
screen code asks for a key (`t("start.heading")`); it never holds a sentence.

The language is a context variable, set once at the top of every Streamlit run by
`main.py` (`use(...)`). A context variable belongs to the running script thread, so two
people using the app at once cannot change each other's language. Pure code (`view.py`,
`components/`) reads it without importing Streamlit. Outside a run it is English, which is
what the unit tests expect.

What does NOT go through here: text read from a PDF (it is data, `components/text.py`),
and the exports (JSON and CSV keep their English keys; Phase 1 export is unchanged).
"""

from contextvars import ContextVar

from app.ui.lang import en, fr

CATALOGS = {"en": en.MESSAGES, "fr": fr.MESSAGES}
LANGUAGES = ("fr", "en")  # the order of the switch on the screen
DEFAULT_LANGUAGE = "fr"  # what a person sees on first load (the papers are French)
SWITCH_LABELS = {"fr": "FR", "en": "EN"}

_current: ContextVar[str] = ContextVar("ui_language", default="en")


def use(code: str) -> None:
    """Speak this language for the rest of the current run."""
    if code not in CATALOGS:
        raise ValueError(f"unknown language: {code}")
    _current.set(code)


def current() -> str:
    return _current.get()


def has(key: str) -> bool:
    return key in CATALOGS[current()]


def t(key: str, **params) -> str:
    """The sentence for `key` in the current language, with `{name}` slots filled in.

    A missing key is a bug, so it raises. Parameters are filled by `str.format`, which
    does not look inside the values: text from a PDF passed as a parameter stays text.
    """
    message = CATALOGS[current()][key]
    return message.format(**params) if params else message


def tn(key: str, count: int, **params) -> str:
    """Singular or plural: looks up `key.one` when count is 1, else `key.other`. `{n}` is the count."""
    return t(f"{key}.{'one' if count == 1 else 'other'}", n=count, **params)
