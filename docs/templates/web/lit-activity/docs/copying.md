# Copying The Template

1. Copy with `dev-std template copy lit-activity-web <destination>`.
2. Rename the package, title, root custom element, and product-neutral sample
   features.
3. Keep the activity kernel unchanged initially; extend through public
   definitions and host adapters.
4. Replace mock clients at the composition root with real semantic clients.
5. Select or add a theme by changing token mappings rather than feature styles.
6. Remove demonstration activities only after equivalent kernel and shell tests
   remain.
7. Update asset provenance if backgrounds or fonts change.
8. Run `npm ci` and `npm run signoff`.
