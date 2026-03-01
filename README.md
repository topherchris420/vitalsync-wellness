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

## Tech Stack

- HTML5, TailwindCSS, Vanilla JavaScript
- Ollama (local LLM inference)
- Local storage for data persistence

## License

MIT
