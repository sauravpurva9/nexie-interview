import os
import time
import json
import logging
from typing import Optional

import pandas as pd
import openai
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class HighRiskCustomerSummarizer:

    def __init__(self, model_name, api_key):

        self.api_key = api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY env var or pass api_key.")

        self.model_name = model_name
        self.client = openai.OpenAI(api_key=self.api_key, http_client=httpx.Client())
        logger.info(f"Using model: {self.model_name}")

    def _df_to_compact_markdown(self,df: pd.DataFrame, max_rows: int = 100, max_chars: int = 12000):

        if df.empty:
            return "No rows – dataframe is empty."

        sampled_df = df.head(max_rows).copy()

        def truncate_cell(x, max_len=200):
            s = str(x)
            return s if len(s) <= max_len else s[:max_len] + "..."

        sampled_df = sampled_df.applymap(truncate_cell)

        table = sampled_df.to_markdown(index=False)

        while len(table) > max_chars and len(sampled_df) > 5:
            sampled_df = sampled_df.head(len(sampled_df) // 2)
            table = sampled_df.to_markdown(index=False)

        return table

    def summarize_dataframe(self, df: pd.DataFrame, extra_context: str = "", max_words: int = 200) -> str:

        if df.empty:
            return "The input dataframe is empty. No high-risk customers to analyze."

        table_markdown = self._df_to_compact_markdown(df)
        columns_list = ", ".join(map(str, df.columns))        

        user_instruction = f"""
        You are an experienced e-commerce retention and churn analytics expert.

        You are given a dataset of **high churn-risk users** for an e-commerce brand in a table format.
        Each row is a user; each column is a feature (e.g., orders, recency, sum_revenue, etc.).

        Columns:
        {columns_list}

        Table (sample of high-risk churn users):
        {table_markdown}

        {"Additional business context:\n" + extra_context if extra_context else ""}

        TASK:
        Provide a concise to the point analytical summary (max {max_words} words) covering:
        1. Key patterns and segments among these high churn-risk users 
        (e.g., count_conversions, unique_sku, sum_revenue).
        2. Likely drivers or correlates of churn based on the available columns 
        (e.g., declining frequency, unique_sku, etc).
        3. Any obvious data quality issues, feature gaps, or missing fields that limit churn analysis.
        4. 3–5 concrete, actionable recommendations for the e-commerce retention / CRM / growth team, such as:
        - Targeted campaigns and offers
        - Journey or lifecycle interventions
        - Product / UX / service improvements
        - Experiments or cohorts to track

        Write the answer as short paragraphs and bullet points. Avoid repeating the raw table.
        """
        start = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in e-commerce churn and retention analysis who writes clear, concise insights for CRM and growth teams."
                    },
                    {"role": "user", "content": user_instruction}
                ],
                temperature=0.3,
            )
            latency_ms = (time.perf_counter() - start) * 1000.0
            logger.info(f"LLM summary generated in {latency_ms:.2f} ms")

            summary = response.choices[0].message.content
            return summary.strip()

        except Exception as e:
            logger.error(f"Error while generating summary: {e}")
            return f"Error while generating summary: {e}"
