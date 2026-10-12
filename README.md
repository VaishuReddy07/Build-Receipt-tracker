# Multimodel Receipt Tracker

An AI-powered receipt scanner built with Streamlit and Google Gemini. Upload a receipt image, review the extracted merchant, date, total, currency, category, and line items, then save it to local JSON storage. Explore category and monthly spending charts or search and delete receipt history.

## Features

- Receipt image extraction with Gemini 2.5 Flash
- Suggested expense category and editable receipt details
- Dashboard with category donut chart and monthly spending chart
- Searchable and filterable history with receipt deletion
- Local JSON storage; no database required
- API key stays in a local `.env` file and is not committed

## Requirements

- Python 3.10 or newer
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

## Run locally

```bash
git clone https://github.com/VaishuReddy07/Build-Receipt-tracker.git
cd Build-Receipt-tracker
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install packages and configure the key:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then set `GEMINI_API_KEY` to your key. Start the app:

```bash
streamlit run app.py
```

The first saved receipt creates `data/receipts.json`. Receipt data and images stay on your machine; images are sent to Google Gemini only when you scan them. The app does not save uploaded images.

## Project layout

```text
multimodel-receipt-tracker/
├── app.py              # Streamlit upload, dashboard, and history UI
├── parser.py           # Gemini image extraction and validation
├── storage.py          # Local JSON persistence
├── requirements.txt
├── .env.example
├── .gitignore
└── data/               # Created on first save; receipt data is git-ignored
```

## Notes

AI extraction can make mistakes, so review the receipt details before saving. Spending totals are not converted between currencies; if your receipts use multiple currencies, the dashboard displays a notice.
