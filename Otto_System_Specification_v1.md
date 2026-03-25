# OTTO — Consumer Digital Health Twin Platform

## System Specification v1.0

**Prepared for Claude Code Implementation**
**25 March 2026 — CONFIDENTIAL**
**Sean Lunn / More Good Days × Roger Grobler / Chronos Capital**

---

## 1. Executive Summary

Otto is a subscription-based consumer health platform that gives each user a single, unified view of their health and helps them improve their healthspan. It productises the Digital Health Twin methodology developed by Roger Grobler over the past year — which combines blood work, genetics, imaging, wearable data, nutrition tracking, goal-setting, and AI-driven analysis — and makes it accessible to non-technical consumers through a compelling, mobile-first interface.

The platform is a collaboration between More Good Days (Sean Lunn and Faf du Plessis, who are building a health media platform and podcast series focused on biohacking and longevity) and Chronos Capital (Roger Grobler, who has built the underlying Digital Health Twin architecture in Notion). The commercial model attaches businesses to the media audience — including genetics companies, nutrition brands, peptide suppliers, and health equipment providers.

**Core Value Proposition:**

- One place for everything: blood results, genetics, imaging, wearables, nutrition, training — all in a single secure profile
- AI-powered coaching: Otto works with the user to set goals, tracks progress, nudges them, and gives personalised feedback
- Healthspan focus: grounded in the Four Horsemen framework (cardiovascular, metabolic, neurodegenerative, cancer) for longevity
- Human-in-the-loop: doctors, biokineticists, or health coaches can collaborate on goals and targets within the platform

---

## 2. Product Vision and Goals

### 2.1 Mission

Extend healthspan for every subscriber by providing a personal, AI-driven health operating system that consolidates all health data into a single view and delivers actionable, evidence-based guidance.

### 2.2 Target User

Health-curious adults aged 30–65 who are interested in improving their longevity but are not technologically sophisticated. They are motivated by the More Good Days media content and podcast, and want to go beyond passive consumption into active, data-driven health management. They are willing to pay a monthly subscription for a guided experience.

### 2.3 Business Model

- Monthly/annual subscription for platform access
- Premium tier: includes human health coach or doctor consultations
- Affiliate/partner revenue from integrated health product recommendations (genetics testing kits, supplements, wearables, peptides, equipment)
- Data insights (anonymised, aggregated) for partner health businesses

### 2.4 Design Principles

1. **Mobile-first:** must work beautifully on a phone browser; native app later
2. **Radically simple:** no health jargon without explanation; no complex configuration
3. **AI-native:** the primary interaction model is conversational (chat with Otto)
4. **Secure by default:** health data encrypted at rest and in transit; POPIA/GDPR compliant
5. **Progressively rich:** start simple (just blood work), unlock modules as user adds data

---

## 3. System Architecture

### 3.1 High-Level Architecture

Otto is a three-tier web application with an AI orchestration layer:

| Tier | Technology | Purpose |
|------|-----------|---------|
| Frontend | React (Next.js) + Tailwind CSS | Mobile-responsive web app; chat UI, dashboards, onboarding flows |
| Backend API | Node.js (Express or Next.js API routes) | Authentication, data ingestion, API gateway, business logic |
| AI Layer | Anthropic Claude API (Sonnet 4) | Conversational coaching, data interpretation, nudge generation, meal photo analysis |
| Database | PostgreSQL + pgvector | User profiles, health data, embeddings for semantic search across user records |
| Object Storage | S3-compatible (e.g. Cloudflare R2) | Lab report PDFs, imaging files, meal photos |
| Auth | Clerk or Auth.js | User authentication, subscription management |
| Wearable Sync | OAuth integrations | Whoop, Oura, Garmin, Apple Health data pipelines |

### 3.2 Data Model Overview

Each user has a personal health repository comprising the following data domains. These mirror the proven Notion database architecture from the existing Digital Health Twin:

