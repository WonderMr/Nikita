CREATE DATABASE IF NOT EXISTS zhr1c;
CREATE USER IF NOT EXISTS zhr1c_user IDENTIFIED WITH plaintext_password BY '';

GRANT ALL PRIVILEGES ON zhr1c.* TO zhr1c_user;

 CREATE TABLE zp_kz1
(
    r1  UInt64,   -- соответствует \{(\d{14})
    r1a DateTime, -- для наглядности
    r2  String,   -- соответствует ,(\w)
    r3  String,   -- соответствует ,\r*\n\{([0-9a-f]+)
    r3a String,
    r4  String,   -- соответствует ,([0-9a-f]+)\}
    r4name String,
    r4guid String,
    r5  String,   -- соответствует ,(\d+)
    r6  String,   -- соответствует ,(\d+)
    r7  UInt64,   -- соответствует ,(\d+)
    r8  String,   -- соответствует ,(\d+)
    r9  String,   -- соответствует ,(\d+)
    r10 String,   -- соответствует ,(\w)
    r11uuid String,   -- соответствует ,"([^ꡏ]*?)(?=",\d+,\r*\n)"
    r11name String,   -- соответствует ,"([^ꡏ]*?)(?=",\d+,\r*\n)"
    r12 String,   -- соответствует ,(\d+)
    r13 String,   -- соответствует ,\r*\n\{([^ꡏ]*?)(?=\},")
    r14 String,   -- соответствует \},"([^ꡏ]*?)(?=",\d+)"
    r15 UInt64,   -- соответствует ,(\d+)
    r16 UInt64,   -- соответствует ,(\d+)
    r17 UInt64,   -- соответствует ,(\d+)
    r18 UInt64,   -- соответствует ,(\d+)
    r19 UInt64,    -- соответствует ,(\d+)
    version UInt8 DEFAULT 1
)
ENGINE = ReplacingMergeTree
ORDER BY (r1, r2, r3, r3a, r4, r4name, r4guid, r5, r6, r7, r8, r9, r10, r11uuid, r11name, r12, r13, r14, r15, r16, r17, r18,  r19)
SETTINGS index_granularity = 8192;









