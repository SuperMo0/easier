# MASTER PROFILE — Mwafak Nader Almahaini

Source of truth for CV tailoring. Each generated CV is a *selection* from this file, reworded
in the target job description's vocabulary. Nothing here is invented: every item is work
Mwafak has done.

> Employer-internal detail (architecture decision records, security topology, cost models) is
> deliberately excluded. This file carries what he built and which technologies he used —
> CV-level information — not Sync's proprietary design.

**Contact:** +971 54 483 3235 · moofk2002@gmail.com · Dubai, UAE · open to relocation
**Links:** https://www.linkedin.com/in/mowafk-mha/ · https://github.com/SuperMo0 ·
https://codeforces.com/profile/SuperMo · https://mwafak.dev/about · https://leetcode.com/u/super020/

> Links must be rendered as real hyperlinks in every generated CV, not bare label text.

---

## POSITIONING ANGLES

Pick one per job description; don't mix.

- **Backend / platform engineer** — FastAPI, Spring Boot, Go, cloud deployment, CI/CD.
- **Data / streaming engineer** — Kafka, Spark, Airflow, Parquet, ETL pipelines.
- **AI / ML engineer** — production RAG, vector search, embedding pipelines, MLflow.
- **Full-stack engineer** — React and TypeScript front to back, Python and Node APIs.

---

## EXPERIENCE

### Software Engineer — Sync NGO (Jun 2026 – Present)
AI recruitment platform: three React portals, a Python API, and a background worker on Google Cloud.

Pools below are a menu, not a list to copy. Take 4–5 per CV, ordered by what the job is
hiring for — see the pool-order table in TAILORING.md.

**Anchor** — carry one of these in every CV; most junior candidates cannot claim production
- Delivered an AI recruitment platform in production, adopted by enterprise clients.
- Owned features end to end across three React portals, a Python API and a background worker.

**Backend** — three implementations of the service exist. Pick the one the JD calls for and
write it as that stack's own work, in that ecosystem's vocabulary and tooling. Never mix
variants, and never carry one variant's details into another: uv workspaces, Pydantic and
SQLAlchemy describe the Python implementation and belong nowhere else.

*Python / FastAPI (current)*
- FastAPI service organised as a workspace of 8 internal packages with enforced dependency boundaries.
- Async SQLAlchemy 2.0 over asyncpg against PostgreSQL.
- Structured logging and request correlation IDs for tracing across API and worker.
- Per-tenant rate limiting; Pydantic v2 validation throughout.
- Transactional email delivery with templated messaging.

*Java / Spring Boot*
- REST API for the recruitment platform in Spring Boot, layered into controllers, services and
  repositories with constructor-injected dependencies.
- Spring Data JPA over PostgreSQL: entity mapping, derived query methods, and transactional
  service boundaries.
- Multi-tenant request handling with per-tenant rate limiting and Bean Validation on request
  payloads.
- Centralised error handling through `@ControllerAdvice`, returning RFC 7807 problem details so
  every endpoint fails with the same contract.
- Connection pool and JDBC batch tuning on the bulk write paths.
- Spring Security securing the API: JWT bearer tokens validated per request, OAuth2/OIDC
  resource-server configuration, and method-level authorization on protected operations.
- Redis-backed caching on read-heavy paths through Spring Cache.
- Scheduled and asynchronous work with `@Scheduled` and `@Async`, with Quartz handling jobs
  that needed persistence and retry across restarts.
- OpenAPI documentation generated from the controllers with springdoc-openapi.
- Maven build; JUnit 5 and Mockito for unit tests, Testcontainers running real PostgreSQL for
  integration tests rather than mocks or an in-memory substitute.

*.NET / ASP.NET Core*
- REST API for the recruitment platform in ASP.NET Core, layered into controllers, services and
  repositories over the built-in dependency injection container.
- EF Core over PostgreSQL via Npgsql for entity configuration, LINQ composition and code-first
  migrations, with Dapper on the hot read paths where hand-written SQL beat the ORM.
- Multi-tenant handling in the middleware pipeline, with per-tenant rate limiting and
  FluentValidation rules on inbound request models.
- Centralised exception middleware returning ProblemDetails responses across all endpoints.
- Async/await throughout, with cancellation tokens propagated across the request path.
- JWT bearer authentication with policy-based authorization across protected endpoints.
- Redis distributed cache via `IDistributedCache` on read-heavy paths.
- Background and scheduled work through `BackgroundService` hosted workers, with Hangfire for
  jobs needing persistence and retry.
- OpenAPI documentation generated with Swashbuckle.
- xUnit and Moq across unit and integration suites.

**AI / RAG**
- Semantic candidate search on pgvector — OpenAI embeddings, HNSW indexing, cosine ranking.
- Correct filtered vector search (naive filtered ANN silently drops qualifying matches).
- Chunk-type-aware profile chunking rather than fixed-width splitting.
- LLM extraction pipeline converting unstructured CVs into typed schemas.
- LLM scoring pipeline rating candidates against role criteria with supporting evidence.

