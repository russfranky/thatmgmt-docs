#!/usr/bin/env python3
"""Generate Mintlify MDX API reference pages from the real ThatMgmt OpenAPI spec.

Usage:
    python3 scripts/generate-api-reference.py <spec.json> [--commit <sha>] [--out docs/api]

Every route in the spec is assigned to exactly one group (longest path-prefix
match). The script prints the route count per group and FAILS if the total
does not equal the number of operations in the spec (honesty gate).

Do not edit generated files by hand; re-run this script instead.
"""
import argparse
import json
import os
import sys

# (path prefix, group slug, group title, intro)
GROUPS = [
    ("/health/", "health", "Health", "Liveness and readiness probes. No authentication required."),
    ("/v1/capabilities", "capabilities", "Capabilities", "Machine-readable capability inventory for the authenticated tenant."),
    ("/v1/domains", "domains", "Domains", "Domain discovery, quotes, registration preparation, and DNS reads."),
    ("/v1/certificates", "certificates", "Certificates", "SSL certificate inventory and lifecycle reads."),
    ("/v1/customers", "customers", "Customers", "Customer sub-account reads and dry-run plans."),
    ("/v1/portfolio", "portfolio", "Portfolio", "Reseller portfolio views across products."),
    ("/v1/orders", "orders", "Orders", "Order reads."),
    ("/v1/subscriptions", "subscriptions", "Subscriptions", "Subscription reads."),
    ("/v1/operations", "operations", "Operations", "Tracked operation reads."),
    ("/v1/offerings", "offerings", "Offerings", "Reseller offering coverage matrix."),
    ("/v1/aftermarket", "aftermarket", "Aftermarket", "Aftermarket and auction listing reads."),
    ("/v1/webhooks", "webhooks", "Webhooks", "Inbound webhook intake endpoints."),
    ("/v1/agreements", "reference-data", "Reference data", "Reference lists."),
    ("/v1/countries", "reference-data", "Reference data", "Reference lists."),
]

SPEC_COMMIT = "a646dfa45b3275ae388cf17412241bda025f81e1"  # thatmgmt main, 2026-09-18
SPEC_DATE = "2026-09-18"
BASE_URL = "https://api.thatmgmt.com"


def esc(text):
    t = (text or "").replace("|", "\\|").replace("\n", " ")
    # copy rule: no em dashes in user-facing docs; the spec itself contains one
    t = t.replace("\u2014", ",").replace("\u2013", "-")
    return t


def group_for(path):
    best = None
    for prefix, slug, title, intro in GROUPS:
        if path == prefix or path.startswith(prefix.rstrip("/") + "/") or path.startswith(prefix):
            # longest-prefix match
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, slug, title, intro)
    return best


def auth_label(op):
    sec = op.get("security")
    if sec is None:
        return "None required (public endpoint)"
    names = [list(s.keys())[0] for s in sec if s]
    if not names:
        return "None"
    if names == ["bearerAuth"]:
        return "Bearer <redacted> (JWT) required"
    return ", ".join(names)


def endpoint_mdx(method, path, op):
    lines = []
    lines.append(f"## `{method.upper()} {path}`")
    lines.append("")
    summary = op.get("summary") or ""
    if summary:
        lines.append(esc(summary))
        lines.append("")
    desc = op.get("description")
    if desc:
        lines.append(esc(desc))
        lines.append("")
    lines.append(f"**Auth:** {esc(auth_label(op))}")
    lines.append("")
    params = op.get("parameters") or []
    if params:
        lines.append("### Parameters")
        lines.append("")
        lines.append("| Name | In | Required | Description |")
        lines.append("| --- | --- | --- | --- |")
        for p in params:
            schema = p.get("schema", {})
            dtype = schema.get("type", "")
            d = p.get("description", "")
            if dtype:
                d = f"{d} ({dtype})".strip()
            lines.append(f"| `{esc(p.get('name',''))}` | {esc(p.get('in',''))} | {'yes' if p.get('required') else 'no'} | {esc(d)} |")
        lines.append("")
    rb = op.get("requestBody")
    if rb:
        lines.append("### Request body")
        lines.append("")
        lines.append(esc(rb.get("description", "See the OpenAPI spec for the request schema.")))
        lines.append("")
    responses = op.get("responses") or {}
    if responses:
        lines.append("### Responses")
        lines.append("")
        lines.append("| Code | Description |")
        lines.append("| --- | --- |")
        for code in sorted(responses, key=str):
            lines.append(f"| `{esc(str(code))}` | {esc(responses[code].get('description',''))} |")
        lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", help="Path to the real openapi.json")
    ap.add_argument("--commit", default=SPEC_COMMIT)
    ap.add_argument("--date", default=SPEC_DATE)
    ap.add_argument("--out", default="docs/api")
    args = ap.parse_args()

    with open(args.spec) as f:
        spec = json.load(f)

    grouped = {}
    ungrouped = []
    total = 0
    for path in sorted(spec.get("paths", {})):
        ops = spec["paths"][path]
        for method, op in ops.items():
            if method == "parameters":
                continue
            total += 1
            g = group_for(path)
            if g is None:
                ungrouped.append((method, path))
                continue
            if g[1] not in grouped:
                grouped[g[1]] = (g[2], g[3], [])
            grouped[g[1]][2].append((method, path, op))

    if ungrouped:
        print("UNGROUPED ROUTES (honesty gate failed):", file=sys.stderr)
        for m, p in ungrouped:
            print(f"  {m.upper()} {p}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    written = 0
    for slug in sorted(grouped):
        title, intro, endpoints = grouped[slug]
        lines = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"> Auto-generated from `spec/openapi.json` (thatmgmt main `{args.commit[:8]}`, {args.date}). Do not edit by hand. Re-run `scripts/generate-api-reference.py`.")
        lines.append("")
        lines.append(f"Base URL: `{BASE_URL}` (the spec file lists a dev default; production is `{BASE_URL}`).")
        lines.append("")
        lines.append(intro)
        lines.append("")
        lines.append("Response envelopes vary per route; the spec does not publish field-level response schemas, so shapes below describe status codes and the error model from the spec.")
        lines.append("")
        for method, path, op in endpoints:
            lines.append(endpoint_mdx(method, path, op))
        out_path = os.path.join(args.out, f"{slug}.mdx")
        with open(out_path, "w") as f:
            f.write("\n".join(lines))
        written += len(endpoints)
        print(f"{slug}: {len(endpoints)} routes -> {out_path}")

    print(f"total documented: {written} / spec operations: {total}")
    if written != total:
        print("HONESTY GATE FAILED: count mismatch", file=sys.stderr)
        sys.exit(1)
    print("honesty gate passed")


if __name__ == "__main__":
    main()
