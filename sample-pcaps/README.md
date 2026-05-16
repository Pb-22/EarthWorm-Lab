# Sample PCAPs

These curated captures are included for people who want to inspect EarthWorm lab traffic without building and running the lab first.

## Included files

- `earthworm_lab_20260509_160001_UTC.pcap` — earlier router capture retained for reference; this one includes the duplicate-packet artifact from router capture on `-i any`
- `ew-test-01-handshake-single-http.pcap` — fresh setup sequence plus one tunneled HTTP request
- `ew-test-02-handshake-double-http.pcap` — fresh setup sequence with two tunneled HTTP requests
- `ew-test-03-tunnel-activity-single-http.pcap` — request-stage activity captured after setup was already established
- `ew-test-04-reconnect-handshake.pcap` — short reconnect-oriented handshake capture
- `ew-test-05-handshake-delayed-http.pcap` — fresh setup sequence with delayed request activity
- `ew-test-06-tunnel-activity-multi-http.pcap` — request-stage activity with multiple tunneled HTTP requests

## Pool-number / Pygmy Goat testing

These `ew-test-07` through `ew-test-10` captures were generated on May 16, 2026 from the current EarthWorm lab container to extend the public sample set with synthetic Pygmy-Goat-style pool-number cases.

- `ew-test-07-pool-disabled-zero.pcap` — baseline zero-pool sequence: `01 03 00 00 00 00`, `01 04 00 00 00 00`, `01 05 00 00 00 00`
- `ew-test-08-pool-enabled-04d2.pcap` — pool-enabled matched sequence using pool `0x000004d2`
- `ew-test-09-pool-enabled-1337.pcap` — pool-enabled matched sequence using pool `0x00001337`
- `ew-test-10-pool-mismatch-04d2-1337.pcap` — mismatch case where setup/request use `0x000004d2` but the response echoes `0x00001337`

## Suggested starting point

If you only want to open one PCAP first, start with:

- `ew-test-01-handshake-single-http.pcap`

That is the simplest sample for viewing the setup-stage control records and a single follow-on request.
