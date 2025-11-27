create table if not exists conversation_sessions (
    id uuid primary key default gen_random_uuid(),
    external_id text,
    user_id text,
    title text,
    summary jsonb,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists conversation_turns (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references conversation_sessions(id) on delete cascade,
    turn_index integer,
    speaker text,
    text text,
    timestamp numeric,
    emotions jsonb,
    psych_labels jsonb,
    stress jsonb,
    artifact text,
    created_at timestamptz default now()
);

create table if not exists conversation_state_trace (
    session_id uuid references conversation_sessions(id) on delete cascade,
    point_index integer,
    timestamp numeric,
    values jsonb,
    primary key (session_id, point_index)
);

create table if not exists conversation_rules_fired (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references conversation_sessions(id) on delete cascade,
    rule_id text,
    description text,
    action text,
    telemetry_key text,
    created_at timestamptz default now()
);

create extension if not exists vector;

create table if not exists conversation_embeddings (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references conversation_sessions(id) on delete cascade,
    turn_index integer,
    embedding_name text,
    embedding vector(1536),
    created_at timestamptz default now()
);

create index if not exists conversation_embeddings_session_idx on conversation_embeddings(session_id);
create index if not exists conversation_turns_session_idx on conversation_turns(session_id);
create index if not exists conversation_state_trace_session_idx on conversation_state_trace(session_id);

