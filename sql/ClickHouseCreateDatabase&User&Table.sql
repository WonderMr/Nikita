CREATE DATABASE IF NOT EXISTS zhr1c;
CREATE USER IF NOT EXISTS zhr1c_user IDENTIFIED WITH plaintext_password BY '';

GRANT ALL PRIVILEGES ON zhr1c.* TO zhr1c_user;

 CREATE TABLE logs
(
    date  UInt64,   -- соответствует \{(\d{14})
    date_idx DateTime, -- для наглядности
    t_status  String,   -- соответствует ,(\w)
    t_id  String,   -- соответствует ,\r*\n\{([0-9a-f]+)
    t_pos String,
    user_id  String,   -- соответствует ,([0-9a-f]+)\}
    user_name String,
    user_guid String,
    comp_id  String,   -- соответствует ,(\d+)
    app_id  String,   -- соответствует ,(\d+)
    conn_id  UInt64,   -- соответствует ,(\d+)
    event_id  String,   -- соответствует ,(\d+)
    severity  String,   -- соответствует ,(\d+)
    comment String,   -- соответствует ,(\w)
    meta_uuid String,   -- соответствует ,"([^ꡏ]*?)(?=",\d+,\r*\n)"
    meta_name String,   -- соответствует ,"([^ꡏ]*?)(?=",\d+,\r*\n)"
    data String,   -- соответствует ,(\d+)
    data_pres String,   -- соответствует ,\r*\n\{([^ꡏ]*?)(?=\},")
    server_id String,   -- соответствует \},"([^ꡏ]*?)(?=",\d+)"
    port_id UInt64,   -- соответствует ,(\d+)
    port_sec_id UInt64,   -- соответствует ,(\d+)
    session_id UInt64,   -- соответствует ,(\d+)
    area_id UInt64,   -- соответствует ,(\d+)
    area_sec_id UInt64,    -- соответствует ,(\d+)
    sign Int8 DEFAULT 1
)
ENGINE = CollapsingMergeTree(sign)
ORDER BY (date, t_status, t_id, t_pos, user_id, user_name, user_guid, comp_id, app_id, conn_id, event_id, severity, comment, meta_uuid, meta_name, data, data_pres, server_id, port_id, port_sec_id, session_id, area_id,  area_sec_id)
SETTINGS index_granularity = 8192;
