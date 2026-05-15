import pandas as pd

# Real cluster data from GSC audit (last 3 months)
CLUSTER_SUMMARY = pd.DataFrame([
    {"cluster": "Grok",          "clicks": 21193, "impressions": 7615477, "ctr": 0.28, "avg_position": 6.2},
    {"cluster": "Canva",         "clicks": 8970,  "impressions": 1368499, "ctr": 0.66, "avg_position": 6.7},
    {"cluster": "GitHub",        "clicks": 4862,  "impressions": 707489,  "ctr": 0.69, "avg_position": 7.1},
    {"cluster": "Claude",        "clicks": 4025,  "impressions": 570124,  "ctr": 0.71, "avg_position": 7.8},
    {"cluster": "NotebookLM",    "clicks": 3456,  "impressions": 171889,  "ctr": 2.01, "avg_position": 4.9},
    {"cluster": "Confluence",    "clicks": 2282,  "impressions": 124443,  "ctr": 1.83, "avg_position": 5.2},
    {"cluster": "LinkedIn",      "clicks": 1718,  "impressions": 333905,  "ctr": 0.51, "avg_position": 8.4},
    {"cluster": "ChatGPT",       "clicks": 1236,  "impressions": 545591,  "ctr": 0.23, "avg_position": 7.3},
    {"cluster": "MS Excel",      "clicks": 1209,  "impressions": 142010,  "ctr": 0.85, "avg_position": 6.8},
    {"cluster": "Adobe Acrobat", "clicks": 1071,  "impressions": 135502,  "ctr": 0.79, "avg_position": 7.2},
    {"cluster": "Linear",        "clicks": 765,   "impressions": 25902,   "ctr": 2.95, "avg_position": 3.8},
    {"cluster": "Lovable",       "clicks": 662,   "impressions": 113358,  "ctr": 0.58, "avg_position": 9.1},
    {"cluster": "Notion",        "clicks": 563,   "impressions": 28931,   "ctr": 1.95, "avg_position": 8.9},
    {"cluster": "GitLab",        "clicks": 563,   "impressions": 25213,   "ctr": 2.23, "avg_position": 4.6},
    {"cluster": "Jira",          "clicks": 543,   "impressions": 44136,   "ctr": 1.23, "avg_position": 7.8},
    {"cluster": "Bitbucket",     "clicks": 467,   "impressions": 19705,   "ctr": 2.37, "avg_position": 4.2},
    {"cluster": "Slack",         "clicks": 447,   "impressions": 75343,   "ctr": 0.59, "avg_position": 8.6},
])

# Position distribution per cluster (queries count in each bucket)
# Format: top 1.5 = absolute #1, top 3, top 5, top 10
POSITION_DISTRIBUTION = pd.DataFrame([
    {"cluster": "Notion",     "top_1_5": 61,  "top_3": 351,  "top_5": 520,  "top_10": 890,  "peak_top_1_5": 114, "peak_top_3": 480},
    {"cluster": "Canva",      "top_1_5": 18,  "top_3": 120,  "top_5": 290,  "top_10": 680,  "peak_top_1_5": 299, "peak_top_3": 510},
    {"cluster": "Grok",       "top_1_5": 45,  "top_3": 210,  "top_5": 380,  "top_10": 720,  "peak_top_1_5": 60,  "peak_top_3": 240},
    {"cluster": "NotebookLM", "top_1_5": 38,  "top_3": 95,   "top_5": 140,  "top_10": 210,  "peak_top_1_5": 30,  "peak_top_3": 75},
    {"cluster": "Linear",     "top_1_5": 22,  "top_3": 48,   "top_5": 70,   "top_10": 98,   "peak_top_1_5": 18,  "peak_top_3": 42},
    {"cluster": "Confluence",  "top_1_5": 29,  "top_3": 72,   "top_5": 110,  "top_10": 180,  "peak_top_1_5": 25,  "peak_top_3": 65},
    {"cluster": "ChatGPT",    "top_1_5": 12,  "top_3": 68,   "top_5": 190,  "top_10": 450,  "peak_top_1_5": 80,  "peak_top_3": 220},
    {"cluster": "GitHub",     "top_1_5": 31,  "top_3": 140,  "top_5": 260,  "top_10": 490,  "peak_top_1_5": 55,  "peak_top_3": 180},
])

# Monthly trend data (mocked based on the audit narrative)
import numpy as np

months = pd.date_range("2025-01-01", periods=16, freq="MS")

