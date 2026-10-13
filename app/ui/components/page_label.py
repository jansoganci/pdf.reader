def page_label(page_number: int, position: int, total: int) -> str:
    """The text between the page buttons. Only numbers go in, and they are forced to int."""
    return (
        f'<div style="text-align:center">Page {int(page_number)} · '
        f"{int(position) + 1} of {int(total)} for this paper</div>"
    )
