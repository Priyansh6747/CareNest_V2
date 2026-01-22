<p align="center">
  <h1 align="center">🌸 CareNest</h1>
  <p align="center"><strong>AI-Powered Pregnancy Companion with Cognitive Memory Architecture</strong></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React_Native-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React Native"/>
  <img src="https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase"/>
  <img src="https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
</p>

---

## 🧠 The Memory Engine — Cognitive Architecture

CareNest is built around a **unified cognitive memory system** that enables context-aware, personalized health insights. The Memory Engine serves as the neural backbone, orchestrating data flow between all modules through three tightly integrated subsystems:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEMORY ENGINE                                     │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐   │
│  │  Context Pyramid  │◄─┤   SymptomMapper   │◄─┤   SRS (Smart Router)  │   │
│  │   5-Layer Stack   │  │  MedicStone Graph │  │  Vector Store Router  │   │
│  └─────────┬─────────┘  └─────────┬─────────┘  └───────────┬───────────┘   │
│            │                      │                        │               │
│            └──────────────────────┼────────────────────────┘               │
│                                   ▼                                        │
│                        ┌─────────────────────┐                             │
│                        │    ChatEngine       │                             │
│                        │  RAG Orchestrator   │                             │
│                        └─────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Context Pyramid — Hierarchical State Aggregation

The `ContextPyramid` implements a **5-layer hierarchical memory architecture** that provides LLM-ready user context with dynamic relevance scoring:

| Layer | Name | Description | Token Budget |
|-------|------|-------------|--------------|
| **L0** | User Profile | Demographics, trimester, medical flags | 100 |
| **L1** | Nutrient Trends | 7-day rolling intake + forecasts | 350 |
| **L2** | Symptom State | Recent MedicStones & active patterns | 350 |
| **L3** | Allergies & Conditions | Known intolerances, chronic conditions | 200 |
| **L4** | Conversation Memory | Last N chat exchanges (managed) | 500 |

```python
# PyramidManager dynamically scores each layer based on query relevance
pyramid = PyramidManager(user_id="uid_123")
context = await pyramid.get_context_for_query(
    query="What should I eat for more iron?",
    max_tokens=2000
)
# → Returns optimized context with L1 (Nutrients) scored highest
```

### SRS — Smart Retrieval System

The `SRS` module implements **dynamic vector store routing** for domain-specific RAG retrieval:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VectorRegistry                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ pregnancy.db │ │ nutrition.db │ │ symptoms.db  │  ...       │
│  │  (FAISS)     │ │  (FAISS)     │ │  (FAISS)     │            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
│         └────────────────┼────────────────┘                     │
│                          ▼                                      │
│                   ┌─────────────┐                               │
│                   │ SmartRouter │  Query Analysis + Scoring     │
│                   └──────┬──────┘                               │
│                          ▼                                      │
│                   ┌─────────────┐                               │
│                   │DynamicLoader│  Lazy Load + LRU Cache        │
│                   └──────┬──────┘                               │
│                          ▼                                      │
│                   ┌─────────────┐                               │
│                   │RetrievalChain│ Similarity Search + Rank     │
│                   └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

**Key SRS Components:**
- **`VectorRegistry`** — Catalogs available vector stores with metadata (domain, embedding model, chunk size)
- **`SmartRouter`** — Analyzes incoming query to route to optimal store(s) via semantic similarity
- **`DynamicLoader`** — Lazy-loads stores on demand with LRU eviction to manage memory
- **`RetrievalChain`** — Performs hybrid search and re-ranks retrieved chunks

### SymptomMapper — Temporal Health Graph

Tracks symptoms as **MedicStones** (tagged health events) connected in a temporal knowledge graph:

```python
@dataclass
class MedicStone:
    symptom: str            # "headache", "nausea"
    severity: Severity      # MILD | MODERATE | SEVERE
    context: SymptomContext # MORNING | AFTER_MEAL | EXERCISE | ...
    notes: Optional[str]
    occurred_at: datetime
    triggers: List[str]     # ["caffeine", "stress"]
    alleviators: List[str]  # ["rest", "water"]
```

**Temporal Intelligence:**
- **`TimelineMapper`** — Builds day-by-day symptom timelines with frequency analysis
- **`PatternDetector`** — Identifies recurring symptom patterns (e.g., "nausea peaks after meals on weekdays")
- **`DoctorSummaryGenerator`** — Generates structured `DoctorReport` for clinical handoff

---

## 🔄 System Interconnection Flow

All modules connect through the Memory Engine to create a **unified data nervous system**:

