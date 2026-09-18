# thatmgmt-docs

Public documentation site for the ThatMgmt API, built for [Mintlify](https://mintlify.com).

Everything here is generated from or checked against the real API. The API reference pages under `docs/api/` are generated from `spec/openapi.json`, which is a copy of `docs/openapi.json` from the `russfranky/thatmgmt` repo (private). The hand-written guides document only real endpoints, parameters, and behaviors from that spec. Nothing is invented.

## Connect to Mintlify (owner step)

The owner must do this click himself; it cannot be done from here:

1. Go to the [Mintlify dashboard](https://dashboard.mintlify.com) and sign in.
2. Create a new documentation site and choose **Import from GitHub**.
3. Select the `russfranky/thatmgmt-docs` repo.
4. Mintlify deploys from `main` on every push. Site config lives in `mint.json`.

## Regenerate the API reference

When the ThatMgmt spec changes:

1. Copy the fresh spec from thatmgmt main (`docs/openapi.json`) over `spec/openapi.json` in this repo.
2. Run the generator from the repo root:

```bash
python3 scripts/generate-api-reference.py spec/openapi.json --out docs/api
```

3. The script assigns every spec operation to exactly one group and fails if any route is ungrouped or the total count mismatches, so a bad generation cannot ship silently.
4. Commit and push. Mintlify redeploys automatically.

## Custom domain

The plan is to serve these docs at `docs.thatmgmt.com`. That needs a DNS record plus the custom domain setting in the Mintlify dashboard, both owner steps, not done yet.

## Repo layout

- `mint.json`: site name, nav, theme, links.
- `docs/`: hand-written MDX pages (start, guides, webhooks, AI agents, roadmap).
- `docs/api/`: generated MDX API reference. Do not edit by hand.
- `spec/openapi.json`: the real spec snapshot the reference was generated from.
- `scripts/generate-api-reference.py`: the generator with the honesty gate.
- `logo.svg`, `favicon.svg`: simple text wordmark, no brand imagery.
