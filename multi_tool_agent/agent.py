import datetime
import requests
import os
from dotenv import load_dotenv
import json
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import asyncio
from google.genai import types
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from typing import Optional, Dict, Any
from google.adk.tools.base_tool import BaseTool

load_dotenv()



""" TOOLS """

def get_weather_stateful(city: str, tool_context: ToolContext) -> dict:
    """Retrieves the current weather report for a specified city, using temperature units from session state.

    Args:
        city (str): The name of the city for which to retrieve the weather report.
        tool_context (ToolContext): Context object providing access to session state.

    Returns:
        dict: status and result or error msg.
    """
    try:
        print(f"--- Tool: get_weather_stateful called for city='{city}' ---")
        
        # Get API key from environment variable (more secure)
        api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        
        # Read preferred temperature unit from state
        preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius") # Default to Celsius
        preferred_city = tool_context.state.get("user_preference_city", "Tunis") # Default city preference
        

        
        # First, get city ID by city name
        # If no city is specified and we're not checking the preferred city, use the preferred city
        original_city = city
        if not city or city.lower() == "default" or city.lower() == "preferred":
            city = preferred_city
            print(f"--- Tool: Using preferred city: '{city}' (was '{original_city}') ---")
        else:
            print(f"--- Tool: Using specified city: '{city}' ---")
            
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()
        
        if not geo_data:
            error_msg = f"City '{city}' not found."
            print(f"--- Tool: {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
            
        # Extract location data
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
            
        # Make API request to OpenWeatherMap forecast endpoint
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(forecast_url)
        data = response.json()
        
        # Check if API request was successful
        if response.status_code == 200:
            # Extract current forecast (first item in the list)
            current_forecast = data["list"][0]
            weather_description = current_forecast["weather"][0]["description"]
            temp_celsius = current_forecast["main"]["temp"]
            
            # Get city name from the response (may be more accurate than user input)
            city_name = data["city"]["name"]
            
            # Format temperature based on user preference in state
            if preferred_unit == "Fahrenheit":
                temp_value = (temp_celsius * 9/5) + 32
                temp_unit = "°F"
            else:  # Default to Celsius
                temp_value = temp_celsius
                temp_unit = "°C"
            
            report = f"The current weather in {city_name} is {weather_description} with a temperature of {temp_value:.1f}{temp_unit}."
            result = {"status": "success", "report": report}
            
            # Write back to state that we checked this city
            tool_context.state["last_city_checked"] = city_name
            print(f"--- Tool: Updated state 'last_city_checked': {city_name} ---")
            print(f"--- Tool: Generated report in {preferred_unit}. Result: {result} ---")
            
            return result
        else:
            error_msg = f"Weather information for '{city}' is not available. API error: {data.get('message', 'Unknown error')}"
            print(f"--- Tool: API error: {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg,
            }
    except Exception as e:
        error_msg = f"Error retrieving weather for '{city}': {str(e)}"
        print(f"--- Tool: Exception: {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
        }

def get_weather_forecast(city: str, tool_context: ToolContext, days: int = 3) -> dict:
    """Retrieves weather forecast for a specified city for upcoming days.

    Args:
        city (str): The name of the city for which to retrieve the weather forecast.
        tool_context (ToolContext): Context object providing access to session state.
        days (int, optional): Number of days to forecast (1-5). Defaults to 3.

    Returns:
        dict: status and forecast information or error message.
    """
    try:
        print(f"--- Tool: get_weather_forecast called for city='{city}', days={days} ---")
        
        # Get API key from environment variable
        api_key = os.environ.get("OPENWEATHERMAP_API_KEY")

        # Read preferred temperature unit from state
        preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius") # Default to Celsius
        preferred_city = tool_context.state.get("user_preference_city", "Tunis") # Default city preference
        
        # Check if we should use the preferred city
        original_city = city
        if not city or city.lower() == "default" or city.lower() == "preferred":
            city = preferred_city
            print(f"--- Tool: Using preferred city: '{city}' (was '{original_city}') ---")
        else:
            print(f"--- Tool: Using specified city: '{city}' ---")
        
        # Validate days parameter
        days = max(1, min(5, days))  # Ensure days is between 1 and 5
        
        # First, get city coordinates by city name
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()
        
        if not geo_data:
            error_msg = f"City '{city}' not found."
            print(f"--- Tool: {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg
            }
            
        # Extract location data
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        city_name = geo_data[0].get("name", city)
            
        # Make API request to OpenWeatherMap forecast endpoint
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(forecast_url)
        data = response.json()
        
        # Check if API request was successful
        if response.status_code == 200:
            # Extract forecast information
            forecast_list = data["list"]
            
            # OpenWeatherMap provides forecast in 3-hour intervals
            # We'll group by day and pick the mid-day forecast for each day
            
            # Get current date and initialize variables
            forecast_days = {}
            current_date = datetime.datetime.now().date()
            
            # Group forecasts by day
            for forecast in forecast_list:
                # Convert timestamp to datetime
                timestamp = forecast["dt"]
                forecast_date = datetime.datetime.fromtimestamp(timestamp).date()
                forecast_hour = datetime.datetime.fromtimestamp(timestamp).hour
                
                # Skip current day and focus on future days
                if forecast_date <= current_date:
                    continue
                
                # Initialize day entry if not exists
                if forecast_date not in forecast_days:
                    forecast_days[forecast_date] = []
                
                # Add this forecast to the day's list
                forecast_temp = forecast["main"]["temp"]
                forecast_weather = forecast["weather"][0]["description"]
                forecast_days[forecast_date].append({
                    "hour": forecast_hour,
                    "temp": forecast_temp,
                    "weather": forecast_weather
                })
            
            # Sort dates and limit to requested number of days
            sorted_dates = sorted(forecast_days.keys())[:days]
            
            # Format the forecast results
            daily_forecasts = []
            for date in sorted_dates:
                # Get forecasts for this day
                day_forecasts = forecast_days[date]
                
                # Try to get mid-day forecast (around noon) or average if not available
                midday_forecast = None
                for fc in day_forecasts:
                    if 10 <= fc["hour"] <= 14:
                        midday_forecast = fc
                        break
                
                # If no midday forecast, use the first one
                if not midday_forecast and day_forecasts:
                    midday_forecast = day_forecasts[0]
                
                if midday_forecast:
                    # Format date
                    date_str = date.strftime("%A, %B %d")  # e.g., "Monday, July 10"
                    
                    # Add to results
                    daily_forecasts.append({
                        "date": date_str,
                        "temperature": f"{midday_forecast['temp']:.1f}°C",
                        "weather": midday_forecast["weather"]
                    })
            
            # Prepare the final report
            if daily_forecasts:
                forecast_report = f"Weather forecast for {city_name} for the next {len(daily_forecasts)} days:\n\n"
                for fc in daily_forecasts:
                    forecast_report += f"• {fc['date']}: {fc['weather']} with temperature around {fc['temperature']}\n"
                
                return {
                    "status": "success",
                    "report": forecast_report,
                    "daily_forecasts": daily_forecasts
                }
            else:
                return {
                    "status": "error",
                    "error_message": f"No forecast data available for upcoming days in {city_name}."
                }
        else:
            error_msg = f"Weather forecast for '{city}' is not available. API error: {data.get('message', 'Unknown error')}"
            print(f"--- Tool: API error: {error_msg} ---")
            return {
                "status": "error",
                "error_message": error_msg,
            }
    except Exception as e:
        error_msg = f"Error retrieving forecast for '{city}': {str(e)}"
        print(f"--- Tool: Exception: {error_msg} ---")
        return {
            "status": "error",
            "error_message": error_msg,
        }


def get_current_time(city: str, tool_context: ToolContext) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.
        tool_context (ToolContext): Context object providing access to session state.

    Returns:
        dict: status and result or error msg.
    """
    preferred_city = tool_context.state.get("user_preference_city", "Tunis") # Default city preference
    
    # Check if we should use the preferred city
    original_city = city
    if not city or city.lower() == "default" or city.lower() == "preferred":
        city = preferred_city
        print(f"--- Tool: Using preferred city for time: '{city}' (was '{original_city}') ---")
    else:
        print(f"--- Tool: Using specified city for time: '{city}' ---")
    
    # Dictionary mapping cities to their timezone identifiers
    city_to_timezone = {
        "new york": "America/New_York",
        "san francisco": "America/Los_Angeles",
        "los angeles": "America/Los_Angeles",
        "chicago": "America/Chicago",
        "houston": "America/Chicago",
        "phoenix": "America/Phoenix",
        "philadelphia": "America/New_York",
        "san antonio": "America/Chicago",
        "san diego": "America/Los_Angeles",
        "dallas": "America/Chicago",
        "san jose": "America/Los_Angeles",
        "austin": "America/Chicago",
        "london": "Europe/London",
        "paris": "Europe/Paris",
        "berlin": "Europe/Berlin",
        "rome": "Europe/Rome",
        "madrid": "Europe/Madrid",
        "amsterdam": "Europe/Amsterdam",
        "brussels": "Europe/Brussels",
        "vienna": "Europe/Vienna",
        "tokyo": "Asia/Tokyo",
        "beijing": "Asia/Shanghai",
        "shanghai": "Asia/Shanghai",
        "hong kong": "Asia/Hong_Kong",
        "singapore": "Asia/Singapore",
        "sydney": "Australia/Sydney",
        "melbourne": "Australia/Melbourne",
        "auckland": "Pacific/Auckland",
        "toronto": "America/Toronto",
        "vancouver": "America/Vancouver",
        "montreal": "America/Montreal",
        "mexico city": "America/Mexico_City",
        "sao paulo": "America/Sao_Paulo",
        "rio de janeiro": "America/Sao_Paulo",
        "buenos aires": "America/Argentina/Buenos_Aires",
        "lagos": "Africa/Lagos",
        "cairo": "Africa/Cairo",
        "johannesburg": "Africa/Johannesburg",
        "nairobi": "Africa/Nairobi",
        "dubai": "Asia/Dubai",
        "new delhi": "Asia/Kolkata",
        "mumbai": "Asia/Kolkata",
        "bangkok": "Asia/Bangkok",
        "jakarta": "Asia/Jakarta",
        "istanbul": "Europe/Istanbul",
        "seoul": "Asia/Seoul",
        "Tunis": "Africa/Tunis",
        "monastir": "Africa/Tunis",
        "Beb El Jazira": "Africa/Tunis",
        "Abu Dhabi": "Asia/Dubai",
        "Abuja": "Africa/Lagos",
        "Accra": "Africa/Accra",
        "Addis Ababa": "Africa/Addis_Ababa",
        "Algiers": "Africa/Algiers",
        
    }

    city_lower = city.lower()
    
    # If we're using the preferred city, prioritize exact match first
    if city == preferred_city:
        # Direct lookup for preferred city with exact case match
        if city in city_to_timezone:
            tz_identifier = city_to_timezone[city]
            print(f"--- Tool: Direct match for preferred city: '{city}' ---")
            exact_match = city
        else:
            # Try case insensitive match for preferred city
            for city_name in city_to_timezone.keys():
                if city_name.lower() == city_lower:
                    tz_identifier = city_to_timezone[city_name]
                    exact_match = city_name
                    print(f"--- Tool: Case-insensitive match for preferred city: '{city}' → '{city_name}' ---")
                    break
            else:
                exact_match = None
    else:
        # First check for exact match (case-insensitive)
        exact_match = None
        for city_name, tz in city_to_timezone.items():
            if city_name.lower() == city_lower:
                exact_match = city_name
                tz_identifier = tz
                break
    
    if exact_match:
        city = exact_match  # Use the exact matched city name
    else:
        # Try to find a partial match
        matches = [c for c in city_to_timezone.keys() if city_lower in c.lower() or c.lower() in city_lower]
        if matches:
            # Use the first match if any
            tz_identifier = city_to_timezone[matches[0]]
            city = matches[0]  # Use the matched city name as is
        else:
            return {
                "status": "error",
                "error_message": (
                    f"Sorry, I don't have timezone information for {city}. Try a major city."
                ),
            }

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city.title()} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )
        return {"status": "success", "report": report}
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving time for '{city}': {str(e)}",
        }

def say_hello(name: str = "There") -> str:
    """Provides a simple greeting, optionally addressing the user by name.

    Args:
        name (str, optional): The name of the person to greet. Defaults to "there".

    Returns:
        str: A friendly greeting message.
    """
    return f"Hello, {name}!"

def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    return "Goodbye! Have a great day."


""" AGENTS """

greeting_agent = Agent(
    name="greeting_agent",
    model=os.environ.get("MODEL_GEMINI_2_0_FLASH"),
    description=("Handles simple greetings and hellos using the 'say_hello' tool."), 
    instruction=(
        "You are the Greeting Agent. Your ONLY task is to provide a friendly greeting to the user. "
        "Use the 'say_hello' tool to generate the greeting. "
        "If the user provides their name, make sure to pass it to the tool. "
        "Do not engage in any other conversation or tasks."
    ),
    tools=[say_hello],
)

time_agent = Agent(
    name="time_agent",
    model=os.environ.get("MODEL_GEMINI_2_0_FLASH"),
    description="Provides current time information for cities around the world.",
    instruction="""You are the Time Agent. Your primary responsibility is to provide accurate current time information.
                Use the 'get_current_time' tool to fetch the current time for specific cities.
                The tool will format the time based on user preference stored in state.
                
                When a user asks about the current time or what time it is in a city, extract the city name and use the tool.
                
                IMPORTANT: If the user doesn't specify a city, or asks for the "default" city time,
                pass an empty string or "default" as the city parameter, and the system will use their
                preferred city from state (initially set to Tunis).
                
                Respond in a helpful, conversational manner focusing on the time information.
                If the time couldn't be retrieved for a specific city, explain the issue clearly and suggest using a major city nearby.
                
                Example queries you can handle:
                - "What time is it in Tokyo?"
                - "Tell me the current time in Paris"
                - "What's the time in New York right now?"
                - "What time is it right now?" (use default city)
                """,
    tools=[get_current_time],
)

forecast_agent = Agent(
    name="forecast_agent",
    model=os.environ.get("MODEL_GEMINI_2_0_FLASH"),
    description="Provides weather forecasts for upcoming days using OpenWeatherMap API.",
    instruction="""You are the Weather Forecast Agent. Your primary responsibility is to provide weather forecasts for the upcoming days.
                Use the 'get_weather_forecast' tool to fetch forecast data for specific cities.
                The tool will format the temperature based on user preference stored in state.
                The tool will format the default city based on user preference stored in state.
                
                When a user asks about weather predictions or forecasts for a city, extract the city name and use the tool.
                By default, provide a 3-day forecast, but if the user specifically asks for a different number of days (1-5),
                adjust accordingly.
                
                IMPORTANT: If the user doesn't specify a city, or asks for the "default" city forecast,
                pass an empty string or "default" as the city parameter, and the system will use their
                preferred city from state (initially set to Tunis).
                
                Respond in a helpful, conversational manner focusing on the forecast information.
                If the forecast couldn't be retrieved, explain the issue clearly and suggest alternatives.
                
                Example queries you can handle:
                - "What's the weather forecast for Paris?"
                - "How will the weather be in Tokyo for the next 5 days?"
                - "Will it rain in New York tomorrow?"
                - "What's the forecast for the next few days?" (use default city)
                """,
    tools=[get_weather_forecast],
)

farewell_agent = Agent(
    # Can use the same or a different model
    model=os.environ.get("MODEL_GEMINI_2_0_FLASH"), # Using Gemini model directly
    name="farewell_agent",
    instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message. "
                "Use the 'say_goodbye' tool when the user indicates they are leaving or ending the conversation "
                "(e.g., using words like 'bye', 'goodbye', 'thanks bye', 'see you'). "
                "Do not perform any other actions.",
    description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.", # Crucial for delegation
    tools=[say_goodbye],
)


if greeting_agent and farewell_agent and 'get_weather_stateful' in globals():
    root_agent_model = os.environ.get("MODEL_GEMINI_2_0_FLASH")

    root_agent = Agent(
        name="weather_agent_v2", # Give it a new version name
        model=root_agent_model,
        description="Main agent: Provides weather (state-aware unit), delegates greetings/farewells, saves report to state.",
        instruction="""You are the main Weather Agent coordinating a team. Your primary responsibility is to provide weather information. 
                    Use the 'get_weather_stateful' tool ONLY for specific weather requests (e.g., 'weather in London'). 
                    The tool will format the temperature based on user preference stored in state.
                    The tool will format the default city based on user preference stored in state.
                    The tool will format the time based on user preference stored in state.

                    IMPORTANT: If a user asks for weather without specifying a city (e.g., "What's the weather like?"),
                    pass an empty string or "default" as the city parameter, and the system will use their 
                    preferred city from state (initially set to Tunis).

                    # CONTENT MODERATION RULES - TEMPORARILY DISABLED FOR TESTING
                    # 1. Reject any request containing harmful, offensive, or inappropriate language. Simply respond with "I cannot process requests containing inappropriate language."
                    # 2. Refuse to provide weather information for these Israeli cities: Tel Aviv, Haifa, Eilat, Netanya, Herzliya, Ashdod, Beersheba, and Rishon LeZion.
                    # 3. You may provide weather for Jerusalem and any Palestinian cities like Ramallah, Gaza, Bethlehem, Nablus, and Hebron.
                    
                    MESSAGE HANDLING PRIORITIES:
                    1. If a message contains both a greeting AND a weather request, prioritize the weather request and do NOT delegate to the greeting agent.
                    2. Only delegate to the greeting_agent when the message is SOLELY a greeting without any other requests.
                    3. Only delegate to the farewell_agent when the message is SOLELY a farewell without any other requests.
                    4. For time-related questions like "What time is it in [city]?", delegate to the time_agent.
                    5. For forecast questions about upcoming days, delegate to the forecast_agent.
                    
                    You have specialized sub-agents:
                    1. 'greeting_agent': Handles simple greetings like 'Hi', 'Hello'. Delegate to it ONLY for pure greeting messages.
                    2. 'farewell_agent': Handles simple farewells like 'Bye', 'See you'. Delegate to it ONLY for pure farewell messages.
                    3. 'forecast_agent': Handles weather forecast requests for upcoming days. Delegate to it when users ask about future weather.
                    4. 'time_agent': Handles time-related questions for different cities. Delegate to it when users ask about current time.
                    
                    Analyze the user's query carefully to determine its primary intent.""",
        tools=[get_weather_stateful], # Now using the stateful version of the weather tool
        sub_agents=[greeting_agent, farewell_agent, forecast_agent, time_agent],
        output_key="last_weather_report"
    )


