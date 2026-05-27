-- SalesPatriot FSC Classifier schema
-- One-time init: docker-compose mounts this at /docker-entrypoint-initdb.d/

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS submissions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name    text NOT NULL,
    website_url     text,
    email_domain    text,
    file_path       text,
    status          text NOT NULL DEFAULT 'queued',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id   uuid NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    filename        text NOT NULL,
    raw_text        text,
    summary         jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS documents_submission_id_idx ON documents(submission_id);

CREATE TABLE IF NOT EXISTS crawls (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id   uuid NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    urls_visited    jsonb NOT NULL DEFAULT '[]'::jsonb,
    raw_text        text,
    summary         jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS crawls_submission_id_idx ON crawls(submission_id);

CREATE TABLE IF NOT EXISTS classifications (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id   uuid NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    fsc_codes       jsonb NOT NULL,
    model           text,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS classifications_submission_id_idx ON classifications(submission_id);

-- Append-only event log; SSE consumers tail it via LISTEN/NOTIFY.
CREATE TABLE IF NOT EXISTS submission_events (
    id              bigserial PRIMARY KEY,
    submission_id   uuid NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    kind            text NOT NULL,            -- 'progress' | 'result' | 'error'
    payload         jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS submission_events_submission_id_idx
    ON submission_events(submission_id, id);

-- NOTIFY on insert. Channel is per-submission so each SSE consumer LISTENs only
-- to its own stream: LISTEN "submission_events:<uuid>".
CREATE OR REPLACE FUNCTION submission_events_notify() RETURNS trigger AS $$
DECLARE
    channel text := 'submission_events:' || NEW.submission_id::text;
    msg jsonb := jsonb_build_object(
        'id', NEW.id,
        'submission_id', NEW.submission_id,
        'kind', NEW.kind,
        'payload', NEW.payload,
        'created_at', NEW.created_at
    );
BEGIN
    PERFORM pg_notify(channel, msg::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS submission_events_notify_trg ON submission_events;
CREATE TRIGGER submission_events_notify_trg
    AFTER INSERT ON submission_events
    FOR EACH ROW EXECUTE FUNCTION submission_events_notify();

-- Touch submissions.updated_at when status changes.
CREATE OR REPLACE FUNCTION submissions_touch_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS submissions_touch_updated_at_trg ON submissions;
CREATE TRIGGER submissions_touch_updated_at_trg
    BEFORE UPDATE ON submissions
    FOR EACH ROW EXECUTE FUNCTION submissions_touch_updated_at();
