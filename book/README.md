# Proof Before Trust

**Engineering Verifiable Execution for Autonomous AI Agents**  
**Author:** Bartosz Osiński (Osa)  
**Project:** Agent Proof Runtime  
**Edition:** 0.1 — July 2026

This directory contains the first complete book-length account of Agent Proof
Runtime (APR). The repository—not chat history, screenshots, or promotional
language—is the factual source for every implementation claim in the manuscript.

The book is written in English because the active Build Week product doctrine,
competition documentation, and public technical interface are English-first.

## Reading options

- [`PROOF_BEFORE_TRUST.md`](PROOF_BEFORE_TRUST.md) — assembled single-file manuscript.
- [`chapters/00-preface.md`](chapters/00-preface.md) — start with the preface and continue through the eight parts.
- [`SOURCES.md`](SOURCES.md) — repository evidence map and claim-boundary notes.

## Table of contents

The chapter order preserves the thirty-two-section structure locked in
`docs/PRODUCT_BLUEPRINT.md`.

### Preface

- Why this book exists
- How to read technical claims in it

### Part I — The Trust Gap and the Product

1. Executive Summary
2. Product Definition
3. Target Users
4. User Roles

### Part II — Goals, Boundaries, and Contracts

5. Product Goals
6. Explicit Non-Goals
7. Canonical Product Objects
8. Mission Manifest

### Part III — From Model Output to Controlled Artifacts

9. Provider Architecture
10. Structured Artifact Proposal
11. Artifact Contract
12. Acceptance Engine

### Part IV — The Integrity Core

13. Event Model
14. Proof Bundle
15. Independent Verifier
16. Mission Control

### Part V — Making Failure Visible

17. Tamper Lab
18. CLI Product Surface
19. HTTP Surface
20. Repository Architecture

### Part VI — Operating the System Honestly

21. Execution Backends
22. Deployment Blueprint
23. Testing Strategy
24. Observability and Evidence

### Part VII — Evaluation and Differentiation

25. Failure Model
26. Product Metrics
27. Build Week Judge Path
28. Product Differentiation

### Part VIII — The Path Forward

29. Roadmap
30. Product Invariants
31. Definition of Done — Build Week v0.2
32. Final Product Statement

## Build the assembled manuscript

From the repository root:

```bash
pandoc --metadata-file=book/metadata.yaml \
  book/chapters/00-title.md \
  book/chapters/00-preface.md \
  book/chapters/01-part-i.md \
  book/chapters/02-part-ii.md \
  book/chapters/03-part-iii.md \
  book/chapters/04-part-iv.md \
  book/chapters/05-part-v.md \
  book/chapters/06-part-vi.md \
  book/chapters/07-part-vii.md \
  book/chapters/08-part-viii.md \
  -t gfm -s -o book/PROOF_BEFORE_TRUST.md
```

The chapter files are canonical. The assembled file is a generated reading and
distribution artifact.