| Domain | Data Types | Source |
|--------|-----------|--------|
| Personal Profile | Demographics, goals, health history, family history | Onboarding wizard + user input |
| Labs & Biomarkers | Blood panels, metabolic markers, inflammatory markers, hormone levels | PDF upload + OCR / manual entry / lab API |
| Genetic Profile | SNP data, risk alleles, pharmacogenomics, polygenic risk scores | 23andMe/Ancestry CSV upload or genetics partner API |
| Imaging | CT, MRI, DEXA, ECG, ultrasound findings; CAC score | PDF/image upload + clinician entry |
| Wearables | Sleep, HRV, recovery, strain, RHR, steps, skin temp | Whoop / Oura / Garmin / Apple Health API sync |
| Training Log | Session type, duration, zone minutes, HR data, RPE | Wearable auto-import + manual entry |
| Nutrition Log | Meals, calories, protein, fibre, omega-3, macro breakdown | Photo-based AI analysis + manual entry |
| Supplements | Active stack, dosing, timing, rationale, compliance | User input + health coach |
| Body Composition | Weight, body fat %, visceral fat, waist circumference | Smart scale sync + manual entry |
| Doctor Visits | Visit date, clinician, findings, follow-ups | User entry |
| Risk Register | Four Horsemen domain scores (ASCVD, metabolic, neuro, cancer) | AI-calculated from all other domains |
| Goals & Targets | Measurable targets with deadlines, linked to domains | Collaborative (user + health coach + AI suggestions) |

---

## 4. User Experience and Interface

### 4.1 Primary Interaction: Chat with Otto

The core user experience is a conversational AI interface. Otto is the user's health companion — always available, always personalised, and always grounded in the user's actual data. The chat interface is the default landing experience after onboarding.

**Chat Capabilities:**

- Answer questions about the user's health data: "What was my last ApoB result?"
- Explain results in plain language: "What does my HbA1c of 5.4 mean?"
- Set and review goals: "Help me set a protein target"
- Log meals via photo: user sends a photo, Otto estimates nutrition and logs it
- Review progress: "How am I tracking on fibre this week?"
- Provide nudges and encouragement: proactive messages based on data patterns
- Surface connections: "Your sleep has been worse on days you skip Zone 2 training"
- Flag risks: "Your homocysteine hasn't been tested in 8 months — worth scheduling"

### 4.2 Dashboard View

A browser-based dashboard complements the chat interface for users who prefer a visual overview. The dashboard is designed for mobile phones first.

**Dashboard Panels:**

- **Health Score:** a single composite score (0–100) summarising overall healthspan status
- **Today's Nutrition:** running totals for protein, fibre, calories against daily targets
- **Training This Week:** sessions logged, Zone 2 hours vs target, next planned session
- **Latest Biomarkers:** flagged results from most recent blood work, with trend arrows
- **Sleep & Recovery:** last night's sleep score, HRV, recovery percentage from wearable
- **Upcoming Actions:** scheduled blood tests, doctor visits, goals due
- **Supplement Compliance:** today's checklist of supplements taken/remaining

### 4.3 Onboarding Flow

The onboarding process must be welcoming and progressive. Users should feel value within 5 minutes, with deeper data loading over subsequent days/weeks.

1. **Account creation:** email/Google sign-up, subscription payment
2. **Basic profile:** name, date of birth, sex, height, weight, health goals (select from list)
3. **Quick win — first data upload:** guided upload of most recent blood test results (PDF). Otto OCRs the document, extracts key markers, and gives immediate feedback
4. **Wearable connection:** prompt to connect Whoop, Oura, Garmin, or Apple Health
5. **Genetics (optional):** upload 23andMe/Ancestry raw data file or order a kit through partner
6. **Goal setting:** Otto suggests initial goals based on available data; user confirms or adjusts
7. **Meet your coach (premium):** introduction to assigned health professional

### 4.4 Nudge System

Otto proactively reaches out to the user via push notifications and in-app messages. Nudges are data-driven and personalised, not generic.

| Nudge Type | Trigger | Example |
|-----------|---------|---------|
| Daily check-in | Morning (configurable time) | "Good morning! You slept 7.2 hours with 89% recovery. Great day for Zone 2 training." |
| Meal logging reminder | No meal logged by 13:00 | "Don't forget to snap your lunch — you're at 62g protein so far today." |
| Training prompt | No session logged for 2 days | "You've had 2 rest days. Feeling ready for a session today?" |
| Biomarker due | Time since last blood test > threshold | "It's been 4 months since your last blood panel. Time to schedule?" |
| Goal milestone | Target reached | "You hit 30g fibre yesterday for the first time this month! Keep it up." |
| Weekly summary | Sunday evening | "Weekly report: 3.2 hrs Zone 2 (target 4), protein avg 148g (target 165). Tap to review." |
| Risk flag | AI detects concerning pattern | "Your resting heart rate has been trending up for 10 days. Worth checking in with your coach." |