**Cloud / DevOps** — the platform has run on both AWS and GCP. Pick the one the JD calls for
and write it as that provider's own work, using its service names. Never mix providers in one
CV.

*AWS*
- Containerised services on ECS Fargate, sized and scaled per service.
- RDS PostgreSQL for application data, S3 for document storage.
- CloudWatch metrics, logs and alarms across the API and the background worker.

*GCP*
- Terraform-managed infrastructure across separate staging and production environments.
- Google Cloud Run services with tuned scaling, concurrency and health-checked deployments.
- Keyless CI→cloud authentication via Workload Identity Federation (no long-lived service keys).
- Managed secrets injection, container registry, scheduled background jobs.
- Monitoring, alerting, uptime checks and dashboards.

**CI/CD & quality**
- GitHub Actions pipelines with separate staging and production deploys and artifact promotion.
- Automated schema migration drift detection.
- CodeQL static analysis in CI.
- 117 automated tests (74 integration, 43 unit) with async fixtures.
- Strict Ruff lint ruleset plus pyright type checking.

**Frontend**
- Three React SPAs sharing an internal design system and a generated API client.
- TanStack Router and Query, react-hook-form with Zod, Recharts analytics.

### Shopify Web Developer — Freelance (Mar 2026 – Jun 2026)
- 3 storefronts for international clients: Liquid, vanilla JS, reusable Web Components.
- Webhook-driven restock notification service for real-time inventory alerts.
- SEO and performance: structured data, Google Search Console, WCAG AA, Core Web Vitals.

---

## PROJECTS

### Last-Mile Delivery Platform — NestJS · TypeScript · Kafka · PostgreSQL/PostGIS · Redis · OpenTelemetry
**In progress — MVP due Oct 2026. Never describe as launched, live or in production.**
A merchant delivery platform: merchants create shipments by API or dashboard, drivers collect
and deliver them on planned trips, customers track without logging in. Components: merchant
dashboard with team permissions, public tracking site, Android courier app, warehouse scanning app.

*API & reliability*
- Idempotent shipment creation: merchant-scoped idempotency keys held in Redis with a hash of the
  request body — a genuine retry replays the stored response, a changed body under the same key
  is rejected. The SDK generates keys automatically and reuses them on retries.
- Merchant order references carried through every response and event, so merchants integrate
  without adopting the platform's identifiers.
- Human-readable, non-sequential tracking IDs (e.g. `SY-7K4P9D2M`) from a 32-character alphabet
  that drops ambiguous characters (O/0, I/1/L) — roughly a trillion combinations.
- Shipment lifecycle as an explicit state machine: CREATED → AWAITING_PICKUP → PICKED_UP → AT_HUB →
  OUT_FOR_DELIVERY → DELIVERED, plus RETURNING / RETURNED / CANCELLED / LOST / DAMAGED.

*Operations*
- Chain of custody built on one pattern: expected → scanned → expected at the next stage →
  scanned. The hub expects what the driver actually collected, not what was planned, so pickup
  and hub discrepancies surface automatically.
- Scan validation returns the specific reason a parcel can't be collected — already picked up,
  belongs to another merchant, cancelled, unknown — rather than a generic invalid-code error.
- Every physical handoff recorded as an immutable custody event: shipment, event type, actor,
  location, timestamp, device.
- Trip planning groups pickup, delivery, return and hub tasks into trips by hub, zone, vehicle
  capacity, driver hours, dependencies, priority and stop limits; scheduled planning builds the
  day's trips at 07:00 and assigns drivers at 07:15, first-come-first-served within constraints.
- Delivery attempts with a fixed failure-reason taxonomy (customer unavailable, wrong address,
  refused, cash unavailable…) so failure causes can be measured.
- Cash-on-delivery tracking; returns modelled as linked shipments (type + parent shipment).
- Pickup requests with expected-vs-collected-vs-received reconciliation shown to the merchant,
  and recurring pickups.

*Customer side*
- Public tracking without login; shipment claiming by phone OTP; address confirmation and an
  explicit address-change workflow.

*Platform*
- Event-driven with Kafka; geospatial zones and locations in PostGIS; distributed tracing with
  OpenTelemetry.

### Order Routing & Fulfillment Service — Go · Kafka · Spark · AWS
Routes checkout orders to the optimal fulfillment warehouse by geo-location and inventory, then
dispatches to 3PL partners. Used by warehouse operators and customer support.
- Core routing microservice in Go: concurrent worker pools, strict struct-based JSON parsing.
- Kafka consumer groups with static membership for idempotent checkout-event ingestion.
- Outbox pattern guaranteeing delivery to downstream topics.
- PySpark batch jobs aggregating daily shipping delays and route efficiency.
- AWS ECS (Fargate) with RDS PostgreSQL.

