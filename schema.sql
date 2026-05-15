CREATE TABLE IF NOT EXISTS pages_monthly (
    page TEXT NOT NULL,
    month TEXT NOT NULL,
    cluster TEXT,
    keywords_count INTEGER,
    top_keyword TEXT,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    position REAL DEFAULT 0,
    traffic_value REAL,
    is_estimated INTEGER DEFAULT 0,
    PRIMARY KEY (page, month)
);

CREATE INDEX IF NOT EXISTS idx_pm_cluster_month ON pages_monthly(cluster, month);
CREATE INDEX IF NOT EXISTS idx_pm_month ON pages_monthly(month);

CREATE TABLE IF NOT EXISTS keywords_monthly (
    keyword TEXT NOT NULL,
    month TEXT NOT NULL,
    top_url TEXT,
    cluster TEXT,
    urls_count INTEGER,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    position REAL DEFAULT 0,
    is_estimated INTEGER DEFAULT 0,
    PRIMARY KEY (keyword, month)
);

CREATE INDEX IF NOT EXISTS idx_km_cluster_month ON keywords_monthly(cluster, month);
CREATE INDEX IF NOT EXISTS idx_km_month ON keywords_monthly(month);

CREATE TABLE IF NOT EXISTS cluster_config (
    cluster TEXT PRIMARY KEY,
    url_patterns TEXT NOT NULL,
    parent_domain TEXT
);