---

## 5. Core Feature Specification

### 5.1 Health Data Repository

**Lab Results Ingestion**

- User uploads a PDF of blood test results (e.g. PathCare, Lancet, Ampath)
- System OCRs the PDF, extracts marker names, values, units, and reference ranges
- AI maps extracted markers to the standardised biomarker schema
- User confirms/corrects any misreads before saving
- Historical results are stored with dates, enabling longitudinal trend analysis
- Each marker is flagged against clinically optimal ranges (not just lab reference ranges)

**Genetic Data Processing**

- User uploads 23andMe or Ancestry raw data CSV
- System parses key SNPs against a curated variant database
- Produces a personalised genetic risk report: cardiovascular, metabolic, pharmacogenomic, neurological, longevity categories
- Links genetic findings to actionable recommendations (e.g. MTHFR TT → methylfolate supplementation)

**Wearable Data Sync**

- OAuth-based integration with Whoop, Oura Ring, Garmin Connect, Apple Health
- Daily sync of: sleep duration, sleep efficiency, HRV, resting heart rate, recovery score, strain/activity, steps, skin temperature
- Data normalised into a common schema regardless of source device
- Historical backfill on first connection

### 5.2 AI Nutrition Tracking

Users photograph their meals. Otto's AI analyses the image and estimates nutritional content. This is the primary daily interaction point and must be fast and accurate.

**Process Flow:**

1. User takes a photo of their meal and sends it to Otto via chat
2. AI vision model identifies food items, estimates portion sizes
3. System calculates: calories, protein (g), fat (g), net carbs (g), fibre (g), omega-3 (estimated)
4. Otto presents the estimate and asks for confirmation or corrections
5. On confirmation, the meal is logged with running daily totals updated
6. User can see daily progress bars: protein vs target, fibre vs target, calories vs target

**Key Nutrition Targets (Defaults, Personalised by Health Coach):**

| Metric | Default Target | Rationale |
|--------|---------------|-----------|
| Protein | 1.6–2.0 g/kg body weight per day | Muscle protein synthesis, sarcopenia prevention |
| Fibre | 30g minimum per day | Gut microbiome health, LPS biosynthesis reduction |
| Calories | Personalised (TDEE-based) | Weight management aligned to body composition goals |
| Omega-3 (EPA+DHA) | 2g per day | Anti-inflammatory, cardiovascular, neurological |
| Alcohol | < 4 drinks per week | Liver health, sleep quality, cancer risk |

### 5.3 Goals, Targets, and Tracking

Goals are set collaboratively between the user, their health coach (if premium), and Otto's AI. They are structured, measurable, and linked to specific health domains.

**Goal Structure:**

| Field | Description | Example |
|-------|-----------|---------|
| Goal | What the user wants to achieve | Reduce body fat to < 22% |
| Domain | Which health domain it belongs to | Metabolic Health |
| Target Metric | The measurable KPI | Body fat percentage |
| Current Value | Where they are now | 25.9% |
| Target Value | Where they want to be | < 22% |
| Deadline | By when | July 2026 |
| Interventions | What actions support this goal | Zone 2 training 4 hrs/week, protein 165g/day |
| Status | Progress tracking | In Progress (24.1% as of last DEXA) |

### 5.4 Human-in-the-Loop

Otto supports a collaborative care model. Premium subscribers are assigned a health professional (doctor, biokineticist, or certified health coach) who:

- Reviews the user's data and agrees on personalised goals and targets
- Has a read-only (or limited-write) view of the user's health repository
- Receives AI-generated summaries before each scheduled check-in
- Can adjust targets, add clinical notes, and flag items for follow-up
- Communicates with the user through the Otto platform (in-app messaging)

The health professional does not replace Otto's AI; they complement it. Otto handles daily nudges, tracking, and data interpretation. The human provides clinical judgement, accountability, and the trust that comes from a real relationship.

### 5.5 Risk Assessment Engine

Otto calculates and maintains a risk profile across the Four Horsemen of chronic disease (per the Peter Attia framework):

