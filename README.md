# Weather Agent Chat Interface

A Python-based chatbot that uses Google's Agent Development Kit (ADK) and Generative AI to answer questions about weather and time in different cities around the world. The application provides a modern, user-friendly web interface for interacting with the agent.

## Features

- **Interactive Chat Interface**: Modern web-based chat interface for easy interaction
- **Weather Information**: Get current weather conditions for cities worldwide using the OpenWeatherMap API
- **Weather Forecasts**: Get weather forecasts for the next few days
- **Time Lookup**: Check the current time in major cities across different time zones
- **Google AI Integration**: Powered by Gemini 2.0 Flash generative AI model
- **Built with ADK**: Uses Google's Agent Development Kit framework for flexible agent development
- **State Management**: Maintains user preferences for temperature units and default city

## About Google Agent Development Kit (ADK)

This project is built using [Google's Agent Development Kit](https://google.github.io/adk-docs), an open-source AI agent framework integrated with Gemini and Google services. ADK is designed for:

- **Developing and deploying AI agents** with tight integration to the Google ecosystem
- **Building simple to complex agents** powered by Gemini models
- **Flexible orchestration** through workflow agents (Sequential, Parallel, Loop)
- **Multi-agent architecture** for modular and scalable applications
- **Rich tool ecosystem** with pre-built tools, custom functions, and third-party integrations
- **Deployment options** including local testing, Vertex AI Agent Engine, or Cloud Run

## How ADK Works in This Project

This project leverages several key ADK components:

1. **LLM Agent**: The core component that uses Gemini to understand natural language, make decisions, and generate responses
2. **Function Tools**: Custom Python functions (`get_weather` and `get_current_time`) that are exposed to the agent to extend its capabilities
3. **Structured Returns**: Function tools return dictionaries with status and result information to help the LLM understand the outcomes

The agent processes user queries about weather and time, identifies the city mentioned, and routes the request to the appropriate function tool. The results are then formatted into natural language responses.

## Prerequisites

- Docker and Docker Compose
- OpenWeatherMap API key
- Google AI Gemini API key

## Quick Start with Docker

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd google_agents
   ```

2. Set up your environment variables:
   - Create a `.env` file in the `multi_tool_agent` directory
   - Add your API keys:
     ```
     GOOGLE_GENAI_USE_VERTEXAI="False"
     GOOGLE_API_KEY="your-google-api-key"
     OPENWEATHERMAP_API_KEY="your-openweathermap-api-key"
     ```

3. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:8001
   ```

## Manual Installation

If you prefer to run without Docker:

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python agent_server.py
   ```

## Usage

The chat interface allows you to:

- Ask about current weather: "What's the weather like in Paris?"
- Get weather forecasts: "What's the forecast for London for the next 3 days?"
- Check current time: "What time is it in Tokyo?"
- Use default city: "What's the weather like?" (uses your preferred city)
- Send greetings and get responses

The agent will:
- Maintain your preferences across the session
- Provide formatted, easy-to-read responses
- Handle multiple types of queries intelligently
- Give accurate weather and time information

## Project Structure

```
google_agents/
├── multi_tool_agent/        # Main agent implementation
│   ├── agent.py            # Core agent implementation
│   ├── __init__.py         # Package initialization
│   └── .env                # Environment variables
├── templates/              # Web interface
│   └── index.html         # Chat interface
├── agent_server.py        # FastAPI server
├── requirements.txt       # Project dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── .dockerignore        # Docker build exclusions
```

## API Endpoints

- `GET /`: Serves the chat interface
- `POST /chat/`: Processes chat messages and returns agent responses

## Environment Variables

Required environment variables in `.env`:
- `GOOGLE_API_KEY`: Your Google AI API key
- `OPENWEATHERMAP_API_KEY`: Your OpenWeatherMap API key
- `GOOGLE_GENAI_USE_VERTEXAI`: Set to "False" for direct API usage

## Contributing

[Add contribution guidelines]

## License

[Specify license information]

## Acknowledgments

- OpenWeatherMap API for weather data
- Google AI for the Gemini model
- Google Agent Development Kit (ADK) for the agent framework

