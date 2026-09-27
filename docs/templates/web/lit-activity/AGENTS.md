# Lit Activity Template Agent Guide

- Keep `src/activity/` independent of Lit, DOM, browser history, and transport.
- Activities may import another feature's public activity definition only.
- Register every activity centrally in `src/application/create-application.ts`.
- Keep raw fetch, EventSource, and WebSocket construction under
  `src/transport/`.
- Keep transient state in the owning activity or feature store; promote it only
  when ownership genuinely broadens.
- Select shell profiles; do not manipulate shell regions from activities.
- Put raw design values in `src/theme/primitives.css` and consume governed
  primitive or semantic tokens elsewhere.
- Run `npm run signoff` before review.
