# GS HALE agent instructions

These instructions apply to the entire repository.

Before designing or implementing product UI, read in order:

1. `README.md`
2. `docs/brand-system.md`
3. `docs/design-system.md`

For Japanese regulatory pre-screening work, also read `docs/jp-yakkiho-corpus/README.md` and the relevant prompt/contracts before changing code or copy.

## Decision order

When requirements are incomplete, decide in this order:

1. Domain safety and truthfulness
2. Exact brand/product/version/scope/evidence linkage
3. Next action, owner, due date, and blocker clarity
4. Accessibility
5. Existing GS HALE tokens and patterns
6. Visual novelty

Do not infer legal approval, task completion, deadlines, reviewers, or evidence. Use an explicit unknown/pending state and expose what must be confirmed.

## UI constraints

- Use semantic tokens from `docs/design-system.md`; do not introduce arbitrary colors or spacing.
- Keep one primary action per view.
- Never style AI pre-screening as human approval or legal clearance.
- Preserve Japanese source text, unofficial translation labels, exact versions, and locator gaps.
- Status must use text plus a non-color cue.
- Do not introduce a new UI pattern only inside a feature or screen. If a new global component, pattern, or token is truly required, add its contract to `docs/design-system.md` before implementation or in the same change.
- A new pattern contract must define its problem, selection criteria, anatomy, variants, states, responsive behavior, accessibility behavior, content rules, and at least one valid and invalid example.
- If the pattern is only a one-off composition of existing components, keep it local and do not promote it to the design system.
