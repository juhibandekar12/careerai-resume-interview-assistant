# CareerAI – AI-Powered Career Assistance System

## Overview

CareerAI is an AI-powered career assistance platform designed to help users analyze resumes, discover suitable job opportunities, prepare for interviews, and generate personalized learning roadmaps. The system leverages Natural Language Processing (NLP), Machine Learning, and Large Language Models (LLMs) to provide intelligent career guidance.

---

## Features

* Resume Analysis and Skill Extraction
* AI-Based Job Recommendation System
* AI-Powered Mock Interview Assistant
* Personalized Learning Roadmaps
* Resume-to-Job Matching using NLP
* Interactive Dashboard and Analytics
* Career Guidance using Groq AI (Llama 3.3 70B)

---

## Technology Stack

### Frontend

* Streamlit
* Plotly
* HTML5 / CSS3

### Backend

* FastAPI
* Uvicorn

### Database

* SQLite

### NLP & Machine Learning

* spaCy (`en_core_web_sm`)
* Scikit-learn
* TF-IDF Vectorization
* Cosine Similarity

### AI Integration

* Groq API
* Llama-3.3-70b-versatile

---

## Prerequisites

Before running the project, ensure the following are installed:

* Python 3.10 or above
* Internet connection
* Groq API Key

A Groq API key can be generated from:
https://console.groq.com

---

## Installation and Setup

### Step 1: Extract the Project

Extract the ZIP file and open the project folder in VS Code or any preferred IDE.

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Install spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

---

## Environment Configuration

Create a file named `.env` in the project root directory and add:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Database Initialization

Initialize and seed the database using:

```bash
python scripts/seed_db.py
```

---

## Running the Application

Start both the frontend and backend services:

```bash
python run.py
```

---

## Application URLs

After successful startup:

| Service            | URL                        |
| ------------------ | -------------------------- |
| Frontend Dashboard | http://localhost:8501      |
| Backend API        | http://localhost:8000      |
| API Documentation  | http://localhost:8000/docs |

---

## Demo Login Credentials

Username: `demo`

Password: `demo123`

---

## Project Structure

```text
ai resume and interview asssistance system/
│
├── .streamlit/
├── backend/
├── data/
├── database/
├── frontend/
├── models/
├── scripts/
├── utils/
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
├── start_backend.ps1
└── start_frontend.ps1
```

---

## Future Enhancements

* LinkedIn Profile Analysis
* ATS Resume Scoring
* Real-Time Job Market Insights
* Multi-Language Support
* AI Career Coach Chatbot
* Resume Builder Module

---

## Project Information

**Project Title:** CareerAI – AI-Powered Career Assistance System

**Domain:** Artificial Intelligence, Machine Learning, NLP

**Purpose:** Academic Internship Project

---