| Domain | Key Inputs | Output |
|--------|-----------|--------|
| Cardiovascular (ASCVD) | ApoB, Lp(a), homocysteine, hsCRP, blood pressure, CAC score, genetic risk, family history, statin status | ASCVD risk score + RAG status + personalised recommendations |
| Metabolic Disease | HbA1c, fasting insulin, HOMA-IR, triglycerides, body fat %, visceral fat, waist circumference, CGM data | Metabolic risk score + insulin resistance assessment + RAG status |
| Neurodegeneration | VO₂ max, sleep quality, omega-3 status, APOE status, cognitive markers, strength training frequency | Neuro risk score + RAG status + modifiable factor analysis |
| Cancer | Screening compliance (colonoscopy, PSA, skin check, mammogram), family history, inflammation markers, genetic variants | Screening adherence score + personalised screening schedule |

Each domain receives a RAG (Red/Amber/Green) status that updates automatically as new data is ingested. The composite Health Score on the dashboard is derived from these four domain scores plus lifestyle factors (training, nutrition, sleep compliance).

---

## 6. Data Security and Privacy

Health data is among the most sensitive personal information. Otto must earn and maintain user trust through robust security.

**Requirements:**

- All data encrypted at rest (AES-256) and in transit (TLS 1.3)
- POPIA (South Africa) and GDPR (EU) compliant from day one
- User owns their data: full export and deletion capability at any time
- Row-level security in the database: each user can only access their own records
- Health professional access is explicitly granted by the user and revocable
- AI model calls use the Anthropic API with no data retention (zero data retention mode)
- Uploaded documents (PDFs, images) stored in user-specific encrypted buckets
- Audit logging for all data access and modifications
- Two-factor authentication available for all accounts

---

## 7. Technical Implementation Specification

### 7.1 Frontend

**Stack:**

- Framework: Next.js 15 (App Router)
- Styling: Tailwind CSS + shadcn/ui component library
- State: React Query (TanStack Query) for server state; Zustand for client state
- Chat: streaming responses via Server-Sent Events (SSE)
- Charts: Recharts for biomarker trends, body composition, training volume
- Camera: native browser camera API for meal photo capture
- PWA: Progressive Web App manifest for install-to-homescreen on mobile

**Key Screens:**

| Screen | Description |
|--------|-----------|
| Onboarding Wizard | Multi-step guided setup: profile, first upload, wearable connect, goals |
| Chat (Home) | Full-screen conversational interface with Otto; supports text, images, quick-reply buttons |
| Dashboard | Visual health overview with panels for nutrition, training, biomarkers, sleep, actions |
| Health Profile | Detailed view of each data domain (labs, genetics, imaging, etc.) with historical trends |
| Goals | Active goals with progress bars, linked interventions, and status |
| Settings | Account, notification preferences, connected devices, data export, health coach management |

### 7.2 Backend API

**Core API Endpoints:**

| Endpoint Group | Methods | Description |
|---------------|---------|-----------|
| `/auth` | POST, GET | Sign up, sign in, token refresh, session management |
| `/users/profile` | GET, PATCH | User demographics, goals, preferences |
| `/health/labs` | GET, POST, PATCH, DELETE | Lab results CRUD; PDF upload triggers OCR pipeline |
| `/health/genetics` | GET, POST | Genetic profile; CSV upload triggers parsing pipeline |
| `/health/wearables` | GET, POST | Wearable data; OAuth callback endpoints for each provider |
| `/health/nutrition` | GET, POST | Nutrition log; photo upload triggers AI analysis |
| `/health/training` | GET, POST, PATCH | Training log; auto-imported from wearables + manual |
| `/health/supplements` | GET, POST, PATCH | Supplement stack and daily compliance |
| `/health/imaging` | GET, POST | Imaging records and findings |
| `/health/risk` | GET | Calculated risk scores across Four Horsemen domains |
| `/health/goals` | GET, POST, PATCH, DELETE | Goals and targets CRUD |
| `/chat` | POST (SSE) | Send message to Otto AI; streams response back |
| `/coach` | GET, POST | Health coach interface: patient summaries, notes, messaging |
| `/nudges` | GET | Pending nudges for the user; POST to acknowledge |

### 7.3 AI Orchestration

