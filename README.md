
# Interview Agent - FastAPI service

<a target="_blank" href="https://colab.research.google.com/github/https://colab.research.google.com/drive/15df8PoaRNlotRZiaEAoegjO2OvUBiiI-?usp=sharing">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a><br>
This repository contains a FastAPI service that implements an intelligent interview agent. The agent conducts technical coding interviews and experience-based interviews, evaluates candidates' responses, and provides scoring. It uses LangGraph for orchestrating the interview flow and LangChain for managing the conversational interactions. The service supports resume parsing from PDF documents and dynamically generates questions based on job descriptions and candidate profiles.

### **Key Features**:
- AI-powered coding and experience interviews
- Resume parsing and analysis
- Dynamic question generation based on job requirements
- Structured evaluation and scoring
- Real-time conversation via Server-Sent Events


### **Running the service**:
```bash
# Clone the repository
git clone https://github.com/aayushjoshi-12/interviewer.git
cd interviewer

# Setup with UV (recommended)
uv venv
source .venv/bin/activate
uv sync --no-dev

# OR Standard Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload
```

The service will be available at http://localhost:8000.

## API Endpoints

### Start an Interview

**Endpoint:** `POST /start` <br>
**Description:** Initiates a new interview session. <br>
**Request Body:**

```json
{
  "job_description": "Software Engineer role with 5 years experience required",
  "resume": "Base64-encoded PDF or text resume content",
  "thread_id": "optional-unique-id"
}
```

**Response:**

```json
"content": {
    "text/event-stream": {
        "example": "data: {'type': 'token', 'content': 'Hello'}\n\ndata: {'type': 'token', 'content': ' World'}\n\ndata: [DONE]\n\n",
        "schema": {"type": "string"},
    }
},
```

---

### Continue a Conversation

**Endpoint:** `POST /stream`
<br>
**Description:** Sends a message to an ongoing interview.
<br>
**Request Body:**

```json
{
  "message": "What are the job responsibilities?",
  "thread_id": "unique-conversation-id"
}
```

**Response:**

- Server-Sent Event stream of messages and tokens from the agent

---

### Get Chat History

**Endpoint:** `GET /history`
<br>
**Description:** Retrieves the complete conversation history.
<br>
**Query Parameters:**

```json
{
  "thread_id": "unique-conversation-id"
}
```

**Response:**

```json
[
  { "user": "Hello", "agent": "Hi, how can I assist you today?" },
  { "user": "Tell me about the job", "agent": "Sure, here are the details..." }
]
```

---

### Get Conversation State

**Endpoint:** `GET /state`
<br>
**Description:** Retrieves the full state of the conversation.
<br>
**Query Parameters:**

```json
{
  "thread_id": "unique-conversation-id"
}
```

**Response:**

```json
{
  "current_question": "What are your strengths?",
  "previous_responses": [
    { "question": "Tell me about yourself", "answer": "I am a software engineer..." }
  ],
  "status": "ongoing"
}
```

---

### Health Check

**Endpoint:** `GET /health`
<br>
**Description:** Simple health check endpoint.
<br>
**Response:**

```json
{
  "status": "ok"
}
```

