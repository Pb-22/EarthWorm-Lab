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

## Suggested starting point

If you only want to open one PCAP first, start with:

- `ew-test-01-handshake-single-http.pcap`

That is the simplest sample for viewing the setup-stage control records and a single follow-on request.
