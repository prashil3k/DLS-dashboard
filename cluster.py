import json
import re

CLUSTER_RULES = {
    "grok": {
        "slugs": ["grok"],
        "parent_domain": "x.com",
    },
    "canva": {
        "slugs": ["canva"],
        "parent_domain": "canva.com",
    },
    "github": {
        "slugs": ["github"],
        "parent_domain": "github.com",
    },
    "claude": {
        "slugs": ["claude", "janitor-ai"],
        "parent_domain": "claude.ai",
    },
    "notebooklm": {
        "slugs": ["notebooklm", "notebook-lm"],
        "parent_domain": "notebooklm.google.com",
    },
    "confluence": {
        "slugs": ["confluence"],
        "parent_domain": "atlassian.com",
    },
    "linkedin": {
        "slugs": ["linkedin"],
        "parent_domain": "linkedin.com",
    },
    "chatgpt": {
        "slugs": ["chatgpt", "chat-gpt", "openai"],
        "parent_domain": "openai.com",
    },
    "excel": {
        "slugs": ["excel", "spreadsheet"],
        "parent_domain": "microsoft.com",
    },
    "adobe": {
        "slugs": ["acrobat", "adobe"],
        "parent_domain": "adobe.com",
    },
    "linear": {
        "slugs": ["linear"],
        "parent_domain": "linear.app",
    },
    "lovable": {
        "slugs": ["lovable"],
        "parent_domain": "lovable.dev",
    },
    "notion": {
        "slugs": ["notion"],
        "parent_domain": "notion.so",
    },
    "gitlab": {
        "slugs": ["gitlab"],
        "parent_domain": "gitlab.com",
    },
    "jira": {
        "slugs": ["jira"],
        "parent_domain": "atlassian.com",
    },
    "bitbucket": {
        "slugs": ["bitbucket"],
        "parent_domain": "bitbucket.org",
    },
    "slack": {
        "slugs": ["slack"],
        "parent_domain": "slack.com",
    },
    "salesforce": {
        "slugs": ["salesforce", "sandbox-salesforce"],
        "parent_domain": "salesforce.com",
    },
    "sharepoint": {
        "slugs": ["sharepoint"],
        "parent_domain": "microsoft.com",
    },
    "docusign": {
        "slugs": ["docusign"],
        "parent_domain": "docusign.com",
    },
    "teams": {
        "slugs": ["teams", "microsoft-teams"],
        "parent_domain": "microsoft.com",
    },
    "calendly": {
        "slugs": ["calendly"],
        "parent_domain": "calendly.com",
    },
    "hubspot": {
        "slugs": ["hubspot"],
        "parent_domain": "hubspot.com",
    },
    "google-meet": {
        "slugs": ["google-meet"],
        "parent_domain": "google.com",
    },
    "figma": {
        "slugs": ["figma"],
        "parent_domain": "figma.com",
    },
    "zoom": {
        "slugs": ["zoom"],
        "parent_domain": "zoom.us",
    },
    "google-forms": {
        "slugs": ["google-form"],
        "parent_domain": "google.com",
    },
    "mailchimp": {
        "slugs": ["mailchimp"],
        "parent_domain": "mailchimp.com",
    },
    "wordpress": {
        "slugs": ["wordpress"],
        "parent_domain": "wordpress.com",
    },
    "webflow": {
        "slugs": ["webflow"],
        "parent_domain": "webflow.com",
    },
    "dropbox": {
        "slugs": ["dropbox"],
        "parent_domain": "dropbox.com",
    },
    "upwork": {
        "slugs": ["upwork"],
        "parent_domain": "upwork.com",
    },
    "perplexity": {
        "slugs": ["perplexity"],
        "parent_domain": "perplexity.ai",
    },
    "gemini": {
        "slugs": ["gemini"],
        "parent_domain": "gemini.google.com",
    },
    "replit": {
        "slugs": ["replit"],
        "parent_domain": "replit.com",
    },
    "ms-access": {
        "slugs": ["ms-access", "microsoft-access", "-in-ms-access", "-access-"],
        "parent_domain": "microsoft.com",
    },
    "asana": {
        "slugs": ["asana"],
        "parent_domain": "asana.com",
    },
    "google-analytics": {
        "slugs": ["google-analytics"],
        "parent_domain": "analytics.google.com",
    },
    "semrush": {
        "slugs": ["semrush"],
        "parent_domain": "semrush.com",
    },
}


def assign_cluster(page_url: str, keyword: str = "") -> str | None:
    slug = page_url.split("storylane.io/")[-1].lower() if "storylane.io/" in page_url else page_url.lower()

    for cluster, config in CLUSTER_RULES.items():
        for pattern in config["slugs"]:
            if pattern in slug:
                return cluster

    kw = keyword.lower()
    for cluster, config in CLUSTER_RULES.items():
        for pattern in config["slugs"]:
            if pattern in kw:
                return cluster

    return None


def seed_cluster_config(cursor):
    for cluster, config in CLUSTER_RULES.items():
        cursor.execute(
            "INSERT OR REPLACE INTO cluster_config (cluster, url_patterns, parent_domain) VALUES (?, ?, ?)",
            (cluster, json.dumps(config["slugs"]), config.get("parent_domain", "")),
        )
