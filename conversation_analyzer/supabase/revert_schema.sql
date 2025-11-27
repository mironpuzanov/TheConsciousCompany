-- Revert/Cleanup: Drop all conversation analyzer tables
-- Run this in the WRONG Supabase project to clean up

-- Drop tables in reverse dependency order (children first)
DROP TABLE IF EXISTS conversation_embeddings CASCADE;
DROP TABLE IF EXISTS conversation_rules_fired CASCADE;
DROP TABLE IF EXISTS conversation_state_trace CASCADE;
DROP TABLE IF EXISTS conversation_turns CASCADE;
DROP TABLE IF EXISTS conversation_sessions CASCADE;

-- Note: We don't drop the 'vector' extension as it might be used by other tables
-- If you want to remove it completely, run:
-- DROP EXTENSION IF EXISTS vector CASCADE;

