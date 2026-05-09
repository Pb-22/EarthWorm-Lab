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

- `01 01 00 00 00 00`
- `01 02 00 00 00 00`
- often `01 03 00 00 00 00`
- repeated `01 03 00 00 00 00` may continue later

### Request stage stream

Observed when a new tunneled request is created:

- `01 04 00 00 00 00`
- `01 05 00 00 00 00`
- then SOCKS negotiation bytes:
  - `05 02 00 01`
  - `05 00`
  - `05 01 00 01 ...`

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
- match `01 02 00 00 00 00`
- set `ew.setup.confirmed`
- optionally add a second companion rule to observe `01 03` and strengthen confidence without forcing it into the alert condition
- do not alert yet

### Rule 3

**Name:** `EARTHWORM Setup Stage Control Sequence`

**Action:** `alert`

**Purpose:** Alert when the setup stage has been confirmed and the same connection shows the expected continuation.

**Draft behavior:**

- require `ew.setup.confirmed`
- alert on `01 03 00 00 00 00` if present very early in the stream
- alternatively alert on `01 02` when stage1 is already set if you want a tighter 2 step setup detection

**Tradeoff:**

- alerting on `01 03` gives a more complete setup stage sequence when it exists
- but `01 03` does not appear in every short reconnect sample
- alerting on `01 02` after a prior `01 01` may be the more robust high confidence draft for first testing

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
- inspect the first small payload bearing records
- if you observe `01 01 00 00 00 00` followed by `01 02 00 00 00 00`
- optionally strengthen when `01 03 00 00 00 00` follows soon after
- raise a Notice tagged as setup stage

### Notice 2

**Name:** `EarthWorm_Post_Setup_Request_Stage_SOCKS_Sequence`

**Confidence:** Medium

**Logic:**

- observe `01 04 00 00 00 00`
- then `01 05 00 00 00 00`
- then immediate SOCKS negotiation bytes on the same request stream
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
