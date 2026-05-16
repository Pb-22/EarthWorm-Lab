# Part 2: Pygmy Goat Pool-Number Follow-On

This note extends the base EarthWorm lab work with the pool-number behavior described in the UK NCSC Pygmy Goat writeup.

## Why this exists

The original lab and first public PCAP set were enough to validate the common six-byte EarthWorm control records:

- `01 01 00 00 00 00`
- `01 02 00 00 00 00`
- `01 03 00 00 00 00`
- `01 04 00 00 00 00`
- `01 05 00 00 00 00`

That is a good base for regular EarthWorm detection work.

The next logical question was how to model the pool-number behavior documented in the NCSC Pygmy Goat report, where the later records carry a reused trailing value.

## What was added

### Synthetic generator

Tool:

- `tools/generate_pool_variant_pcaps.py`

This generator produces small synthetic captures that preserve the EarthWorm-style control record shape while allowing repeatable pool-number variations.

### Public sample PCAP continuation

The sample set now continues through `ew-test-10`:

- `ew-test-07-pool-disabled-zero.pcap`
- `ew-test-08-pool-enabled-04d2.pcap`
- `ew-test-09-pool-enabled-1337.pcap`
- `ew-test-10-pool-mismatch-04d2-1337.pcap`

### UI support

The lab UI now includes pool-oriented controls for the synthetic test path:

- enable or disable pool numbering
- generate a random pool number
- show the current pool as decimal, hex, bytes, and ASCII
- emit a synthetic test PCAP from the current UI state

Important note: this does not claim that the stock EarthWorm binary itself gained native pool controls. The UI drives the synthetic test-generator path so the resulting bytes can be validated directly.

## Protocol model used

The synthetic captures model the following sequence family:

### Setup side

- client -> server: `01 01 00 00 00 00`
- server -> client: `01 02 00 00 00 00`
- server -> client: `01 03 <pool>`

### Request side

- client -> server: `01 04 <pool>`
- server -> client: `01 05 <pool>`
- server -> client: `05 02 00 01`
- client -> server: `05 00`
- server -> client: `05 01 00 01 0a 01 01 32 00 50`

That is close enough to the public Pygmy Goat description to support rule testing and PCAP review.

## Included test cases

### ew-test-07

Pool disabled / zero-tail baseline.

Expected records:

- `01 03 00 00 00 00`
- `01 04 00 00 00 00`
- `01 05 00 00 00 00`

### ew-test-08

Pool enabled with matched pool `0x000004d2`.

Expected records:

- `01 03 00 00 04 d2`
- `01 04 00 00 04 d2`
- `01 05 00 00 04 d2`

### ew-test-09

Pool enabled with matched pool `0x00001337`.

Expected records:

- `01 03 00 00 13 37`
- `01 04 00 00 13 37`
- `01 05 00 00 13 37`

### ew-test-10

Intentional mismatch case.

Expected records:

- `01 03 00 00 04 d2`
- `01 04 00 00 04 d2`
- `01 05 00 00 13 37`

This is the important negative-control sample for testing whether a detection actually enforces request/response pool equality.

## Detection implications

### What looks solid right now

The tightened vanilla EarthWorm path remains the strongest near-term ship candidate:

- exact six-byte control-record matching
- separated setup-stage and request-stage logic
- stateful correlation on the stable zero-tail control path

### What remains unresolved

The pool-aware Pygmy Goat branch is useful for testing, but the plain-rule Suricata equality attempt is not validated yet.

So the right way to describe the current state is:

- the repo now supports pool-number testing
- the public sample set includes matched and mismatched pool cases
- plain-rule equality enforcement between `01 04` and `01 05` remains an open research problem

## Recommended use

If you are reviewing this repository from a detection-engineering angle, a good sequence is:

1. start with the original EarthWorm handshake/request samples
2. confirm the setup-stage and request-stage detections behave as expected
3. open `ew-test-07` through `ew-test-10`
4. compare the trailing four bytes across `01 03`, `01 04`, and `01 05`
5. use `ew-test-10` as the negative control for any proposed pool-aware logic

## Related notes

- `sample-pcaps/README.md`
- `docs/EW-DETECTION-DRAFTS.md`
- `docs/POOL-VARIANT-TESTING-2026-05-16.md`
- `docs/reference/NCSC-EarthWORM-REFERENCE.md`
