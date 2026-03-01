# VitalSync - Vers3Dynamics Local Wellness AI Platform

A privacy-first multi-agent wellness system that runs entirely on your local device using Ollama for AI inference.

## Features

- **Local-First Architecture**: All data stays on your device - no cloud processing
- **5 Specialized Agents**: Signal Ingestion, User Modeling, Interpretation, Feedback Generation, Safety Supervisor
- **Ollama Integration**: Uses local LLMs (llama3.2, phi3, qwen2.5)

## Architecture

### Agents
1. **Signal Ingestion** - Normalizes data from HealthKit, Health Connect, wearables
2. **User Modeling** - Maintains Digital Twin with baselines and preferences
3. **Interpretation** - Pattern analysis and correlation detection
4. **Feedback Generation** - RAG-powered personalized recommendations
5. **Safety Supervisor** - Medical boundary enforcement and factual verification

### Message Schema
```json
{
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "topic": "DATA_INGESTED|MODEL_UPDATED|INSIGHT_GENERATED|DRAFT_RESPONSE|FINAL_OUTPUT",
  "source_agent": "agent_name",
  "payload": {}
}
```

### Memory Model
- **Working Memory**: In-memory for active sessions
- **Long-term Memory**: Vector store for episodic/semantic memories
- **Structured Storage**: Encrypted SQLite for biometrics

## Setup

1. **Install Ollama**:
   ```bash
   ollama run llama3.2
   ```

2. **Open index.html** in your browser

3. **Start chatting** with your wellness AI!

## Local Data Input

You can import real metric series using the paperclip button in the UI.

Expected JSON format:

```json
{
  "heartRate": [68, 70, 67, 72],
  "sleep": [6.1, 6.4, 6.0, 6.5],
  "stress": [52, 49, 55, 47]
}
```

You can also push live samples from a local script by dispatching a browser event:

```js
window.dispatchEvent(new CustomEvent('vitalsync-metric', {
  detail: { metric: 'heartRate', value: 71 }
}));
```

### Local Streaming Bridge

The page now auto-connects to `http://127.0.0.1:8765/events` via SSE.

Run the included bridge:

```bash
python vitalsync_metric_bridge.py
```

Disable demo data generation:

```bash
python vitalsync_metric_bridge.py --no-demo
```

Push real samples into the bridge:

```bash
curl -X POST http://127.0.0.1:8765/push \
  -H "Content-Type: application/json" \
  -d "{\"metric\":\"heartRate\",\"value\":72}"
```

Batch push:

```json
{
  "samples": [
    {"metric": "heartRate", "value": 72},
    {"metric": "sleep", "value": 6.4},
    {"metric": "stress", "value": 48}
  ]
}
```

## Tech Stack

- HTML5, TailwindCSS, Vanilla JavaScript
- Ollama (local LLM inference)
- Local storage for data persistence

## License

MIT