Otto's AI layer is powered by the Anthropic Claude API and consists of several specialised agents:

| Agent | Model | Purpose |
|-------|-------|---------|
| Chat Agent | Claude Sonnet 4 | Primary conversational interface; has full read access to user's health repository via tool use |
| Nutrition Analyser | Claude Sonnet 4 (Vision) | Analyses meal photos, estimates macronutrients, returns structured JSON |
| Lab OCR + Interpreter | Claude Sonnet 4 (Vision) | Reads uploaded lab PDFs, extracts structured biomarker data |
| Nudge Generator | Claude Sonnet 4 | Runs daily/weekly on user data to generate personalised nudge messages |
| Risk Calculator | Claude Sonnet 4 | Evaluates all health domains and calculates composite risk scores |
| Coach Summariser | Claude Sonnet 4 | Generates pre-consultation summaries for health professionals |

**Tool Use Pattern (Chat Agent):**

The Chat Agent uses Claude's tool-use capability to query the user's database in real time. Available tools include: `query_labs`, `query_genetics`, `query_wearables`, `query_nutrition`, `query_training`, `query_goals`, `query_risk`, `log_meal`, `update_goal`, `set_reminder`. This ensures every response is grounded in the user's actual data, not generic advice.

### 7.4 Database Schema (Core Tables)

| Table | Key Columns |
|-------|-----------|
| `users` | id, email, name, dob, sex, height_cm, weight_kg, subscription_tier, coach_id, created_at |
| `lab_results` | id, user_id, marker_name, value, unit, ref_range_low, ref_range_high, optimal_low, optimal_high, flag, test_date, source_pdf_url |
| `genetic_variants` | id, user_id, gene, snp, genotype, risk_level, category, clinical_implication, action |
| `wearable_data` | id, user_id, date, source, sleep_hours, sleep_efficiency, hrv, rhr, recovery, strain, steps, skin_temp |
| `nutrition_log` | id, user_id, date, meal_type, calories, protein_g, fat_g, carbs_net_g, fibre_g, omega3_g, photo_url, notes |
| `training_log` | id, user_id, date, session_name, type, duration_min, avg_hr, zone2_min, calories, source, notes |
| `supplements` | id, user_id, name, dose, frequency, timing, rationale, target_marker, status, review_date |
| `supplement_compliance` | id, user_id, supplement_id, date, taken (bool), time_taken, notes |
| `goals` | id, user_id, domain, goal_text, target_metric, current_value, target_value, deadline, status, interventions |
| `risk_scores` | id, user_id, domain, score, rag_status, last_calculated, contributing_factors (JSON) |
| `nudges` | id, user_id, type, message, scheduled_at, sent_at, acknowledged_at |
| `coach_notes` | id, user_id, coach_id, date, note_text, goals_adjusted (JSON) |

---

## 8. Integrations

| Integration | Protocol | Data Flow | Priority |
|------------|----------|-----------|----------|
| Whoop | OAuth 2.0 + REST API | Daily sync: sleep, HRV, recovery, strain, HR zones | P0 (MVP) |
| Oura Ring | OAuth 2.0 + REST API | Daily sync: sleep, HRV, readiness, temperature | P0 (MVP) |
| Garmin Connect | OAuth 1.0a + REST API | Daily sync: steps, HR, sleep, activities, weight | P1 |
| Apple Health | HealthKit (via mobile wrapper) | Read: steps, HR, sleep, workouts, weight | P1 |
| 23andMe / Ancestry | CSV file upload | One-time: raw genotype data parsed for key SNPs | P0 (MVP) |
| PathCare / Lancet / Ampath | PDF upload + OCR | Per-event: blood test results extracted and structured | P0 (MVP) |
| Garmin Scale | Via Garmin Connect API | Auto: weight, body fat %, BMI | P1 |
| CGM (Libre / Dexcom) | API or CSV upload | Continuous: glucose readings for metabolic module | P2 |

---

## 9. MVP Scope and Phasing

### 9.1 Phase 1: Foundation (Weeks 1–4)

Build the core platform with enough functionality for internal testing with 5–10 users.

- User authentication and account creation
- Basic onboarding wizard (profile, first PDF upload)
- Lab results ingestion via PDF upload + AI OCR
- Chat interface with Otto (Claude API, tool use for querying labs)
- Nutrition logging via meal photo (AI vision analysis)
- Daily nutrition dashboard (protein, fibre, calories vs targets)
- Basic goal setting (manual)
- Mobile-responsive web app

