# Fonts

IBM Plex Sans (400, 500, 600) and IBM Plex Mono (400, 500), Latin and Latin Extended, as `woff2`.

Reason they are in the repo: the screen must look the same on a machine with no internet and must not
call an outside host from a finance tool (`docs/design.md` §9, §11).

Source: the `@fontsource/ibm-plex-sans` and `@fontsource/ibm-plex-mono` packages, version 5.1.0.
License: SIL Open Font License 1.1, see `LICENSE.txt`.

Latin Extended is included because names on the papers contain letters such as ı, ş and Ş.

Streamlit serves this folder at `/app/static/fonts/` only when it is started with
`--server.enableStaticServing true` (see the README run command). Without that flag the
screen falls back to the system sans and monospace fonts.
