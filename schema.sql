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

CREATE TABLE IF NOT EXISTS keyword_volumes (
    keyword TEXT PRIMARY KEY,
    volume INTEGER,
    cpc INTEGER,
    difficulty INTEGER,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_kv_volume ON keyword_volumes(volume DESC);

CREATE TABLE IF NOT EXISTS organic_competitors (
    competitor_domain TEXT PRIMARY KEY,
    keywords_common INTEGER,
    keywords_target INTEGER,
    keywords_competitor INTEGER,
    traffic INTEGER,
    domain_rating REAL,
    share REAL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS serp_snapshots (
    keyword TEXT NOT NULL,
    position INTEGER NOT NULL,
    url TEXT,
    domain TEXT,
    domain_rating REAL,
    traffic INTEGER,
    updated_at TEXT,
    PRIMARY KEY (keyword, position, url)
);

CREATE INDEX IF NOT EXISTS idx_serp_domain ON serp_snapshots(domain);
CREATE INDEX IF NOT EXISTS idx_serp_keyword ON serp_snapshots(keyword);

CREATE TABLE IF NOT EXISTS cluster_config (
    cluster TEXT PRIMARY KEY,
    url_patterns TEXT NOT NULL,
    parent_domain TEXT
);
