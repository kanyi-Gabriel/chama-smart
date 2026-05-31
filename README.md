# Chama Smart 🏦

A Django-powered Chama (investment group) management platform for Kenya.

## Features
- Member registration and management
- Automated M-Pesa contributions via Daraja API
- Loan application and approval system
- ML-powered credit scoring
- Automated penalty calculation
- Live draw/voting system for chama winners

## Tech Stack
- Backend: Django 6.0 + Django REST Framework
- Database: PostgreSQL
- Payments: Safaricom Daraja API
- ML: scikit-learn, pandas
- Task Queue: Celery + Redis

## Setup
```bash
git clone https://github.com/yourusername/chama-smart.git
cd chama-smart
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your values
python3 manage.py migrate
python3 manage.py runserver
```

## Environment Variables
See `.env.example` for required variables.