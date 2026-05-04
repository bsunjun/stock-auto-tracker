# Observation Scope and Non-Goals

This document defines what a future read-only real-data observation
stage is, and — at least as importantly — what it is **not**. PR #60
records the policy. PR #60 does **not** begin observation.

## Core Statement

Observation is **observation**. It is not judgement. It is not
preparation for execution. It is not execution.

A read-only observation stage exists to verify, in a controlled and
auditable way, that:

- Source classification (Tier 1 – Tier 5 from PR #59) can be applied
  to real, externally produced material.
- The field allowlist (see `REAL_DATA_FIELD_ALLOWLIST_POLICY.md`) is
  sufficient to describe what was seen, without ever capturing values
  that fall under the prohibited categories.
- The human gate is honored before any next stage is even discussed.

## In Scope

- Manually confirming the source tier of a piece of public material
  before any further processing is considered.
- Manually confirming that a description of the material can be
  expressed using only allowlisted field names.
- Manually confirming that no prohibited field has been captured.
- Recording the result of the above checks in a private journal that
  is **not** committed to this repository.
- Verifying that the human approval gate
  (`HUMAN_APPROVAL_FOR_OBSERVATION.md`) is in force before any
  observation activity begins.

## Out of Scope (Non-Goals)

The following are **not** part of read-only observation, and must not
be performed under the cover of "observation":

- Producing a candidate recommendation.
- Producing a ranking, score, or "watchlist" of named instruments.
- Real-time monitoring of price, volume, or order book.
- Preparing an order, draft order, or order ticket of any kind.
- Executing any order on any account on any venue.
- Sending automated alerts or automated notifications.
- Connecting any broker, API, Kiwoom path, WiseReport feed, or Drive
  sync.
- Committing any real-data artifact (raw, derived, or summarized) into
  this repository.
- Deriving an execution intent from the observation output.

## Boundary Rules

- Observation is **read-only**. No write back to any external system,
  including Drive, Telegram, mail, or messaging.
- Observation is **manual**. No scheduled job, cron, or webhook
  produces observation output automatically.
- Observation is **journal-only**. Output stays in a private journal
  governed by `REAL_DATA_REDACTION_AND_STORAGE_POLICY.md`. It is not
  pushed to a remote.
- Observation does **not** authorize execution. A successful
  observation cycle does not become permission to act.

## Relation to PR #59

- PR #59 defined source tiers and the boundary.
- PR #60 defines the operating posture for any future observation
  stage.
- A separate, future PR — and explicit human approval per
  `HUMAN_APPROVAL_FOR_OBSERVATION.md` — is required to actually begin
  observation.
