# Robin - Virtual Assistant

## Overview
Robin is a Python-based virtual assistant that performs tasks such as web browsing, playing music, fetching the latest news, and providing weather updates. It can also handle custom commands via OpenAI's API, acting as an AI-powered assistant capable of general tasks similar to Alexa or Google Assistant.

## Features
- Voice-activated commands using "Jarvis" as the wake word.
- Integration with OpenAI's GPT-3.5 to handle general questions and tasks.
- Web browsing capabilities (Google, YouTube, GitHub, etc.).
- Music player integration using a custom `musicLibrary`.
- Fetches the latest news from India via NewsAPI.
- Provides weather updates for specified cities.
- Handles various errors and retry logic in case of API limits or other issues.

## Dependencies
Install the following Python libraries:
```bash
pip install SpeechRecognition pyttsx3 requests openai
```

Additional setup may be needed:
- `SpeechRecognition`: Requires installing PortAudio for microphone input.
- `pyttsx3`: Text-to-speech engine.
- `openai`: Interacts with OpenAI's API.
- `musicLibrary`: Custom Python module (ensure it's present).
- NewsAPI: Requires an API key for fetching the news.

## How to Run
1. Install the necessary dependencies.
2. Set up API keys for OpenAI, OpenWeather, and NewsAPI.
3. Run the script:
    ```bash
    python selis.py
    ```
4. Speak the wake word "Jarvis" followed by your command, e.g., "open Google" or "play [song name]".

## Configuration
The application requires API keys to function. Ensure the following:
- OpenAI API Key is set correctly in the `openai.api_key` variable.
- NewsAPI Key is set in the `newsapi` variable.
- OpenWeather API Key should be placed in the `get_weather()` function.

## Error Handling
- Implements error handling for OpenAI's rate limit and other API errors.
- Handles speech recognition errors and retries commands.

---

### config.json

```json
{
  "openai_api_key": "your_openai_api_key",
  "newsapi_key": "your_newsapi_key",
  "openweather_api_key": "your_openweather_api_key",
  "wake_word": "jarvis",
  "speech_engine": "nsss",
  "default_country_news": "in",
  "default_temperature_units": "metric",
  "default_temperature_lang": "en"
   "email_user": "youremail",
   "email_password": "yourpassword"
}
```

- **openai_api_key**: Your OpenAI API key for GPT-3.5.
- **newsapi_key**: Your NewsAPI key to fetch news.
- **openweather_api_key**: Your OpenWeather API key for weather data.
- **wake_word**: The wake word to activate the assistant.
- **speech_engine**: The engine used for text-to-speech (TTS).
- **default_country_news**: Country code for fetching news (e.g., 'in' for India).
- **default_temperature_units**: Temperature units used by OpenWeather API (e.g., 'metric' for Celsius).
- **default_temperature_lang**: Language for temperature output.

