# PR #44 — Drive folder URL ingestion (operator notes)

PR #44 adds `scripts/build_wisereport_drive_inventory.py`, a sibling to
PR #39's local-mount inventory builder. It accepts Google Drive folder
URLs (or bare folder IDs) and emits a phase3 inventory consumable by
the existing PR #29 chain runner without changing parser / bridge /
merge / build / emit / ticker map / broker autodetect logic.

## Real-smoke procedure (operator on a network-allowed host)

The two production folder URLs in scope:

```
COMPANY_URL=https://drive.google.com/drive/folders/1-GiNJ47og07Jwvj2-PbQLqs7EwpN21va
INDUSTRY_URL=https://drive.google.com/drive/folders/1Y4AhlpSSGW6GiroVMS1mSpyCCiF7JUEW
```

### 1. List both folders into a /tmp inventory (no downloads yet)

```
python3 stock_research/phase3_report_pipeline/scripts/build_wisereport_drive_inventory.py \
    --date 2026-04-30 \
    --company-drive-folder-url  "$COMPANY_URL" \
    --industry-drive-folder-url "$INDUSTRY_URL" \
    --out /tmp/pr44_real_smoke_inventory.json \
    --max-company-pdfs 50 --max-industry-pdfs 50 \
    --apply
```

Expected printed counters (verbatim summary lines):

```
[APPLY]   summary.company_pdf_count               = <int>
[APPLY]   summary.industry_pdf_count              = <int>
[APPLY]   summary.malformed_filename_count        = <int>
[APPLY]   summary.duplicate_basename_count        = <int>
[APPLY]   summary.skipped_non_pdf_count           = <int>
[APPLY]   summary.capped_company_count            = <int>
[APPLY]   summary.capped_industry_count           = <int>
[APPLY]   summary.direct_trade_signal_true_count  = 0
[APPLY]   summary.selected_alias_count            = <== company_pdf_count>
[APPLY]   summary.selected_alias_matches_company  = True
[APPLY]   summary.downloaded_pdf_count            = 0
[APPLY]   summary.failed_download_count           = 0
```

The first listing run records counts only — no PDF bytes are pulled.
Operator should note `company_pdf_count` and `industry_pdf_count` for the PR
description; do NOT paste filenames into the PR (filenames may include
ticker hints).

### 2. Sample raw download to /tmp (one company + one industry PDF)

```
python3 stock_research/phase3_report_pipeline/scripts/build_wisereport_drive_inventory.py \
    --date 2026-04-30 \
    --company-drive-folder-url  "$COMPANY_URL" \
    --industry-drive-folder-url "$INDUSTRY_URL" \
    --out /tmp/pr44_real_smoke_inventory_dl.json \
    --download-dir /tmp/pr44_real_smoke_pdfs \
    --max-download-pdfs 2 \
    --download-which company,industry \
    --apply
```

Expected: `downloaded_pdf_count = 2`, `failed_download_count = 0`,
two PDFs land at `/tmp/pr44_real_smoke_pdfs/기업/<filename>.pdf` and
`/tmp/pr44_real_smoke_pdfs/산업/<filename>.pdf`. Verify each starts
with the `%PDF` magic and lives entirely OUTSIDE the repo:

```
head -c 4 /tmp/pr44_real_smoke_pdfs/기업/*.pdf
head -c 4 /tmp/pr44_real_smoke_pdfs/산업/*.pdf
# both should print: %PDF
```

Do NOT paste the PDF body, the per-file sha256, or the per-file size
into the PR description.

### 3. Forbidden actions checklist (must all hold)

| guard                                                  | enforced by             |
|--------------------------------------------------------|-------------------------|
| no Drive write / rename / delete                       | script only issues GETs |
| no PDF / extracted text / inventory committed to repo  | --out /tmp gate (exit 2)|
| no PDF download landing inside the repo                | --download-dir /tmp gate (exit 2)|
| no OCR / Vision / API client                           | stdlib `urllib.request` only |
| `--max-*-pdfs` ≤ 50                                    | HARD_MAX (exit 2)       |
| `direct_trade_signal=true` never emitted               | hard-coded `False` per entry (exit 3 on violation) |
| no `latest/` / `promote_*` / SuperPack / rolling --apply | not invoked by this script |
| default dry-run                                        | `--apply` opt-in       |

## Sandbox-blocked variant (offline cache mode)

If the operator's host blocks outbound HTTPS to `drive.google.com`
(seen on this PR's CI sandbox: `Host not in allowlist` / HTTP 403),
pre-fetch the listing HTML on a network-allowed host and feed it in
via `--listing-cache-dir`:

```
# on a network-allowed host:
mkdir -p /tmp/pr44_listing_cache
curl -fsS "https://drive.google.com/embeddedfolderview?id=1-GiNJ47og07Jwvj2-PbQLqs7EwpN21va" \
    > /tmp/pr44_listing_cache/1-GiNJ47og07Jwvj2-PbQLqs7EwpN21va.html
curl -fsS "https://drive.google.com/embeddedfolderview?id=1Y4AhlpSSGW6GiroVMS1mSpyCCiF7JUEW" \
    > /tmp/pr44_listing_cache/1Y4AhlpSSGW6GiroVMS1mSpyCCiF7JUEW.html

# then on the offline host:
python3 stock_research/phase3_report_pipeline/scripts/build_wisereport_drive_inventory.py \
    --date 2026-04-30 \
    --company-drive-folder-url  "$COMPANY_URL" \
    --industry-drive-folder-url "$INDUSTRY_URL" \
    --listing-cache-dir /tmp/pr44_listing_cache \
    --out /tmp/pr44_real_smoke_inventory.json \
    --apply
```

A clean exit-4 with an operator-actionable hint is emitted whenever
the network fetch fails; no partial inventory file is written.

## Chain into the existing PR #29 runner

Once a `/tmp` inventory exists (with `selected[]` populated as the alias
of `selected_company[]`), feed it into the existing chain runner with
the downloaded PDFs:

```
python3 stock_research/phase3_report_pipeline/examples/run_inventory_batch_smoke.py \
    --inventory /tmp/pr44_real_smoke_inventory_dl.json \
    --pdf-dir   /tmp/pr44_real_smoke_pdfs/기업 \
    --workdir   /tmp/pr44_chain_wk \
    --max-pdfs  50 \
    --date      2026-04-30 \
    --pdf-engine pypdf
```

The PR #44 inventory's industry entries (`selected_industry[]`) are
NEVER fed to the parser — they are isolated for downstream LLM-summary
queue use only. The synthetic-fixture chain test asserts this end-to-end.
