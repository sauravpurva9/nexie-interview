# Nexie Interview – Churn Insights + Voice Outreach

This project is a small prototype that:

- Loads customer churn scores from a CSV.
- Lets you explore and select high-risk customers via a Streamlit app.
- Generates summaries/insights using an LLM (OpenAI).
- Can trigger voice calls via Twilio using a FastAPI server.

---

## Tech Stack

- **Language:** Python 3.10+ (tested with **Python 3.12**)
- **Frontend / UI:** Streamlit
- **Backend API:** FastAPI + Uvicorn
- **LLM / AI:** OpenAI API
- **Telephony:** Twilio
- **Data:** CSV files in `data/`

---

## Project Structure

```text
nexie_interview/
├── streamlit_run.py          # Streamlit UI for exploring churn data & summaries
├── voice_server.py           # FastAPI app for Twilio-based voice calls
├── open_ai_summary.py        # HighRiskCustomerSummarizer (OpenAI client)
├── data_generation.ipynb     # Synthetic data creation & customer cohotring
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── env.example               # Example env vars (no secrets)
├── data/
   ├── churn_probability.csv # Main file used by the app
   ├── full_training_data.csv   (optional, for reference/notebooks)
   ├── synthetic_data.csv       (optional)
   └── train_df.csv             (optional)


Command Sequence (End-to-End)
# 1. Clone
cd nexie_interview

# 2. Create & activate venv
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Create .env from env.example and fill in real values
cp env.example .env  

# 5. Start FastAPI voice server
uvicorn voice_server:app --host 0.0.0.0 --port 8000 --reload

# 6. In another terminal, start Streamlit
streamlit run streamlit_run.py