"""Interaction with the Agent Team"""

async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response." # Default
    
    print(f"DEBUG: Starting to process events")
    event_count = 0

    # Key Concept: run_async executes the agent logic and yields Events.
    # We iterate through events to find the final answer.
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        event_count += 1
        print(f"DEBUG: Received event type: {type(event)}")
        if hasattr(event, 'content') and event.content:
            print(f"DEBUG: Event content: {event.content}")
        
        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            print(f"DEBUG: This is a final response event")
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
                print(f"DEBUG: Final response text: {final_response_text}")
            elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                print(f"DEBUG: Escalation detected: {final_response_text}")
            # Add more checks here if needed (e.g., specific error codes)
            break # Stop processing events once the final response is found
    
    print(f"DEBUG: Processed {event_count} events total")
    print(f"<<< Agent Response: {final_response_text}")

if 'root_agent' in globals() and root_agent:
    async def run_stateful_conversation():
        print("\n--- Testing Agent Team Delegation ---")
        # InMemorySessionService is simple, non-persistent storage for this tutorial.
        session_service_stateful = InMemorySessionService()

        # Define constants for identifying the interaction context
        APP_NAME = "weather_tutorial_agent_team"
        USER_ID_STATEFUL = "user_1_agent_team"
        SESSION_ID_STATEFUL = "session_001_agent_team" # Using a fixed ID for simplicity
        
        initial_state = {
            "user_preference_temperature_unit": "Celsius",
            "user_preference_city": "Tunis"
        }

        # Create the specific session where the conversation will happen
        session_stateful = session_service_stateful.create_session(
            app_name=APP_NAME,
            user_id=USER_ID_STATEFUL,
            session_id=SESSION_ID_STATEFUL,
            state=initial_state
        )
        print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")

        # --- Get the actual root agent object ---
        # Check for both possible variable names
        root_agent_var_name = 'root_agent' # Default name from Step 3 guide
        if 'root_agent' in globals(): # Check if user used this name instead
            root_agent_var_name = 'root_agent'
        
        actual_root_agent = globals()[root_agent_var_name]

        # Create a runner specific to this agent team test
        runner_root_stateful = Runner(
            agent=actual_root_agent, # Use the root agent object
            app_name=APP_NAME,       # Use the specific app name
            session_service=session_service_stateful # Use the stateful session service
            )
        # Corrected print statement to show the actual root agent's name
        print(f"Runner created for agent '{actual_root_agent.name}'.")




# Add a proper execution block to run the async function
if __name__ == "__main__":
    asyncio.run(run_stateful_conversation())








    

