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

**Backend**
- FastAPI service organised as a workspace of 8 internal packages with enforced dependency boundaries.
- Async SQLAlchemy 2.0 over asyncpg against PostgreSQL.
- Structured logging and request correlation IDs for tracing across API and worker.
- Per-tenant rate limiting; Pydantic v2 validation throughout.
- Transactional email delivery with templated messaging.

**AI / RAG**
- Semantic candidate search on pgvector — OpenAI embeddings, HNSW indexing, cosine ranking.
- Correct filtered vector search (naive filtered ANN silently drops qualifying matches).
- Chunk-type-aware profile chunking rather than fixed-width splitting.
- LLM extraction pipeline converting unstructured CVs into typed schemas.
- LLM scoring pipeline rating candidates against role criteria with supporting evidence.

**Cloud / DevOps**
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
**Backend:** FastAPI, Spring Boot, Spring Batch, Express, Node.js, SQLAlchemy, Hibernate/JPA, Prisma
**Data & Streaming:** Apache Kafka, Apache Spark / PySpark, Apache Airflow, Parquet, MLflow
**Cloud:** Azure, AWS (ECS Fargate, RDS, S3, SQS, EMR), Google Cloud (Cloud Run, Secret Manager, Cloud Scheduler), Terraform, Docker
**Databases:** PostgreSQL, pgvector, MongoDB
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
