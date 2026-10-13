from dataclasses import dataclass

import streamlit as st

from app.ui import state, view
from app.ui.components import field_label, group_title, plain
from app.ui.words import LINE_MANUAL


@dataclass(frozen=True)
class FormResult:
    """What the person submitted with Save, for one paper."""

    paper_typed: dict[str, str]  # store key -> typed text, the paper's own boxes
    line_typed: dict[str, str]  # store key -> typed text, per-line tax and reason codes
    corrections: dict[str, str]  # field key -> new text, only for fields that changed


def paper_form(paper: view.PaperView, manual: dict[str, str]) -> FormResult | None:
    """The two-group form: values copied from the page, then values the person types.

    Returns a `FormResult` on the run where Save was pressed, otherwise None. It does not
    save anything; the screen decides what to do with the result.
    """
    with st.form(state.form_key(paper.id)):
        st.markdown(group_title("Copied from the page"), unsafe_allow_html=True)
        typed_values: dict[str, tuple[str, str]] = {}
        for row in paper.rows:
            label, value_col, printed = st.columns([1.3, 1.6, 1.5])
            label.markdown(field_label(row.label, row.needs_check), unsafe_allow_html=True)
            new_value = value_col.text_input(
                row.label,
                value=row.value_text,
                key=state.value_key(paper.id, row.key),
                label_visibility="collapsed",
            )
            printed.markdown(plain(row.printed_text), unsafe_allow_html=True)
            typed_values[row.key] = (row.value_text, new_value)

        line_typed: dict[str, str] = {}
        if paper.lines:
            st.write("")
            st.caption("Lines copied from the page")
            for line in paper.lines:
                if paper.line_codes:
                    line_left, line_tax, line_reason = st.columns([2.2, 1.15, 1.15])
                    line_left.markdown(plain(line.text, "body"), unsafe_allow_html=True)
                    for code_key, code_label in LINE_MANUAL:
                        store_key = view.line_store_key(paper.id, line.index, code_key)
                        target = line_tax if code_key == "tax_code" else line_reason
                        line_typed[store_key] = target.text_input(
                            code_label, value=manual.get(store_key, ""), key=state.line_key(store_key)
                        )
                else:
                    st.markdown(plain(line.text, "body"), unsafe_allow_html=True)

        st.write("")
        st.markdown(group_title("You type"), unsafe_allow_html=True)
        st.caption("Not on the PDF. Leave a box empty if you do not have it yet.")
        for note in paper.typed_notes:
            st.caption(note)
        paper_typed: dict[str, str] = {}
        columns = st.columns(2)
        for index, (key, label) in enumerate(paper.typed_fields):
            store_key = view.paper_store_key(paper.id, key)
            paper_typed[store_key] = columns[index % 2].text_input(
                label, value=manual.get(store_key, ""), key=state.paper_key(store_key)
            )

        submitted = st.form_submit_button("Save", type="primary")

    if not submitted:
        return None
    corrections = {key: after for key, (before, after) in typed_values.items() if after != before}
    return FormResult(paper_typed=paper_typed, line_typed=line_typed, corrections=corrections)
