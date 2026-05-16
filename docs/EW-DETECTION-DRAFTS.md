# EarthWorm Detection Drafts

## Goal

Keep the detection focused on observed communication stages instead of a fixed port.

The current lab PCAP set supports two practical draft detections:

1. High confidence setup stage control sequence detection
2. Medium confidence post setup request stage SOCKS sequence detection

These are drafts based on the current EarthWorm lab data set and should be treated as starting points for tuning.

---

## Observed byte patterns from the lab

### Setup stage control stream

Observed on the long lived control channel:

- client -> server: `01 01 00 00 00 00`
- server -> client: `01 02 00 00 00 00`
- often server -> client: `01 03 00 00 00 00`
- repeated `01 03 00 00 00 00` may continue later

### Request stage stream

Observed when a new tunneled request is created:

- client -> server: `01 04 00 00 00 00`
- server -> client: `01 05 00 00 00 00`
- then SOCKS negotiation bytes:
  - server -> client: `05 02 00 01`
  - client -> server: `05 00`
  - server -> client: `05 01 00 01 ...`

---

## Detection naming

### High confidence

**Name:** `EARTHWORM Setup Stage Control Sequence`

**Intent:** Catch the initial control setup stage on a fresh connection.

### Medium confidence

**Name:** `EARTHWORM Post Setup Request Stage SOCKS Sequence`

**Intent:** Catch request stage activity after the control channel is already established.

---

## Draft Suricata xbits plan

### Rule 1

**Name:** `EARTHWORM Setup Stage Marker 1`

**Action:** `alert` or `pass` with `noalert`

**Purpose:** Mark a flow that begins with the first observed setup stage control record.

**Observed bytes:**

- `01 01 00 00 00 00`

**Draft behavior:**

- match a 6 byte payload very early in the TCP stream
- set an xbit such as `ew.setup.stage1`
- do not alert yet

### Rule 2

**Name:** `EARTHWORM Setup Stage Confirmation`

**Action:** `alert` or `pass` with `noalert`

**Purpose:** Confirm the setup stage by requiring the next control stage record on the same flow.

**Observed bytes:**

- `01 02 00 00 00 00`
- optionally `01 03 00 00 00 00`

**Draft behavior:**

- require `ew.setup.stage1`
- match server -> client `01 02 00 00 00 00`
- alert here for the first robust high-confidence setup-stage detection
- optionally set `ew.setup.confirmed`
- optionally add a second companion noalert rule to observe `01 03` as continuation without making it mandatory

### Rule 3

**Name:** `EARTHWORM Setup Stage Control Sequence`

**Action:** `alert`

**Purpose:** Alert when the setup stage has been confirmed and the same connection shows the expected continuation.

**Draft behavior:**

- in the current rule draft, the alert fires on server -> client `01 02 00 00 00 00` after an earlier client -> server `01 01 00 00 00 00`
- `01 03 00 00 00 00` is treated as optional corroborating continuation rather than a required alert condition

**Tradeoff:**

- alerting on `01 03` gives a more complete setup stage sequence when it exists
- but `01 03` does not appear in every short reconnect sample
- alerting on `01 02` after a prior `01 01` is the more robust high-confidence draft for first testing and is what the current rule file now does

---

## Alternate 3 rule set for request stage detection

If you want the 3 rule structure to model the post setup request stage instead, use this split:

### Rule A
- mark `01 04 00 00 00 00`

### Rule B
- require Rule A and mark `01 05 00 00 00 00`

### Rule C
- require Rule B and alert on SOCKS negotiation starting with `05 02 00 01`

This should be labeled as a medium confidence request stage detection because it catches activity after the setup stage may already have been missed.

---

## Recommended first Suricata testing order

1. Build and test the setup stage draft first
2. Then build the post setup request stage draft
3. Keep the two alerts separate so the communication stage is obvious in the alert name

---

## Zeek notice draft plan

### Notice 1

**Name:** `EarthWorm_Setup_Stage_Control_Sequence`

**Confidence:** High

**Logic:**

- on a new TCP connection
- inspect both directions, not just originator payloads
- if you observe client -> server `01 01 00 00 00 00` followed by server -> client `01 02 00 00 00 00`
- optionally strengthen when server -> client `01 03 00 00 00 00` follows soon after
- raise a Notice tagged as setup stage

### Notice 2

**Name:** `EarthWorm_Post_Setup_Request_Stage_SOCKS_Sequence`

**Confidence:** Medium

**Logic:**

- observe client -> server `01 04 00 00 00 00`
- then server -> client `01 05 00 00 00 00`
- then server -> client SOCKS negotiation bytes `05 02 00 01` on the same request stream
- raise a Notice tagged as post setup request stage

---

## What not to assume yet

- Do not assume `01 03` always appears before every `01 04` and `01 05`
- Do not assume `01 04` and `01 05` will appear if no tunneled request is made
- Do not assume the destination port is stable
- Do not collapse setup stage and request stage into one alert name if you want useful triage context

---

## Practical recommendation

For first implementation, I would build:

1. `EARTHWORM Setup Stage Control Sequence`
2. `EARTHWORM Post Setup Request Stage SOCKS Sequence`

That preserves the communication stage in the detection name and gives a cleaner operational story when reviewing alerts.

---

## Pool-number / Pygmy Goat follow-on

The newer sample set extends the lab and public test material beyond the zero-tail EarthWorm records.

Relevant public samples:

- `ew-test-07-pool-disabled-zero.pcap`
- `ew-test-08-pool-enabled-04d2.pcap`
- `ew-test-09-pool-enabled-1337.pcap`
- `ew-test-10-pool-mismatch-04d2-1337.pcap`

Those captures model this sequence family:

- `01 03 <pool>`
- `01 04 <pool>`
- `01 05 <pool>`

### Current detection takeaway

The pool-aware follow-on is useful for testing and protocol grounding, but the current plain-Suricata equality attempt is not validated yet.

In practical terms:

- exact vanilla six-byte zero-tail matching is in good shape
- pool-bearing Pygmy Goat-style matching is useful as a research branch
- equality enforcement between `01 04` and `01 05` should still be treated as unresolved unless a stronger mechanism proves out

For the fuller write-up, protocol context, and reproduction guidance, see:

- `docs/PART-2-PYGMY-GOAT.md`
- `docs/POOL-VARIANT-TESTING-2026-05-16.md`
