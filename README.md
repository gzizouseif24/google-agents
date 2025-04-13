# Weather and Time Agent

A Python-based agent that uses Google's Agent Development Kit (ADK) and Generative AI to answer questions about weather and time in different cities around the world.

## Features

- **Weather Information**: Get current weather conditions for cities worldwide using the OpenWeatherMap API
- **Time Lookup**: Check the current time in major cities across different time zones
- **Google AI Integration**: Powered by Gemini 2.0 Flash generative AI model
- **Built with ADK**: Uses Google's Agent Development Kit framework for flexible agent development

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

- Python 3.6+
- OpenWeatherMap API key
- Google AI Gemini API key
- Google ADK: `pip install google-adk`

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd google_agents
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - Create a `.env` file in the `multi_tool_agent` directory
   - Add your API keys:
     ```
     GOOGLE_GENAI_USE_VERTEXAI="False"
     GOOGLE_API_KEY="your-google-api-key"
     OPENWEATHERMAP_API_KEY="your-openweathermap-api-key"
     ```

## Usage

The agent contains two main function tools integrated with Google ADK:

1. `get_weather(city)`: Retrieves current weather information for a specified city
   - Returns structured dictionary with status and weather report 
   - Makes API calls to OpenWeatherMap to fetch real-time weather data

2. `get_current_time(city)`: Returns the current time in a specified city
   - Returns structured dictionary with status and time information
   - Uses Python's datetime and zoneinfo to calculate accurate local times

### Running the Agent

You can run the agent using one of these methods:

1. **Using the ADK Web Interface**:
   ```
   cd ..  # Navigate to parent directory
   adk web
   ```
   Then open http://localhost:8000 in your browser and select "multi_tool_agent"

2. **Using the Terminal**:
   ```
   cd ..  # Navigate to parent directory
   adk run multi_tool_agent
   ```

3. **As an API Server**:
   ```
   cd ..  # Navigate to parent directory
   adk api_server multi_tool_agent
   ```

### ADK Agent Implementation

This project uses the ADK's `Agent` class (an alias for `LlmAgent`) to create an agent with the following configuration:

```python
root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash-exp",
    description="Agent to answer questions about the time and weather in a city.",
    instruction="I can answer your questions about the time and weather in a city.",
    tools=[get_weather, get_current_time],
)
```

The configuration includes:
- **name**: A unique identifier for the agent
- **model**: The Gemini model used for natural language understanding
- **description**: A concise summary of the agent's capabilities
- **instruction**: Guidance for the LLM on how to respond to queries
- **tools**: The Python functions that extend the agent's capabilities

## Project Structure

```
google_agents/
├── multi_tool_agent/        # Main project directory
│   ├── agent.py             # Core agent implementation
│   ├── __init__.py          # Package initialization
│   └── .env                 # Environment variables (not in version control)
└── requirements.txt         # Project dependencies
```

## Learn More About ADK

For more information about Google's Agent Development Kit:
- [ADK Documentation](https://google.github.io/adk-docs)
- [Getting Started](https://google.github.io/adk-docs/get-started/quickstart/)
- [LLM Agents](https://google.github.io/adk-docs/agents/llm-agents/)
- [Function Tools](https://google.github.io/adk-docs/tools/function-tools/)
- [Sample Agents](https://google.github.io/adk-docs/get-started/sample-agents/)

## License

[Specify license information]

## Acknowledgments

- OpenWeatherMap API for weather data
- Google AI for the Gemini model
- Google Agent Development Kit (ADK) for the agent framework 

