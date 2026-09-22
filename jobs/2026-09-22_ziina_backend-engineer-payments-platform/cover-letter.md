Dear Ziina team,

A payments platform lives or dies on doing the right thing exactly once, and that is the problem I am spending my evenings on. I am building a merchant delivery platform in NestJS, your stack, where shipment creation is idempotent: merchant-scoped keys in Redis with a hash of the request body, so a genuine retry replays the stored response and an altered request under the same key is rejected. Every shipment moves through an explicit state machine, and every handoff is an immutable event.

By day I build and run the backend of a recruitment platform used in production by enterprise clients at Sync NGO: multi-tenant APIs, per-tenant rate limiting, and the CI/CD and monitoring around them, with 117 automated tests gating every change. I have also built a reconciliation engine matching internal ledgers against Stripe and PayPal settlements, and Kafka services using an outbox pattern so no event is lost or duplicated.

I am based in Dubai, can start within about three weeks, and would welcome a conversation about the Payments Platform team.

Mwafak Almahaini
