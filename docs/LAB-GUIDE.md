# EarthWorm Lab Guide

This guide ties the lab materials together in one place.

It is meant for two kinds of readers:

1. people who want to run the lab and collect their own PCAPs
2. people who just want to inspect the included sample PCAPs

---

## What this repo contains

### Lab components

- Docker-based EarthWorm reverse SOCKS lab
- Local browser UI for controlling the lab
- Capture workflow for generating PCAPs
- Draft Suricata detections
- Draft Zeek detector

### Included supporting materials

- sample PCAPs under `sample-pcaps/`
- screenshots under `docs/screenshots/`
- collection instructions under:
  - `docs/COLLECTION-STEPS.txt`
  - `docs/MULTI-PCAP-TESTING-STEPS.txt`
- detection notes under:
  - `docs/EW-DETECTION-DRAFTS.md`

---

## Quick start

Start the lab:

```bash
docker compose up -d
```

Then open:

- <http://127.0.0.1:23456>

The UI is local only and is intended for contained lab use.

---

## Standard lab workflow

The normal control flow is:

1. Reset Lab State
2. Initialize Routing
3. Start Server
4. Connect Client
5. Start Capture
6. Test SOCKS Through Tunnel
7. Stop Capture / Save
8. Download the PCAP

Use **Reset Lab State** before each clean run.

---

## Two main collection styles

### 1. Handshake collection

Use this when you want to capture the initial setup and reverse connection behavior.

Best for:

- viewing the earliest control records
- studying setup-stage sequencing
- testing setup-stage detections

### 2. Tunnel-activity collection

Use this when you want to capture traffic after setup is already complete.

Best for:

- studying request-stage behavior
- examining SOCKS negotiation and tunneled HTTP
- testing post-setup detections

For the full operator steps, see:

- `docs/COLLECTION-STEPS.txt`

For the repeated six-PCAP test plan, see:

- `docs/MULTI-PCAP-TESTING-STEPS.txt`

---

## Included sample PCAPs

If you do not want to run the lab first, sample captures are included in:

- `sample-pcaps/`

See:

- `sample-pcaps/README.md`

Suggested first file:

- `ew-test-01-handshake-single-http.pcap`

That sample is the easiest starting point for viewing both setup-stage bytes and a simple follow-on request.

---

## Important packet patterns

The most useful observed patterns are front loaded in the setup and request stages.

### Setup-stage control records

Fresh setup captures consistently showed:

- `01 01 00 00 00 00`
- `01 02 00 00 00 00`
- often `01 03 00 00 00 00`

### Request-stage records

When a tunneled request is driven through the tunnel, captures consistently showed:

- `01 04 00 00 00 00`
- `01 05 00 00 00 00`
- then SOCKS negotiation bytes such as:
  - `05 02 00 01`
  - `05 00`
  - `05 01 00 01 ...`

These patterns are why the current draft detections are split into:

- setup-stage detection
- post-setup request-stage detection

---

## Detection materials

Draft detection materials are included here:

- Suricata rules: `detections/suricata/earthworm.rules`
- Zeek script: `detections/zeek/earthworm-detector.zeek`
- Notes and rationale: `docs/EW-DETECTION-DRAFTS.md`

These are based on current lab observations and should be treated as draft detection content for further tuning.

---

## Screenshot reference

The repo also includes screenshots used in the article and README:

- `docs/screenshots/earthworm_lab_tile.png`
- `docs/screenshots/earthworm_lab_dashboard.png`
- `docs/screenshots/earthworm_lab_downloads.png`
- `docs/screenshots/earthworm_lab_setup_sequence.png`
- `docs/screenshots/earthworm_lab_request_sequence.png`

---

## Recommended reader paths

### If you want to run the lab yourself

1. Start with the main `README.md`
2. Open this guide
3. Follow `docs/COLLECTION-STEPS.txt`
4. Review `docs/EW-DETECTION-DRAFTS.md`

### If you only want the PCAPs

1. Open `sample-pcaps/README.md`
2. Start with `ew-test-01-handshake-single-http.pcap`
3. Compare what you see against the byte patterns listed in this guide

---

## Final note

This project is meant to support practical detection engineering. The goal is not just to run EarthWorm, but to generate repeatable packet captures that are useful for Suricata, Zeek, and related network analysis work.
