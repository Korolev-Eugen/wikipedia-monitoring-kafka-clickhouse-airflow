SELECT 'Initializing database...' AS message;

CREATE TABLE IF NOT EXISTS wiki_edits (
      timestamp DateTime,
      title String,
      user String,
      is_bot Bool,
      server_name String
) ENGINE = MergeTree()
      ORDER BY (timestamp, title);

CREATE TABLE IF NOT EXISTS wiki_stats (
        date Date,
        hour DateTime,
        edits_count UInt64,
        unique_users UInt64,
        bot_edits_ratio Float64,
        top_article Array(String),
        projects Map(String, UInt64)
) ENGINE = MergeTree()
        ORDER BY (date, hour);
