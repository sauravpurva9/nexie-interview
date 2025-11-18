import os
import numpy as np
import pandas as pd
import streamlit as st
import requests
from open_ai_summary import HighRiskCustomerSummarizer
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

voice_api_url = "http://localhost:8000/call_user"
# voice_result_url = "http://localhost:8000/get_call_result" 

if "call_responses" not in st.session_state:
    st.session_state["call_responses"] = {}

def load_data():
    df = pd.read_csv("data/churn_probability.csv")
    return df

df = load_data()


def add_risk_bucket(data):

    df = pd.read_csv('data/churn_probability.csv')
    churn_dict = {'<40': 'Low', '40-80': 'Medium', '80-99': 'High', '>99': 'At Risk'}
    df['churn_bucket_new'] = df['churn_bucket'].map(churn_dict)
    df['churn_probability'] = df['churn_probability'].apply(lambda x: round(x, 2))
    df = df.rename(columns = {'user_id': 'User Id', 'churn_bucket_new': 'Risk Bucket', 'churn_probability': 'Churn Prob'})
    df = df.drop_duplicates(subset = ['User Id'], keep = 'first').reset_index(drop = True)
        
    return df

df = add_risk_bucket(df)

# Summary table (counts per bucket)
summary_df = df['Risk Bucket'].value_counts().reset_index().rename(columns={'Risk Bucket': 'Risk Bucket', 'count': 'No. of Users'})

high_risk_df = df[df["Risk Bucket"] == 'At Risk'].copy()

# for _, row in high_risk_df.iterrows():
#     cust_id = row["User Id"]
#     if cust_id in st.session_state["call_responses"] and "Call initiated" in st.session_state["call_responses"][cust_id]:
#         try:
#             res = requests.get(
#                 voice_result_url,
#                 params={"user_id": str(cust_id)},
#                 timeout=5,
#             )
#             if res.ok:
#                 data = res.json()
#                 if data.get("status") == "done":
#                     st.session_state["call_responses"][cust_id] = data.get("summary", "")
#         except Exception:
#             pass

#Heading
st.title("User Churn Analysis - Actions Dashboard")

#Description
st.markdown(
    """
    This dashboard shows churn risk bucket for our users & actions on high risk users.

    **Data description:**
    - Churn probability is the model-estimated probability that the user will churn in the next 2 months.
    - Users are bucketed into percentile-based risk groups for easy prioritization.
    """
)

st.divider()

# Text summary for churn analysis
st.subheader("Churn Risk Summary")

st.markdown("Users grouped by churn probability percentile buckets:")
st.dataframe(summary_df, hide_index = True)

st.divider()

# st.subheader("AI Generated summary of High Risk Customers.")

summarizer = HighRiskCustomerSummarizer(model_name="gpt-4o-mini",api_key = openai_api_key)  
summary = summarizer.summarize_dataframe(high_risk_df, extra_context="These are customers with high probability to churn in next 2 months")

st.markdown(f"{summary}")
st.divider()

# high risk Users
st.subheader("High-Risk Users")

st.markdown("Showing users above 99th percentile of churn probability")

cols_to_show = ["User Id", "Churn Prob", "Risk Bucket"]
high_risk_display = high_risk_df[cols_to_show].reset_index(drop=True).copy()

high_risk_display["Call"] = high_risk_display["User Id"].map(lambda uid: uid in st.session_state["call_responses"])

high_risk_display["Response"] = high_risk_display["User Id"].map(lambda uid: st.session_state["call_responses"].get(uid, ""))

st.markdown("### High-risk users and actions")

edited_df = st.data_editor(
    high_risk_display.sort_values(['Churn Prob'], ascending = False),
    use_container_width=True,
    hide_index=True,
    disabled=["User Id", "Churn Prob", "Risk Bucket", "Response"],
    key="high_risk_editor",
)

call_rows = edited_df[edited_df["Call"] == True]

did_update = False 

for _, row in call_rows.iterrows():
    cust_id = row["User Id"]
    churn_prob = row["Churn Prob"]

    if cust_id in st.session_state["call_responses"]:
        continue

    try:
        user_phone_number = row.get("phone_number", "+917397463121")

        payload = {
            "user_id": str(cust_id),
            "phone_number": user_phone_number,
            "message": (
                f"Hi user {cust_id}, we noticed a decline in your purchase activity from brand x, We would like to check if you are facing any issues."
            ),
        }

        resp = requests.post(
            voice_api_url,
            json=payload,
            timeout=15,
        )

        if resp.ok:
            data = resp.json()
            call_sid = data.get("call_sid", "")
            summary = f"Call initiated (SID: {call_sid})"
            st.session_state["call_responses"][cust_id] = summary
            st.success(f"Call triggered for user {cust_id}")
        else:
            msg = f"API error {resp.status_code}: {resp.text}"
            st.session_state["call_responses"][cust_id] = msg
            st.error(msg)

        did_update = True

    except Exception as e:
        msg = f"Failed to call voice API for customer {cust_id}: {e}"
        st.session_state["call_responses"][cust_id] = msg
        st.error(msg)
        did_update = True

if did_update:
    st.rerun()
