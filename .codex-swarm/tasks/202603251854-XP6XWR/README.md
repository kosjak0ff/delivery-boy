---
id: "202603251854-XP6XWR"
title: "Build Telegram channel relay MVP"
status: "DONE"
priority: "med"
owner: "ORCHESTRATOR"
depends_on: []
tags: []
commit: { hash: "ba0fddd430d049b9e85528bff8d5288d22ff1e8d", message: "✨ 9YCYQA NHH4FX SM51CP 3YGT6P build the Telegram channel relay MVP service" }
comments:
  - { author: "ORCHESTRATOR", body: "Start: create the project tracking task, decompose the approved implementation plan into execution steps, and record the initial scope, risks, verification, and rollback notes before coding begins." }
doc_version: 2
doc_updated_at: "2026-03-25T18:55:21+00:00"
doc_updated_by: "agentctl"
description: "Top-level project task for a headless Python service that polls public Telegram channel web pages, deduplicates posts in SQLite, and forwards new posts to an admin chat via Telegram Bot API with logging, tests, deployment files, and bilingual README."
---
## Summary

Build a headless Python MVP service that polls public Telegram channel web pages, deduplicates channel posts in SQLite, and forwards new posts to an admin chat through Telegram Bot API.

## Scope

Create project scaffold, isolated Telegram web parser module, polling and forwarding services, SQLite-based deduplication and per-channel state, tests, deployment artifacts, and bilingual documentation.

## Risks

Telegram web markup may change; network failures or rate limits may cause temporary gaps; Bot API message limits require safe trimming; deployment must remain simple for systemd on a VPS.

## Verify Steps

Run the unit test suite for parser and repository behavior, then perform a local dry run with sample configuration and verify logs plus successful message delivery in Telegram.

## Rollback Plan

Stop the systemd service, revert the implementation commit, remove the generated SQLite database and log files if needed, and restore the previous configuration files on the VPS.

## Notes

Downstream tasks: 202603251854-9YCYQA scaffold; 202603251854-NHH4FX core and storage; 202603251854-SM51CP parser and forwarding; 202603251854-3YGT6P tests and docs.

