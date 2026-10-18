# Contracts

The cross-repo API contracts (OpenAPI 3.1). The architect drafts them per request, and they're
filed here once approved (`scripts/adr.sh contracts <REQ>`). `index.json` names the producer and
consumers of each contract. Every party records the contract version it implements in its
`.contracts.lock`, and `scripts/contract-check.sh` enforces that.
