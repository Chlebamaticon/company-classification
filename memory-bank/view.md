# View

High-level architecture (MVP).

```mermaid
flowchart LR
    subgraph Client["Client"]
        SPA["React SPA<br/>(Vite + TS + Tailwind)"]
    end

    subgraph Backend["Backend"]
        API["FastAPI"]
        MQ{{"RabbitMQ"}}
    end

    subgraph Workers["Workers"]
        CW["Classification<br/>Worker"]
        DI["Doc Ingest<br/>Worker"]
        WC["Web Crawl<br/>Worker"]
    end

    subgraph Data["Data"]
        PG[("Postgres")]
    end

    subgraph External["External"]
        LLM["OpenAI"]
    end

    SPA -->|"HTTP POST /submissions"| API
    API -->|"SSE /submissions/{id}/events"| SPA

    API -->|"persist submission"| PG
    API -->|"publish classify.request"| MQ

    MQ -->|"classify.request"| CW
    CW -->|"ingest.request (RPC)"| MQ
    CW -->|"crawl.request (RPC)"| MQ
    MQ -->|"ingest.request"| DI
    MQ -->|"crawl.request"| WC
    DI -->|"reply"| MQ
    WC -->|"reply"| MQ
    MQ -->|"reply"| CW

    CW -->|"HTTPS chat.completions"| LLM
    CW -->|"events + result"| PG
    DI -->|"persist artifacts"| PG
    WC -->|"persist artifacts"| PG

    PG -->|"LISTEN/NOTIFY<br/>submission_events:{id}"| API
```

Legend:
- Solid arrows = data/control flow.
- `{{...}}` = message broker, `[(...)]` = database, `[...]` = service.
- AMQP traffic between workers is RPC (`reply_to` + `correlation_id`).
- One classification per submission; FSC catalog is loaded in-process by the Classification Worker.
