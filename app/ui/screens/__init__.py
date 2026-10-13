"""One module per screen (docs/UI_PLAN.md section 3).

Screens are the only place in `app/ui` that calls `app.service`. They turn what the
widgets return into service calls, then rerun.
"""
