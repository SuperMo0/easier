# MWAFAK NADER ALMAHAINI
**SOFTWARE ENGINEER · BACKEND · .NET · GO · CONTINUOUS DELIVERY**
+971 54 483 3235 • moofk2002@gmail.com • Dubai, UAE • open to relocation
[LinkedIn](https://www.linkedin.com/in/mowafk-mha/) • [GitHub](https://github.com/SuperMo0) • [Codeforces](https://codeforces.com/profile/SuperMo) • [Portfolio](https://mwafak.dev/about)

Backend engineer who owns work from discovery to production: REST APIs in ASP.NET Core over PostgreSQL, event-driven services in Go and Kafka, and continuous delivery with automated tests on every change. Currently building a last-mile delivery platform covering shipments, trips, drivers and hubs.

---

## EXPERIENCE

### Software Engineer | Sync NGO — Jun 2026 – Present
- Delivered an AI recruitment platform in production, adopted by enterprise clients, owning features end to end across three React portals, the API and a background worker.
- Built the platform's REST API in ASP.NET Core, layered into controllers, services and repositories over the built-in dependency injection container.
- EF Core over PostgreSQL with code-first migrations, Dapper on the hot read paths where hand-written SQL beat the ORM, and a Redis distributed cache on read-heavy endpoints.
- Multi-tenant middleware with per-tenant rate limiting, FluentValidation on inbound models, and ProblemDetails responses from centralised exception middleware.
- xUnit and Moq across unit and integration suites, run in GitHub Actions pipelines with separate staging and production deploys; services on AWS ECS Fargate with RDS and CloudWatch alarms.

### Shopify Web Developer | Freelance — Mar 2026 – Jun 2026
- Shipped 3 storefronts for international clients using Liquid, JavaScript and Web Components.
- Built a webhook-driven restock notification service that alerts customers the moment stock returns.

---

## PROJECTS

### Last-Mile Delivery Platform — NestJS, TypeScript, Kafka, PostgreSQL/PostGIS, Redis (in progress)
- Building a merchant delivery platform where trips group pickup, delivery, return and hub tasks by zone, vehicle capacity and driver hours, planned automatically each morning.
- Event-driven on Kafka; each shipment is an explicit state machine from pickup to delivery, and shipment creation is idempotent so a retried request never creates a second parcel.

### Order Routing & Fulfillment Service — Go, Kafka, AWS
- Go microservice with concurrent worker pools routing each checkout order to the optimal warehouse by location and stock, then dispatching to 3PL partners.
- Kafka consumer groups with static membership for idempotent ingestion, and an outbox pattern guaranteeing delivery to downstream topics.

### Financial Reconciliation & Settlement Engine — Java, Spring Boot, AWS
- Spring Batch pipeline streaming multi-gigabyte settlement files from S3 without loading them into memory; unmatched transactions go to an SQS dead-letter queue for review.

### Cinema Discovery Platform — TypeScript, Express, PostgreSQL
- Vitest and Supertest API tests in a CI pipeline running lint, typecheck, test, build and CodeQL on every change.

---

## SKILLS

- **Languages:** C#, Go, TypeScript, Python, Java, SQL
- **Backend:** ASP.NET Core, EF Core, Dapper, NestJS, Node.js, Spring Boot, FastAPI, REST APIs
- **Distributed systems:** Microservices, event-driven design, Apache Kafka, outbox pattern, idempotent APIs
- **Databases:** PostgreSQL, PostGIS, Redis, MongoDB
- **Cloud:** AWS (ECS Fargate, RDS, S3, SQS, CloudWatch), Google Cloud, Azure, Docker, Terraform
- **Testing & delivery:** xUnit, Moq, Vitest, Supertest, Playwright, GitHub Actions, CodeQL

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
