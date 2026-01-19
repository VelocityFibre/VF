# Weather Agent Specification - TEST

**Purpose**: Simple test agent for harness validation

## Purpose

Provide weather information for FibreFlow project planning. Help contractors and project managers check weather conditions for fiber installation work.

## Domain

**Type**: External Integration
**Specialization**: Weather API integration (OpenWeatherMap)
**External Service**: OpenWeatherMap API

## Capabilities

### 1. Get Current Weather

**What it does**: Fetch current weather conditions for a location
**When to use**: Check current conditions before scheduling work
**Tool**: `get_current_weather`

**Use Cases**:
- Check if it's safe to deploy fiber today
- Verify weather conditions before contractor dispatch
- Log weather at time of installation

### 2. Get Weather Forecast

**What it does**: Get 5-day weather forecast
**When to use**: Plan installation schedules for the week
**Tool**: `get_weather_forecast`

**Use Cases**:
- Plan fiber deployment schedule
- Schedule contractor availability
- Anticipate weather delays

### 3. Check Weather Alerts

**What it does**: Get weather warnings and alerts
**When to use**: Safety checks before outdoor work
**Tool**: `get_weather_alerts`

**Use Cases**:
- Safety alerts before fiber installation
- Storm warnings for equipment protection
- Planning around severe weather

## Tools

### Tool: `get_current_weather`

**Purpose**: Get current weather for location

**Parameters**:
- `location` (string, required): City name or coordinates (e.g., "London" or "51.5,-0.1")
- `units` (string, optional): "metric" or "imperial" (default: metric)

**Returns**:
```json
{
  "status": "success",
  "location": "London, GB",
  "temperature": 15,
  "feels_like": 13,
  "humidity": 72,
  "description": "partly cloudy",
  "wind_speed": 5.2,
  "units": "metric"
}
```

**Example**:
```python
result = agent.execute_tool("get_current_weather", {
    "location": "London",
    "units": "metric"
})
```

### Tool: `get_weather_forecast`

**Purpose**: Get 5-day forecast

**Parameters**:
- `location` (string, required): City name or coordinates
- `units` (string, optional): "metric" or "imperial" (default: metric)
- `days` (integer, optional): Number of days (1-5, default: 5)

**Returns**:
```json
{
  "status": "success",
  "location": "London, GB",
  "forecast": [
    {
      "date": "2025-12-05",
      "temp_high": 16,
      "temp_low": 12,
      "description": "light rain",
      "precipitation_chance": 60
    },
    ...
  ]
}
```

### Tool: `get_weather_alerts`

**Purpose**: Get active weather alerts

**Parameters**:
- `location` (string, required): City name or coordinates

**Returns**:
```json
{
  "status": "success",
  "location": "London, GB",
  "alerts": [
    {
      "event": "Wind Warning",
      "severity": "moderate",
      "description": "Strong winds expected",
      "start": "2025-12-05T10:00:00Z",
      "end": "2025-12-05T18:00:00Z"
    }
  ]
}
```

## Integration Requirements

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
OPENWEATHER_API_KEY=abc123...         # OpenWeatherMap API key

# Optional
WEATHER_DEFAULT_UNITS=metric          # Default unit system
WEATHER_CACHE_MINUTES=10              # Cache weather data
```

### External Dependencies

**Python Packages** (add to requirements.txt):
```
requests>=2.31.0
```

**API Access**:
- Sign up at https://openweathermap.org/api
- Free tier: 1000 calls/day
- No credit card required for testing

### Orchestrator Triggers

**Keywords**:
- weather
- forecast
- temperature
- rain
- conditions
- climate
- meteorology
- weather check

## Success Criteria

Agent is complete when:
- [x] All 3 tools implemented and working
- [x] API key authentication working
- [x] Error handling for invalid locations, API failures
- [x] Full test coverage (unit + integration with mock API)
- [x] README.md documentation
- [x] Registered in orchestrator/registry.json
- [x] Demo script functional
- [x] Environment variables documented
- [x] Follows BaseAgent pattern
- [x] Response caching implemented

## Architecture

```
User Query → Orchestrator → Weather Agent → OpenWeatherMap API
                                 ↓
                    [get_current, get_forecast, get_alerts]
                                 ↓
                    Cache layer (10 min TTL)
```

**Position in FibreFlow**:
- **Inherits from**: `shared/base_agent.py`
- **Registers in**: `orchestrator/registry.json`
- **Tests in**: `tests/test_weather.py`
- **Demo**: `demo_weather.py`

## Example Usage

### Via Orchestrator

```python
query = "What's the weather in London?"
# Orchestrator detects "weather" trigger
# Routes to WeatherAgent
# Returns: "Current weather in London: 15°C, partly cloudy..."
```

### Direct Usage

```python
from agents.weather.agent import WeatherAgent

agent = WeatherAgent(os.getenv('ANTHROPIC_API_KEY'))

# Check current weather
response = agent.chat("What's the weather in London?")
print(response)

# Get forecast
response = agent.chat("5-day forecast for Manchester")
print(response)

# Check alerts
response = agent.chat("Any weather alerts for Birmingham?")
print(response)
```

## Complexity Estimate

**Classification**: Simple Agent

**Features**:
- 3 simple tools
- Basic HTTP API calls
- Simple caching
- Standard error handling

**Estimated Metrics**:
- **Test Cases**: 25-30 features
- **Build Time**: 4-6 hours
- **Cost**: $3-5 (using Haiku)
- **LOC**: ~300-400 lines

**Breakdown**:
- Scaffolding: 5 features
- Base implementation: 5 features
- Tools: 12 features (3 tools × 4 features each)
- Testing: 8 features
- Documentation: 3 features
- Integration: 2 features

## Notes

### API Considerations

- **Rate Limits**: 1000 calls/day (free tier)
- **Caching**: Cache responses for 10 minutes to reduce API calls
- **Error Handling**: Handle invalid locations, API downtime, rate limit exceeded

### Testing Strategy

**Unit Tests**:
- Mock OpenWeatherMap API responses
- Test each tool with valid/invalid inputs
- Test error handling paths

**Integration Tests**:
- Use real API with test locations
- Verify response formats
- Test caching behavior

### Security

- Never log API keys
- Validate location inputs (prevent injection)
- Use HTTPS for all API calls

### Performance

- Implement response caching (10-minute TTL)
- Async API calls if checking multiple locations
- Timeout requests after 5 seconds
