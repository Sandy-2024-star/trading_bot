# 05 RND Structure and Workflow

## Overview
The RND (Research and Development) workspace serves as the staging area for research, experimental work, and prototyping before features are merged into the main application modules. It is designed to keep the production codebase clean while providing a sandbox for innovation.

## RND Organization

The RND directory is structured into several specialized subdirectories:

### 1. Experiments (`/RND/experiments/`)
Used for isolated prototype code that should not be imported by the main runtime until validated.
- **Purpose**: New signal ideas, alternative broker adapters, data-cleaning spikes, and performance test prototypes.
- **Guideline**: Prototypes here should be independent of the core application flow until they are ready for promotion.

### 2. Scripts (`/RND/scripts/`)
Contains helper scripts for ad hoc analysis and one-off tasks.
- **Purpose**: Data inspection, migration preparation, and reproducible experiments.
- **Guideline**: Keep scripts focused and disposable. If a script becomes part of regular operations, it should be moved to a production-ready location.

### 3. Patches (`/RND/patches/`)
Tracks draft patches, manual change notes, and promotion checklists for code transitioning to main modules.
- **Contents**:
    - Patch summaries and before/after behavior notes.
    - Integration checklists.
    - Dependency or configuration changes required for promotion.

### 4. Documentation (`/RND/docs/`)
Stores research notes, comparisons, feasibility checks, and rollout plans.
- **Naming Convention**:
    - `YYYY-MM-DD-topic.md`
    - `proposal-<feature>.md`
    - `promotion-<feature>.md`

## Workflow and Promotion Process

The suggested workflow for moving an idea from conception to production is:

1. **Exploration**: Explore the idea in `experiments/` or `scripts/`.
2. **Documentation**: Capture findings, tradeoffs, and design decisions in `docs/`.
3. **Drafting**: Record the final code movement and necessary changes in `patches/`.
4. **Promotion**: Move the stable implementation into the appropriate runtime modules (e.g., `data/`, `signals/`, `strategy/`, `risk/`, `execution/`, `monitoring/`, or `main.py`).

### Rules of Thumb
- **Keep Production Clean**: Keep production-ready code out of `RND/`.
- **Sandbox Isolation**: Keep temporary investigation artifacts inside `RND/`.
- **Audit Trail**: When an experiment is validated and promoted, leave a short note in the RND area describing what was moved.

## Current Focus
The current active research track is focused on chart access and trade lifecycle flow (reference: `docs/2026-04-01-chart-entry-exit-plan.md`).
