# MWAFAK NADER ALMAHAINI
**SOFTWARE ENGINEER · BACKEND · CLOUD · AI**
+971 54 483 3235 • moofk2002@gmail.com • Dubai, UAE • open to relocation
[LinkedIn](https://www.linkedin.com/in/mowafk-mha/) • [GitHub](https://github.com/SuperMo0) • [Codeforces](https://codeforces.com/profile/SuperMo) • [Portfolio](https://mwafak.dev/about)

---

## EXPERIENCE

### Software Engineer | Sync NGO — Jun 2026 – Present
- Delivered an AI recruitment platform (React, Python/FastAPI, PostgreSQL) that cut candidate screening from manual CV review to minutes, adopted by enterprise clients.
- Built semantic candidate search with vector embeddings and pgvector, so recruiters match profiles by meaning rather than keywords, with AI-generated evidence behind every match.
- Automated CV parsing and candidate scoring, removing manual data entry from the recruiter workflow.
- Deployed on Google Cloud with Terraform and Cloud Run across staging and production, scaling to zero so infrastructure cost tracks real usage.
- Built the CI/CD pipeline — automated tests, security scanning, keyless deployments — plus monitoring and alerting that catches failures before users see them.

### Shopify Web Developer | Freelance — Mar 2026 – Jun 2026
- Shipped 3 Shopify storefronts for international clients using Liquid, JavaScript and Web Components.
- Built a webhook-driven restock notification service that recovers lost sales by alerting customers the moment stock returns.
- Grew organic traffic through structured data, Core Web Vitals and WCAG AA compliance, tracking indexing and query performance in Google Search Console.

---

## PROJECTS

### Last-Mile Delivery Platform — NestJS, Kafka, PostgreSQL/PostGIS, Redis, OpenTelemetry (in progress)
- Building a merchant delivery platform with an idempotent shipment API (merchant-scoped keys in Redis, request-hash checks on replay), non-sequential human-readable tracking IDs, and a shipment state machine from pickup through delivery, returns and cash-on-delivery.
- Scan-based chain of custody where every handoff is an immutable event and expected-versus-scanned reconciliation surfaces pickup and hub discrepancies; trips group pickups and deliveries by hub, zone and vehicle capacity before driver assignment.

### Order Routing & Fulfillment Service — Go, Kafka, Spark, AWS
- Order-routing microservice in Go that assigns each order to the optimal warehouse by location and stock, then dispatches to 3PL partners.
- Kafka ingestion with an outbox pattern so no order is lost or duplicated; PySpark shipping-delay analytics, on AWS ECS Fargate.

### Financial Reconciliation & Settlement Engine — Java, Spring Boot, AWS
- Spring Batch service reconciling internal ledgers against daily Stripe, PayPal and bank settlement reports.
- Streams multi-gigabyte CSVs straight from S3 without loading them into memory; unmatched transactions go to an SQS dead-letter queue.

### Clickstream & Recommendations Pipeline — Airflow, Spark, MLflow, AWS
- Airflow DAGs orchestrating a clickstream ETL pipeline feeding personalized recommendation models.
- Spark on EMR turning raw JSON events into partitioned Parquet; FastAPI serving layer with MLflow drift tracking.

### Cinema Discovery Platform — TypeScript, Express, PostgreSQL
- Scheduled scraping pipeline aggregating 200+ sources on a daily sync, with pagination and indexing keeping query paths fast as the dataset grows.
- Monorepo with a shared types package so API contract changes surface at compile time; JWT auth, schema-validated boundaries, rate limiting, CI running CodeQL and dependency review.

### Personal Blog Platform — TypeScript, Express, PostgreSQL, React
- End-to-end TypeScript with Zod-validated API boundaries, JWT authentication and role-based access control separating public readers from the admin dashboard.
- Hardened with per-route rate limiting, security headers and DOMPurify sanitization on user-generated HTML; CI running tests and CodeQL static analysis.

### Real-Time Chat Application — TypeScript, Socket.IO, React, PostgreSQL
- WebSocket backend handling live presence, read receipts and group channels, with virtualized message lists holding render cost flat as history grows.
- Cookie-based JWT sessions, per-route rate limiting, and a component test suite with coverage reporting.

### AI Research Agent — LangGraph, Python
- Agent that routes queries, runs parallel web searches and grades the quality of its own output before returning results.

### Quantum Malware Detection — Qiskit, PennyLane
- Benchmarked classical against quantum ML pipelines for malware classification: SVM, Random Forest and XGBoost versus QSVM and Variational Quantum Classifiers.

---

## SKILLS

- **Languages:** Python, TypeScript, Go, Java, JavaScript, C++, C#, SQL
- **Backend:** NestJS, FastAPI, Spring Boot, Express, Node.js, REST APIs, SQLAlchemy, Hibernate/JPA, Prisma
- **Data & Streaming:** Apache Kafka, Apache Spark / PySpark, Apache Airflow, Parquet, MLflow
- **Cloud & DevOps:** AWS (ECS Fargate, RDS, S3, SQS, EMR, CloudWatch), Google Cloud (Cloud Run, Secret Manager), Azure, Terraform, Docker, CI/CD, GitHub Actions
- **Databases:** PostgreSQL, PostGIS, pgvector, Redis, MongoDB
- **AI & ML:** RAG, vector search, embeddings, LangGraph, PyTorch, TensorFlow, XGBoost, Pandas, NumPy
- **Frontend:** React, Next.js, TanStack Query, Tailwind
- **Web & SEO:** SEO, Google Search Console, structured data, Core Web Vitals, WCAG AA
- **Testing:** pytest, Vitest, Playwright, Testing Library, Supertest

---

## ACHIEVEMENTS
- ECPC 2025 Finalist — 129th / 1,734, 4th among 80+ university teams
- Nile University Competitive Programming Arena (NUCPA 2025) — 1st place
- Codeforces Specialist — 50+ contests
- Official ICPC Coach — 6 teams preparing for ICPC 2026

## CERTIFICATIONS
- MongoDB Associate Developer (Apr 2026)
- DevOps with Docker — University of Helsinki (Jun 2026)
- Machine Learning Specialization — DeepLearning.AI (Jun 2025)
- TypeScript — Frontend Masters (Feb 2026)

## EDUCATION
**BSc Computer Science** — Nile University, Egypt (Sep 2021 – Sep 2025)
**Full-Stack Development Curriculum** — The Odin Project (Jul 2025 – Mar 2026)

## LANGUAGES
Arabic (Native) • English (IELTS Band 7)
