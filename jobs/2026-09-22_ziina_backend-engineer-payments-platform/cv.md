# MWAFAK NADER ALMAHAINI
**BACKEND ENGINEER · TYPESCRIPT · NESTJS · POSTGRESQL**
+971 54 483 3235 • moofk2002@gmail.com • Dubai, UAE • open to relocation
[LinkedIn](https://www.linkedin.com/in/mowafk-mha/) • [GitHub](https://github.com/SuperMo0) • [Codeforces](https://codeforces.com/profile/SuperMo) • [Portfolio](https://mwafak.dev/about)

Backend engineer who ships and owns services end to end — a production platform serving enterprise clients, multi-tenant APIs, and the CI/CD and observability around them. Currently building a delivery platform in NestJS around idempotent APIs and an explicit state machine for every shipment.

---

## EXPERIENCE

### Software Engineer | Sync NGO — Jun 2026 – Present
- Built and shipped backend services for a recruitment platform in production with enterprise clients, owning features from design through deployment and monitoring.
- Designed a modular service split into eight internal packages with enforced dependency boundaries, so the API and background worker share domain logic without sharing a deployment.
- Multi-tenant request handling with per-tenant rate limiting and validated request boundaries throughout.
- Structured logging and request correlation IDs tracing a single request across API and worker.
- 117 automated tests across unit and integration suites; CI running lint, typecheck, tests and static analysis on every change.

### Shopify Web Developer | Freelance — Mar 2026 – Jun 2026
- Shipped 3 storefronts for international clients using Liquid, JavaScript and Web Components.
- Built a webhook-driven restock notification service that recovers lost sales by alerting customers the moment stock returns.

---

## PROJECTS

### Last-Mile Delivery Platform — NestJS, Kafka, PostgreSQL/PostGIS, Redis, OpenTelemetry (in progress)
- Building a merchant delivery platform with an idempotent shipment API: merchant-scoped keys in Redis with a request-body hash, so a genuine retry replays the stored response and a changed body under the same key is rejected.
- Explicit shipment state machine from pickup through delivery, returns and cash-on-delivery, with every physical handoff recorded as an immutable custody event and expected-versus-scanned reconciliation surfacing discrepancies.

### Financial Reconciliation & Settlement Engine — Java, Spring Boot, AWS
- Reconciles internal ledgers against daily Stripe, PayPal and bank settlement reports so finance closes the books without manual matching.
- Streams multi-gigabyte settlement files straight from S3 without loading them into memory; unmatched transactions go to an SQS dead-letter queue for review.

### Order Routing & Fulfillment Service — Go, Kafka, AWS
- Order-routing microservice in Go that assigns each order to the optimal warehouse by location and stock, then dispatches to 3PL partners.
- Kafka ingestion with an outbox pattern so no order is lost or duplicated; runs on AWS ECS Fargate with RDS and CloudWatch.

### Cinema Discovery Platform — TypeScript, Express, PostgreSQL
- Scheduled scraping pipeline aggregating 200+ sources on a daily sync, with pagination and indexing keeping query paths fast as the dataset grows.
- Monorepo with a shared types package so API contract changes surface at compile time; JWT auth, schema-validated boundaries, rate limiting, CI running CodeQL and dependency review.

---

## SKILLS

- **Languages:** TypeScript, JavaScript, Python, Go, Java, C++, C#, SQL
- **Backend:** NestJS, Node.js, Express, FastAPI, Spring Boot, REST APIs, GraphQL, WebSockets
- **Databases:** PostgreSQL, PostGIS, Redis, Prisma, SQLAlchemy, pgvector, MongoDB
- **Cloud & DevOps:** AWS (ECS Fargate, RDS, S3, SQS, CloudWatch), Google Cloud (Cloud Run, Secret Manager), Terraform, Docker, CI/CD, GitHub Actions
- **Messaging & Data:** Apache Kafka, Apache Spark, Apache Airflow
- **Testing:** Vitest, pytest, Supertest, Testing Library, Playwright, Testcontainers
- **Practices:** Idempotent APIs, state machines, event-driven design, multi-tenant APIs, rate limiting, RBAC, OpenTelemetry tracing, CodeQL

---

## ACHIEVEMENTS
- ECPC 2025 Finalist — 129th / 1,734, 4th among 80+ university teams
- Nile University Competitive Programming Arena (NUCPA 2025) — 1st place
- Codeforces Specialist — 50+ contests
- Official ICPC Coach — 6 teams preparing for ICPC 2026

## CERTIFICATIONS
- DevOps with Docker — University of Helsinki (Jun 2026)
- MongoDB Associate Developer (Apr 2026)
- TypeScript — Frontend Masters (Feb 2026)
- Machine Learning Specialization — DeepLearning.AI (Jun 2025)

## EDUCATION
**BSc Computer Science** — Nile University, Egypt (Sep 2021 – Sep 2025)
**Full-Stack Development Curriculum** — The Odin Project (Jul 2025 – Mar 2026)

## LANGUAGES
Arabic (Native) • English (IELTS Band 7)