### 9.2 Phase 2: Data Richness (Weeks 5–8)

- Wearable integration: Whoop + Oura OAuth sync
- Training log (auto-populated from wearables + manual entry)
- Sleep and recovery dashboard panel
- Genetic data upload and risk report generation
- Supplement tracking with daily compliance checklist
- Weekly summary nudge (AI-generated)
- Biomarker trend charts

### 9.3 Phase 3: Intelligence (Weeks 9–12)

- Risk Assessment Engine (Four Horsemen scoring)
- Composite Health Score calculation and dashboard
- Proactive nudge system (daily check-ins, reminders, milestone celebrations)
- Health coach portal (read-only patient view, notes, goal adjustment)
- AI-generated pre-consultation summaries for coaches
- Push notifications (via PWA or web push)

### 9.4 Phase 4: Scale (Weeks 13+)

- Additional wearable integrations (Garmin, Apple Health)
- CGM integration for metabolic module
- Partner marketplace (genetics kits, supplements, equipment)
- Subscription billing and tier management
- Anonymised cohort analytics for partner businesses
- Native mobile app (React Native or Expo)

---

## 10. Reference Architecture: Existing Digital Health Twin

Otto's data model and health logic are derived from the working Digital Health Twin built by Roger Grobler in Notion over the past year. This serves as the functional blueprint and includes:

| Component | Notion Implementation | Otto Equivalent |
|-----------|---------------------|----------------|
| Hub Page | Single page with all databases linked | User Dashboard |
| Labs Database | 13 databases with structured biomarker entries from 16+ PathCare reports | `lab_results` table + biomarker trend engine |
| Genetic Profile | 9 DNA report entries with SNP-level detail | `genetic_variants` table + risk report generator |
| Wearables | 694 Whoop days + 645 Oura days of time-series data | `wearable_data` table + OAuth sync pipelines |
| Training Log | Session-level entries with zone minutes, HR, strain | `training_log` table + wearable auto-import |
| Nutrition Log | Photo-based meal entries with macro breakdown | `nutrition_log` table + AI vision analyser |
| Supplements | 8 active entries with dosing, timing, rationale, review dates | `supplements` + `supplement_compliance` tables |
| Goals & Targets | Structured targets across Four Horsemen domains | `goals` table + `risk_scores` linkage |
| Risk Register | RAG-scored domains (ASCVD, metabolic, neuro, cancer) | `risk_scores` table + AI calculation engine |
| Imaging | 11 CT studies, CAC score tracking | imaging table + PDF/image storage |
| Body Composition | Weight and body fat tracking | `body_composition` table + smart scale sync |
| DHT Blueprint | 12-module Google Drive architecture document | Full product feature set |

**Key operational rules from the existing DHT that must carry into Otto:**

1. **Lead with the conclusion, support with data, suggest the action** — users want signal, not noise
2. **No supplement theatre** — every supplement recommendation must have evidence linked to the user's specific data
3. **Hikes do not equal Zone 2** — only count actual Zone 2 minutes with > 60% density toward cardio targets
4. **HRV and recovery data decide training load, not subjective feel**
5. **Weekend nutrition drift is intentional, not protocol failure** — don't nag about it
6. **Present data gaps as gaps, not failures** — "3/7 days logged" not "you failed to log 4 days"

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|------------|
| Daily Active Users | > 50% of subscribers | Users who open the app or chat with Otto daily |
| Meals Logged per User per Day | > 2.0 | Average nutrition log entries per active user per day |
| Wearable Sync Rate | > 90% | Percentage of users with connected wearable syncing daily |
| Lab Upload Rate | > 1 per quarter per user | Blood work uploaded within expected cadence |
| Health Score Improvement | Positive trend at 90 days | Average Health Score increase across cohort |
| Subscription Retention | > 80% at 6 months | Percentage of subscribers still active at 6 months |
| NPS | > 60 | Net Promoter Score from quarterly survey |
| AI Accuracy (Nutrition) | > 85% user acceptance | Percentage of AI meal estimates accepted without correction |

---

*End of Specification — Ready for Claude Code Implementation*