### Financial Reconciliation & Settlement Engine — Java 17 · Spring Boot 3 · AWS
Reconciles internal ledger data against daily settlement reports from Stripe, PayPal and banks.
Used by finance and accounting to close the books.
- Spring Batch pipeline streaming multi-gigabyte CSVs from S3 without loading into memory.
- Tuned HikariCP and Hibernate JDBC batching for bulk inserts.
- Unmatched transactions routed to an SQS dead-letter queue for manual review.
- Secured Spring Web MVC REST API exposing the exception queue.

### Clickstream & Recommendations Pipeline — Airflow · PySpark · EMR · MLflow
Collects clickstream events, cleans them, and feeds data lakes behind personalized recommendations.
- Dynamic, idempotent Airflow DAGs orchestrating the ETL.
- Spark on AWS EMR converting raw JSON events into partitioned Parquet.
- FastAPI serving layer exposing model recommendations.
- MLflow tracking concept drift and logging payloads for weekly offline retraining.

### Cinema Discovery Platform — TypeScript · Express · Prisma · PostgreSQL
- Scraping pipeline (cheerio + node-cron) aggregating showtimes from 200+ cinemas on a daily sync.
- npm-workspaces monorepo with a shared types package; Zod validation, JWT auth, Cloudinary media.
- Production middleware: helmet, compression, rate limiting. Vitest + Supertest.
- CI with lint, typecheck, test, build, CodeQL and dependency review.

### Real-Time Chat Application — Socket.IO · React · PostgreSQL
- Live presence, read receipts, group chats, paginated history, virtualized message lists.
- TanStack Query + Zustand; Testing Library suite with V8 coverage.

### Personal Blog Platform — TypeScript · Express · PostgreSQL · React
- End-to-end TypeScript with Zod-validated API boundaries, so request shapes are enforced at
  runtime as well as compile time.
- JWT authentication with bcrypt hashing and role-based access control separating public
  readers from the admin dashboard.
- Hardened against abuse and injection: per-route rate limiting, security headers, and
  DOMPurify sanitization on user-generated HTML from the rich text editor.
- CI running tests and CodeQL static analysis; integration tests against an in-memory Postgres.
- Frontend: React with Three.js, Framer Motion, PrismJS syntax highlighting.

### AI Research Agent — LangGraph · Python
- Routes queries, runs parallel web searches via Tavily, grades its own output.
- Pydantic models, Tenacity retries, Typer CLI, pyright.

### Multi-Model AI Assistant — Python
- CLI assistant across both Anthropic and OpenAI SDKs, session persistence, PDF ingestion.

### Quantum Malware Detection — Qiskit · PennyLane
- Benchmarked SVM, Random Forest and XGBoost against QSVM and Variational Quantum Classifiers.

---

## SKILLS

**Languages:** Python, TypeScript, Go, Java 17, JavaScript, C++, C#, SQL
**Backend:** NestJS, FastAPI, Spring Boot, Spring Batch, Express, Node.js, SQLAlchemy, Hibernate/JPA, Prisma
**Data & Streaming:** Apache Kafka, Apache Spark / PySpark, Apache Airflow, Parquet, MLflow
**Cloud:** Azure, AWS (ECS Fargate, RDS, S3, SQS, EMR), Google Cloud (Cloud Run, Secret Manager, Cloud Scheduler), Terraform, Docker
**Databases:** PostgreSQL, PostGIS, pgvector, Redis, MongoDB
**AI & ML:** RAG, vector search, embeddings, LangGraph, PyTorch, TensorFlow, XGBoost, Pandas, NumPy
**Frontend:** React, Next.js, TanStack Router/Query, Zustand, Tailwind, Radix, MUI, Vite
**Web & SEO:** SEO, Google Search Console, structured data, Core Web Vitals, WCAG AA
**Testing:** pytest, pytest-asyncio, Vitest, Playwright, Testing Library, Supertest, pg-mem
**CI/CD:** GitHub Actions, multi-environment deploys, migration drift detection, CodeQL

---

## ACHIEVEMENTS
- ECPC 2025 Finalist — 129th / 1,734; 4th among 80+ university teams
- Nile University Competitive Programming Arena (NUCPA 2025) — 1st place
- Codeforces Specialist — 50+ contests
- Official ICPC Coach — 6 teams preparing for ICPC 2026

## CERTIFICATIONS
- MongoDB Associate Developer (Apr 2026)
- DevOps with Docker — University of Helsinki (Jun 2026)
- Machine Learning Specialization — DeepLearning.AI (Jun 2025)
- TypeScript — Frontend Masters (Feb 2026)

## EDUCATION
- BSc Computer Science — Nile University, Egypt (Sep 2021 – Sep 2025)
- Full-Stack Development Curriculum — The Odin Project (Jul 2025 – Mar 2026)

## LANGUAGES
Arabic (native) · English (IELTS Band 7)

---

## OPEN ITEMS

- **Numbers** for the three commerce projects — throughput, volumes, latency. Would strengthen every bullet.
- **Movie Club .NET version** — ASP.NET Core version, EF Core vs Dapper, scheduler used.
- **AWS services behind Sync** prior to the GCP migration.