def _notion_trend():
    clicks =      [4200, 4800, 5100, 4700, 3800, 2900, 2100, 1600, 1200, 900,  750,  650,  590,  570,  555,  563]
    impressions =  [120000,145000,160000,175000,190000,200000,195000,185000,170000,155000,140000,120000,35000,30000,29000,28931]
    ctr =         [3.5,  3.3,  3.2,  2.7,  2.0,  1.4,  1.1,  0.86, 0.71, 0.58, 0.54, 0.54, 1.69, 1.90, 1.92, 1.95]
    position =    [3.2,  2.8,  2.5,  2.7,  3.1,  4.2,  5.8,  7.1,  8.0,  8.5,  8.7,  8.8,  8.9,  8.9,  8.9,  8.9]
    return clicks, impressions, ctr, position

def _canva_trend():
    clicks =      [18000,21000,22000,19000,14000,9500, 7000, 5500, 4200, 3100, 2400, 2000, 1500, 1100, 900,  897]
    impressions =  [260000,310000,320000,350000,400000,900000,1100000,1200000,1250000,1300000,1330000,1350000,1360000,1365000,1368000,1368499]
    ctr =         [6.9,  6.8,  6.9,  5.4,  3.5,  1.06, 0.64, 0.46, 0.34, 0.24, 0.18, 0.15, 0.11, 0.08, 0.07, 0.066]
    position =    [4.1,  3.8,  3.5,  4.2,  5.1,  6.0,  6.3,  6.5,  6.5,  6.6,  6.7,  6.7,  6.7,  6.7,  6.7,  6.7]
    return clicks, impressions, ctr, position

MONTHLY_TRENDS = {}
for cluster, fn in [("Notion", _notion_trend), ("Canva", _canva_trend)]:
    c, i, r, p = fn()
    MONTHLY_TRENDS[cluster] = pd.DataFrame({
        "month": months,
        "clicks": c,
        "impressions": i,
        "ctr": r,
        "avg_position": p,
    })

# Top queries per cluster with CTR signal
TOP_QUERIES = {
    "Grok": pd.DataFrame([
        {"query": "how to cancel grok subscription",    "clicks": 42,   "impressions": 9552,  "ctr": 0.44, "position": 4.1, "signal": "AIO"},
        {"query": "grok subscription",                  "clicks": 44,   "impressions": 5449,  "ctr": 0.81, "position": 5.2, "signal": "AIO"},
        {"query": "grok image downloader",              "clicks": 890,  "impressions": 7740,  "ctr": 11.5, "position": 2.1, "signal": "Healthy"},
        {"query": "bypass grok limit",                  "clicks": 310,  "impressions": 2088,  "ctr": 14.8, "position": 1.8, "signal": "Healthy"},
        {"query": "grok image download by link",        "clicks": 198,  "impressions": 500,   "ctr": 39.6, "position": 1.2, "signal": "Healthy"},
    ]),
    "Notion": pd.DataFrame([
        {"query": "how to merge cells in notion",       "clicks": 27,   "impressions": 4200,  "ctr": 0.64, "position": 5.1, "signal": "AIO"},
        {"query": "notion progress bar",                "clicks": 18,   "impressions": 6100,  "ctr": 0.30, "position": 3.8, "signal": "AIO"},
        {"query": "notion database tutorial",           "clicks": 9,    "impressions": 8900,  "ctr": 0.10, "position": 4.2, "signal": "AIO"},
    ]),
    "NotebookLM": pd.DataFrame([
        {"query": "notebooklm confluence integration",  "clicks": 210,  "impressions": 786,   "ctr": 26.7, "position": 2.1, "signal": "Healthy"},
        {"query": "notebooklm slack",                   "clicks": 145,  "impressions": 928,   "ctr": 15.6, "position": 2.4, "signal": "Healthy"},
        {"query": "notebooklm notion",                  "clicks": 98,   "impressions": 1237,  "ctr": 7.92, "position": 3.1, "signal": "Healthy"},
    ]),
    "Confluence": pd.DataFrame([
        {"query": "confluence center table",            "clicks": 180,  "impressions": 483,   "ctr": 37.3, "position": 1.9, "signal": "Healthy"},
        {"query": "how to center a table in confluence","clicks": 156,  "impressions": 520,   "ctr": 30.0, "position": 2.1, "signal": "Healthy"},
        {"query": "confluence cancel unpublished changes","clicks":89,  "impressions": 601,   "ctr": 14.8, "position": 2.3, "signal": "Healthy"},
    ]),
    "Linear": pd.DataFrame([
        {"query": "linear custom fields",               "clicks": 142,  "impressions": 543,   "ctr": 26.1, "position": 2.8, "signal": "Healthy"},
        {"query": "linear timeline view",               "clicks": 98,   "impressions": 618,   "ctr": 15.9, "position": 3.1, "signal": "Healthy"},
    ]),
}
