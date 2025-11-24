# CourtDominion

CourtDominion is a lightweight, AI-powered **fantasy basketball insights engine** designed to help players make smarter lineup decisions, discover undervalued players, and get fast, clean projections.

This repository contains the complete platform:

- **Backend (FastAPI)** — serves insights, projections, player data  
- **Automation Engine (Python)** — computes projections, risk, value, insights  
- **Frontend (Next.js/React)** — user interface & marketing pages  
- **Dockerized Dev Environment** — local + production-aligned runtime  
- **Railway Deployment Ready**

Everything is designed for clarity, stability, and ease of deployment.

---

## 📦 Repository Structure

to be filled in

---

## 🚀 Platform Overview

### Backend (FastAPI)
- Stateless API server  
- Endpoints: players, projections, insights, risk metrics  
- Loads JSON from automation output  
- Runs under Docker locally & on Railway

### Automation Engine
- Ingests raw data → normalizes → computes projections  
- Computes insights, risk, value, opportunity index  
- Exports JSON to shared volume for backend

### Frontend
- Next.js + React  
- Tailwind CSS  
- Clean insights UI  
- Marketing pages  
- Clerk login optional

---

## 🐳 Local Development (Docker)

From inside:

courtdominion-app/docker


Run:

docker compose up --build


You get:
- Backend on `http://localhost:8000`
- Automation runs once and writes JSON
- Shared outputs stored in `shared-outputs/`

---

## 🌐 Production Deployment (Railway)

- Backend & Automation each run as services  
- Shared volume at `/data/outputs`  
- One-click deploy from GitHub  
- Database added in Phase 2

---

## 📅 Launch Target
**January 26, 2026  
Free-for-rest-of-season Fantasy Basketball Insights Engine**

---

## 📄 License
Private / Proprietary



