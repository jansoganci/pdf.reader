import streamlit as st


def export_row(
    csv: bytes | None,
    json: bytes | None,
    *,
    show_override: bool,
    overridden: bool,
    override_key: str,
) -> bool:
    """The export row: two download buttons, and the "download anyway" box beside them when errors block.

    The row has the same shape in every state (docs/design.md principle 6). When there is no file to
    give yet (`csv` or `json` is None) the buttons are drawn disabled instead of being left out.
    The box keeps its state under `override_key`; the caller sets it up with `state.init_override`
    before the first draw. Returns whether "download anyway" is ticked; when the box is not shown
    that is `overridden`.
    """
    columns = st.columns([1, 1, 4], vertical_alignment="center")
    ready = csv is not None and json is not None
    columns[0].download_button(
        "Download CSV", csv or b"", file_name="fields.csv", disabled=not ready, width="stretch"
    )
    columns[1].download_button(
        "Download JSON", json or b"", file_name="import-file.json", type="primary", disabled=not ready, width="stretch"
    )
    if show_override:
        return columns[2].checkbox("Download anyway — errors are not fixed yet", key=override_key)
    return overridden
