-- Purpose: Rename ABT login bucket columns from login_f* to login_v* in Supabase.
-- Used by: Manual Supabase SQL Editor or psql before re-uploading fake_account_abt.
-- Main dependencies: Existing fake_account_abt table with login_f* columns.
-- Public/main objects: fake_account_abt column rename migration.
-- Side effects: Renames existing columns in Supabase; does not add or drop data rows.

ALTER TABLE fake_account_abt RENAME COLUMN login_f1h TO login_v1h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f2h TO login_v2h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f3h TO login_v3h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f4h TO login_v4h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f5h TO login_v5h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f6h TO login_v6h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f12h TO login_v12h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f18h TO login_v18h;
ALTER TABLE fake_account_abt RENAME COLUMN login_f24h TO login_v24h;