```
                    ┌──────────────────────┐
                    │     Mobile App       │
                    │   (React Native)     │
                    └──────────┬───────────┘
                               │ HTTP/WS
                    ┌──────────▼───────────┐
                    │     FastAPI Backend  │
                    │    /routers/*.py     │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼─────┐       ┌─────▼─────┐       ┌──────▼──────┐
    │ Nutrition │       │  Insights │       │    Chat     │
    │  Module   │       │   Engine  │       │   Engine    │
    └─────┬─────┘       └─────┬─────┘       └──────┬──────┘
          │                   │                    │
          │    ┌──────────────┴──────────────┐     │
          │    │        MEMORY ENGINE        │     │
          │    │  ┌──────────────────────┐   │     │
          └────┼──► Context Pyramid      ◄───┼─────┘
               │  ├──────────────────────┤   │
               │  │ SymptomMapper        │   │
               │  ├──────────────────────┤   │
               │  │ SRS (Vector Retrieval)│  │
               │  └──────────────────────┘   │
               └─────────────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Firebase Firestore  │
                    │  (Persistence Layer) │
                    └──────────────────────┘
```

### Data Flow Example: Chat Query

1. **User sends:** _"I've been feeling dizzy after meals, is this normal?"_
2. **ChatEngine** calls `ContextPyramid.get_context_for_query()` → relevance-scored user context
3. **ChatEngine** calls `SRS.retrieve()` → relevant pregnancy knowledge chunks
4. **ContextPyramid** internally queries `SymptomMapper` for recent dizziness events (Layer 2)
5. **ChatEngine** combines context + retrieved docs → sends to LLM (Groq/Gemini)
6. **Response** is personalized with user's trimester, nutrient status, and symptom history
7. **Message saved** to Firestore → updates Layer 4 (Conversation Memory)

---

## 📁 Project Architecture

```
Carenest_V2/
├── App/                          # React Native Mobile App
│   ├── app/                      # Expo Router screens
│   │   ├── (tabs)/               # Tab navigation
│   │   ├── meal-log.jsx          # Meal logging UI
│   │   ├── water-log.jsx         # Hydration tracking
│   │   ├── hospitals.jsx         # Nearby hospital finder
│   │   └── ...
│   ├── components/               # Reusable UI components
│   ├── hooks/                    # auth_context, useLocation
│   ├── services/apiService.js    # Backend API client
│   └── theme.js                  # Global theming
│
├── backend/                      # FastAPI Backend
│   ├── Core/                     # Business Logic Modules
│   │   ├── Memory/               # 🧠 MEMORY ENGINE
│   │   │   ├── ContextPyramid/   # Hierarchical context aggregation
│   │   │   │   ├── PyramidManager.py
│   │   │   │   └── RetrieveData.py
│   │   │   ├── SRS/              # Smart Retrieval System
│   │   │   │   ├── VectorRegistry.py
│   │   │   │   ├── SmartRouter.py
│   │   │   │   ├── DynamicLoader.py
│   │   │   │   └── RetrievalChain.py
│   │   │   └── SymptomMapper/    # Temporal symptom graph
│   │   │       ├── MedicStone.py
│   │   │       ├── TimelineMapper.py
│   │   │       ├── PatternDetector.py
│   │   │       └── DoctorSummary.py
│   │   │
│   │   ├── Chat/                 # RAG Chat Orchestrator
│   │   │   ├── ChatEngine.py     # Main orchestrator
│   │   │   └── InferenceProvider.py  # Groq/Gemini abstraction
│   │   │
│   │   ├── Insights/             # AI-Powered Analytics
│   │   │   ├── InsightEngine.py  # Chronos forecasting
│   │   │   ├── DataExtractor.py  # Historical data pipeline
│   │   │   └── FeatureBuilder.py # Feature engineering
│   │   │
│   │   ├── Nutrition/            # Food Analysis Pipeline
│   │   │   ├── AnalyseFood.py    # Gemini-powered parsing
│   │   │   ├── MacroBreakdown.py # Nutrient computation
│   │   │   ├── Storage.py        # Meal CRUD
│   │   │   └── WaterLog.py       # Hydration tracking
│   │   │
│   │   └── Parser/               # Document Processing
│   │       ├── pdf_parser.py     # Medical report OCR
│   │       └── insights_generator.py
│   │
│   ├── routers/                  # API Endpoints
│   │   ├── chat.py               # /chat/*
│   │   ├── memory.py             # /memory/*
│   │   ├── nutrition.py          # /nutrition/*
│   │   ├── symptoms.py           # /symptoms/*
│   │   └── insights.py           # /insights/*
│   │
│   └── test/                     # HTTP test files
│
└── parser/                       # Standalone parsing utilities
```

---

## 🚀 Core Modules

### Nutrition Pipeline

```python
# Full pipeline: Image/Text → Ingredients → Nutrients → Storage
from Core.Nutrition import Pipeline, AnalyseFood, Storage

# 1. Parse meal input (text or image via Gemini Vision)
ingredients = await AnalyseFood.extract_ingredients("grilled salmon with quinoa")

# 2. Compute detailed nutrient breakdown
analysis = await MacroBreakdown.analyze(ingredients, amount="300g")

# 3. Store with timestamp for trend tracking
await Storage.create_meal(user_id, name="Dinner", analysis=analysis)
```

