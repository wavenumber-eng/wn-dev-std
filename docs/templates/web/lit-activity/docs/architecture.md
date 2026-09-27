# Architecture

Dependency direction:

`activity kernel <- host adapters <- application composition -> feature factories`

`generated contracts -> transports -> feature clients -> stores -> activities -> views`

The checked-in `src/contracts/generated/project-service.ts` file is explicitly
a template fixture, not a second contract authority. Replace it with the pinned
output of a TypeSpec-owned contract package before connecting a real backend;
keep `src/contracts/index.ts` as the stable application import seam.

The activity kernel imports no Lit, DOM, browser, transport, application, or
feature module. A feature can invoke another feature by importing its public
activity definition. It cannot import that feature's implementation, store, or
view.

The composition root is the only place that imports all implementations and
registers factories. Each activity renders its feature-owned view through the
host's active-frame outlet. Shell policy remains separate from workflow
behavior.

## DOM policy

This reference uses a documented mixed policy. The application shell overrides
`createRenderRoot()` and deliberately renders to light DOM so the global theme,
host layout, and copied application styles apply predictably. Feature views are
plain Lit templates hosted in that light-DOM outlet. Reusable custom elements
may use Shadow DOM when their encapsulation and styling contract warrant it;
document that choice per component family and expose theme values through
custom properties rather than reaching through a shadow boundary.
