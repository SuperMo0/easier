# MWAFAK NADER ALMAHAINI
**BACKEND ENGINEER · TYPESCRIPT · NESTJS · POSTGRESQL · KAFKA**
+971 54 483 3235 • moofk2002@gmail.com • Dubai, UAE • open to relocation
[LinkedIn](https://www.linkedin.com/in/mowafk-mha/) • [GitHub](https://github.com/SuperMo0) • [Codeforces](https://codeforces.com/profile/SuperMo) • [Portfolio](https://mwafak.dev/about)

Backend engineer who owns services end to end: a platform in production with enterprise clients, multi-tenant APIs, and the CI/CD and monitoring around them. Currently building a delivery platform in NestJS around idempotent APIs and an explicit state machine for every shipment.

---

## EXPERIENCE

### Software Engineer | Sync NGO — Jun 2026 – Present
- Delivered an AI recruitment platform in production, adopted by enterprise clients, owning features end to end across three React portals, the API and a background worker.
- Split the service into eight internal packages with enforced dependency boundaries, so the API and background worker share domain logic without sharing a deployment.
- Multi-tenant request handling with per-tenant rate limiting and validated request boundaries throughout.
- Ran on AWS: containerised services on ECS Fargate, RDS PostgreSQL, S3 document storage, and CloudWatch metrics, logs and alarms across the API and worker.
- GitHub Actions pipelines with separate staging and production deploys and artifact promotion; 117 automated tests and CodeQL gating every change.

### Shopify Web Developer | Freelance — Mar 2026 – Jun 2026
- Shipped 3 storefronts for international clients using Liquid, JavaScript and Web Components.
- Built a webhook-driven restock notification service that alerts customers the moment stock returns.

---

## PROJECTS

### Last-Mile Delivery Platform — NestJS, TypeScript, Kafka, PostgreSQL/PostGIS, Redis, OpenTelemetry (in progress)
- Building an idempotent shipment API: merchant-scoped keys in Redis with a hash of the request body, so a genuine retry replays the stored response and a changed body under the same key is rejected.
- Every shipment moves through an explicit state machine, every physical handoff is an immutable custody event, and cash-on-delivery is tracked per shipment; events flow over Kafka.

### Financial Reconciliation & Settlement Engine — Java, Spring Boot, AWS
- Reconciles internal ledgers against daily Stripe, PayPal and bank settlement reports so finance can close the books.
- Streams multi-gigabyte settlement files from S3 without loading them into memory; unmatched transactions go to an SQS dead-letter queue for review.

### Order Routing & Fulfillment Service — Go, Kafka, AWS
- Go microservice routing each checkout order to the optimal warehouse, with Kafka consumer groups for idempotent ingestion.
- Outbox pattern guaranteeing delivery to downstream topics, so no order is lost or duplicated.

### Cinema Discovery Platform — TypeScript, Express, Prisma, PostgreSQL
- Monorepo with a shared types package so API contract changes surface at compile time; Zod validation, JWT auth, rate limiting, and CI running CodeQL and dependency review.

---

## SKILLS

- **Languages:** TypeScript, JavaScript, Python, Go, Java, SQL
- **Backend:** NestJS, Node.js, Express, FastAPI, Spring Boot, REST APIs
- **Data & messaging:** PostgreSQL, PostGIS, Redis, Apache Kafka, MongoDB, Prisma
- **Cloud & DevOps:** AWS (ECS Fargate, RDS, S3, SQS, CloudWatch), Terraform, Docker, GitHub Actions
- **Practices:** Idempotent APIs, state machines, outbox pattern, event-driven design, multi-tenant rate limiting, OpenTelemetry tracing, CodeQL
- **Testing:** Vitest, Supertest, pytest, Playwright

---

## ACHIEVEMENTS
- ECPC 2025 Finalist — 129th / 1,734, 4th among 80+ university teams
- Nile University Competitive Programming Arena (NUCPA 2025) — 1st place
- Codeforces Specialist — 50+ contests
- Official ICPC Coach — 6 teams preparing for ICPC 2026

## CERTIFICATIONS
- DevOps with Docker — University of Helsinki (Jun 2026)
- TypeScript — Frontend Masters (Feb 2026)
- MongoDB Associate Developer (Apr 2026)
- Machine Learning Specialization — DeepLearning.AI (Jun 2025)

## EDUCATION
**BSc Computer Science** — Nile University, Egypt (Sep 2021 – Sep 2025)
**Full-Stack Development Curriculum** — The Odin Project (Jul 2025 – Mar 2026)

## LANGUAGES
Arabic (Native) • English (IELTS Band 7)