### Insights Engine (Time-Series Forecasting)

Powered by **Amazon Chronos-Bolt** for zero-shot nutrient trend forecasting:

```python
from Core.Insights import InsightEngine

engine = InsightEngine(user_id="uid_123", use_chronos=True)
insights = await engine.generate_insights()

# Returns:
# - 7-day nutrient forecasts (protein, iron, folate, ...)
# - Gap analysis against pregnancy RDA
# - Trend direction (increasing/decreasing/stable)
# - Personalized recommendations
```

### ChatEngine (RAG Orchestrator)

Unified orchestrator combining all memory layers:

```python
from Core.Chat import ChatEngine

engine = ChatEngine(user_id="uid_123")
response = await engine.chat(
    message="What foods help with morning sickness?",
    provider="groq",  # or "gemini"
    include_sources=True
)

# response.message → Personalized answer
# response.sources → Retrieved knowledge chunks
# response.context_used → True (Memory Engine engaged)
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Mobile App** | React Native (Expo), Expo Router |
| **Backend API** | FastAPI, Pydantic, async/await |
| **Database** | Firebase Firestore (NoSQL) |
| **Vector Store** | FAISS (local), optional Pinecone |
| **LLM Providers** | Groq (LLaMA 3.3 70B), Google Gemini |
| **Forecasting** | Amazon Chronos-Bolt (AutoGluon) |
| **Auth** | Firebase Authentication |
| **Deployment** | Render (backend), Expo EAS (mobile) |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm`
- **Firebase Project** with Firestore enabled
- **API Keys**: Gemini API (Google AI Studio), Groq API

---

### 1️⃣ Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Configure Environment:**

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values
nano .env  # or use any editor
```

```bash
# backend/.env
GOOGLE_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
FIREBASE_CREDENTIALS=./firebase-service-account.json
```

**Add Firebase Credentials:**

1. Go to [Firebase Console](https://console.firebase.google.com/) → Project Settings → Service Accounts
2. Click **"Generate new private key"**
3. Save the JSON file as `backend/firebase-service-account.json`

**Bind to Your IPv4 Address:**

Find your local IPv4:
```bash
# Linux
ip addr | grep "inet " | grep -v 127.0.0.1

# macOS
ipconfig getifaddr en0

# Windows
ipconfig | findstr IPv4
```

Edit `backend/main.py` and set your IPv4:
```python
if __name__ == "__main__":
    uvicorn.run(app, host="YOUR_IPV4_ADDRESS", port=8000)
    # Example: uvicorn.run(app, host="192.168.1.100", port=8000)
```

**Start the Server:**

```bash
python main.py
# Server runs at http://YOUR_IPV4:8000
```

---

### 2️⃣ Frontend Setup

```bash
# Navigate to App
cd App

# Install dependencies
npm install

# Or with Expo
npx expo install
```

**Configure Server URL:**

Edit `App/services/apiService.js` and set `BASE_URL` to your backend:

```javascript
// Line 17 - Update to your backend IPv4
const BASE_URL = 'http://YOUR_IPV4_ADDRESS:8000';
// Example: const BASE_URL = 'http://192.168.1.100:8000';
```

**Launch the App:**

```bash
# Start Expo dev server
npx expo start

# Scan QR code with Expo Go app (iOS/Android)
# Or press 'a' for Android emulator, 'i' for iOS simulator
```

---

### 📱 Quick Start Summary

| Step | Command | Location |
|------|---------|----------|
| 1. Setup venv | `python -m venv venv && source venv/bin/activate` | `backend/` |
| 2. Install deps | `pip install -r requirements.txt` | `backend/` |
| 3. Configure env | `cp .env.example .env` + add Firebase JSON | `backend/` |
| 4. Set IPv4 | Edit `host` in `main.py` | `backend/main.py` |
| 5. Start backend | `python main.py` | `backend/` |
| 6. Install frontend | `npm install` | `App/` |
| 7. Set API URL | Edit `BASE_URL` in `apiService.js` | `App/services/` |
| 8. Launch app | `npx expo start` | `App/` |

---

## 🔐 Environment Variables Reference

```bash
# backend/.env.example
GOOGLE_API_KEY=           # Gemini API key (Google AI Studio)
GROQ_API_KEY=             # Groq API key (console.groq.com)
FIREBASE_CREDENTIALS=     # Path to Firebase service account JSON
OVERPASS_API_URL=         # Optional: for hospital/outlet search
```

---

## 📝 License

This project is developed as part of academic research. Contact maintainers for licensing inquiries.

---

<p align="center">
  <strong>Built with 🩺 for maternal health</strong>
</p>
