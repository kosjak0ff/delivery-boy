---
id: "202603251854-3YGT6P"
title: "Add tests and deployment docs"
status: "DONE"
priority: "med"
owner: "TESTER"
depends_on: ["[\"202603251854-SM51CP\"]"]
tags: []
commit: { hash: "ba0fddd430d049b9e85528bff8d5288d22ff1e8d", message: "✨ 9YCYQA NHH4FX SM51CP 3YGT6P build the Telegram channel relay MVP service" }
comments:
  - { author: "TESTER", body: "Start: add automated coverage for parser and deduplication behavior, complete the bilingual operator documentation, and document VPS plus systemd deployment and real-world verification steps." }
doc_version: 2
doc_updated_at: "2026-03-25T19:04:36+00:00"
doc_updated_by: "agentctl"
description: "Add parser and deduplication tests, finalize the bilingual README in Russian and English, and document VPS plus systemd setup and verification steps for the service."
---
## Summary

Added baseline automated tests for parser and repository behavior and completed bilingual operator documentation covering local setup, VPS deployment, systemd, and real-world verification steps.

## Scope

Covered parser and repository unit tests plus README sections for installation, configuration, local operation, VPS deployment, systemd setup, and end-to-end verification.

## Risks

Automated coverage is intentionally basic for the MVP and does not yet include mocked end-to-end Bot API or live Telegram Web integration tests.

## Verify Steps

Run pytest and review README deployment steps to ensure the documented VPS, systemd, and operator instructions match the shipped files.

## Rollback Plan

Revert the implementation commit if the docs or tests prove incorrect and remove the added local virtual environment if it is no longer needed.

## Notes

Tests were executed from a local .venv on Python 3.14 because python3.12 was not present in the current shell PATH; the project target remains Python 3.12 for deployment.

