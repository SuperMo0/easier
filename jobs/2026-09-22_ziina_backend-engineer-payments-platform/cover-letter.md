Dear Ziina team,

A payments platform has to do the right thing exactly once, and that is the problem at the centre of the delivery platform I am building in NestJS, your stack. Shipment creation is idempotent: merchant-scoped keys in Redis with a hash of the request body, so a genuine retry replays the stored response and an altered request under the same key is rejected. Every shipment moves through an explicit state machine, and every handoff is an immutable event on Kafka.

At Sync NGO I build and run the backend of a recruitment platform used in production by enterprise clients: multi-tenant APIs with per-tenant rate limiting, AWS infrastructure, and CI/CD with 117 automated tests gating every change. I have also built a reconciliation engine that matches internal ledgers against Stripe and PayPal settlements, and a Go service that uses an outbox pattern so no order is lost or duplicated.

I live in Dubai, can start about 20 days after an offer, and would welcome a conversation about the Payments Platform team.

Mwafak Almahaini
