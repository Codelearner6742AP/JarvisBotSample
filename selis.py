import speech_recognition as sr  # For voice recognition
import webbrowser  # For opening web pages
import pyttsx3  # For text-to-speech conversion
import requests  # For making HTTP requests
import time  # For time-related functions
from openai import OpenAI
import json  # Add this line to import the json module

# Load your configuration
with open('config.json') as config_file:  # Ensure you have a config.json file
    config = json.load(config_file)

client = OpenAI(api_key=config['openai_key'])  # For interacting with OpenAI's API
from openai import OpenAIError, RateLimitError  # Error handling for OpenAI
import json  # For handling JSON data
import asyncio  # For asynchronous programming
from datetime import datetime, timedelta  # For date and time manipulation
import random  # For generating random jokes and quotes
import smtplib  # For sending emails
from email.mime.text import MIMEText  # For creating email messages
import logging  # For logging
import concurrent.futures  # For threading
import re  # For parsing email commands
import dateparser  # For natural language date parsing
from googleapiclient.discovery import build  # For Google Calendar API
from google.oauth2.credentials import Credentials  # For Google OAuth2
import pvporcupine
import pyaudio
from pvrecorder import PvRecorder


# Load API keys from configuration
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        newsapi = config['newsapi_key']
        email_user = config['email_user']
        email_password = config['email_password']
except FileNotFoundError:
    logging.error("Configuration file 'config.json' not found!")
    exit(1)
except KeyError as e:
    logging.error(f"Missing key in config file: {e}")
    exit(1)
except json.JSONDecodeError:
    logging.error("Error decoding 'config.json'. Please check its format.")
    exit(1)


# Initialize logging
logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

# Initialize speech recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init(driverName='nsss')

# Cache to store results like news and common responses
cache = {}
cache_expiration = timedelta(minutes=10)  # Cache expiration time
conversation_history = [
    {"role": "system", "content": "You are a helpful assistant named Robin."},
]

# Global variable for reminders
reminders = []

# Function to fetch a random joke
def fetch_joke():
    jokes = [
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "I told my computer I needed a break, and now it won't stop sending me KitKat ads.",
        "Why don't scientists trust atoms? Because they make up everything!"
    ]
    return random.choice(jokes)  # Return a random joke

# Function to set a reminder with natural language parsing
def set_reminder(time_str, message):
    reminder_time = dateparser.parse(time_str)  # Parse natural language time
    if reminder_time:
        reminders.append({"time": reminder_time, "message": message})  # Add reminder to list
        speak(f"Reminder set for {reminder_time.strftime('%H:%M on %B %d, %Y')}.")  # Confirm reminder
    else:
        speak("Sorry, I could not understand the time.")  # Handle parse error

# Function to check and trigger reminders
def check_reminders():
    now = datetime.now()  # Get current time
    for reminder in reminders:
        if now >= reminder["time"]:
            speak(reminder["message"])  # Speak the reminder message
            reminders.remove(reminder)  # Remove the reminder after speaking

# Function to send an email
def send_email(to, subject, body):
    try:
        msg = MIMEText(body)  # Create email message
        msg['Subject'] = subject  # Set email subject
        msg['From'] = config['email_user']  # Set sender email
        msg['To'] = to  # Set recipient email

        # Connect to SMTP server and send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Start TLS for security
            server.login(config['email_user'], config['email_password'])  # Log in to email
            server.send_message(msg)  # Send the email
        speak("Email sent successfully.")  # Confirm email sent
    except Exception as e:
        speak(f"Failed to send email: {e}")  # Handle errors

# Function to convert text to speech
def speak(text):
    engine.say(text)  # Queue the text to be spoken
    engine.runAndWait()  # Wait until speaking is finished

# Asynchronous function to fetch weather data
async def fetch_weather(city_name):
    try:
        # Ensure the OpenWeather API key is loaded from the config
        api_key = config.get('openweather_api_key')
        if not api_key:
            speak("OpenWeather API key not found in configuration.")
            return
        
        # Construct the OpenWeather API URL
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
        
        # Make the API request asynchronously
        response = await asyncio.to_thread(requests.get, base_url)
        
        # Parse the JSON response
        data = response.json()
        
        # Check if the city was found (API status code 200 means success)
        if data.get("cod") == 200:
            main = data["main"]
            weather = data["weather"][0]
            temperature = main["temp"]
            description = weather["description"]
            weather_report = f"The temperature in {city_name.capitalize()} is {temperature}°C with {description}."
            speak(weather_report)
        else:
            # If city not found or other error, speak the error
            message = data.get("message", "Unknown error")
            speak(f"Could not find weather data for {city_name.capitalize()}. Error: {message}")
    
    except requests.exceptions.RequestException as e:
        speak(f"Network error occurred: {e}")

# Asynchronous function to fetch news headlines
async def fetch_news():
    try:
        # Ensure the NewsAPI key is loaded from the config
        api_key = config.get('newsapi_key')
        if not api_key:
            speak("NewsAPI key not found in configuration.")
            return []

        # Fetch the top headlines for a specific country (e.g., India)
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={api_key}")
        
        # Parse the JSON response
        data = r.json()
        
        # Check for success and extract articles
        if data.get("status") == "ok":
            articles = data.get("articles", [])
            if not articles:
                speak("No news articles found.")
                return []

            # Extract the headlines from the articles
            headlines = [article["title"] for article in articles if article.get("title")]
            
            # Cache the headlines with an expiration time
            cache["news"] = {
                "data": headlines,
                "expires": datetime.now() + cache_expiration
            }

            return headlines  # Return the headlines
        else:
            speak(f"Failed to fetch news. Reason: {data.get('message', 'Unknown error')}")
            return []
    
    except requests.exceptions.RequestException as e:
        speak(f"Error occurred while fetching news: {e}")
        return []


# Function to process AI commands
def ai_process(command):
    if command in cache:
        return cache[command]  # Return cached response if available

    def create_completion():
        try:
            response = client.chat.completions.create(model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": command},
                # Add previous messages if needed
            ],
            max_tokens=100)
            return response.choices[0].message.content  # Return AI response
        except RateLimitError as e:
            logging.warning(f"Rate limit exceeded: {e}")
            time.sleep(60)  # Wait before retrying
            return create_completion()  # Retry completion
        except OpenAIError as e:
            logging.error(f"An error occurred: {e}")
            return "An error occurred while processing your request."  # Handle errors

    conversation_history.append({"role": "user", "content": command})  # Log user command
    response = create_completion()  # Get AI response
    conversation_history.append({"role": "assistant", "content": response})  # Log AI response

    cache[command] = response  # Cache the response
    return response  # Return AI response

# Function to process user commands
def process_command(c):
    logging.info(f"Command: {c}")  # Log the command
    if "open google" in c.lower():
        webbrowser.open("https://google.com")  # Open Google
        speak("Opening Google.")
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")  # Open YouTube
        speak("Opening YouTube.")
    elif "open stackoverflow" in c.lower():
        webbrowser.open("https://stackoverflow.com")  # Open Stack Overflow
        speak("Opening Stack Overflow.")
    elif "open github" in c.lower():
        webbrowser.open("https://github.com")  # Open GitHub
        speak("Opening GitHub.")
    elif "news" in c.lower():
        asyncio.run(fetch_news_and_speak())  # Fetch and speak news
    elif "weather" in c.lower():
        city = " ".join(c.lower().split(" ")[1:])  # Extract city name
        asyncio.run(fetch_weather(city))  # Fetch and speak weather
    elif "set reminder" in c.lower():
        parts = c.lower().split(" ")
        time_str = parts[-2]  # Assuming time is the second last word
        message = " ".join(parts[:-2])  # The rest is the message
        set_reminder(time_str, message)  # Set reminder
    elif "tell me a joke" in c.lower():
        joke = fetch_joke()  # Fetch a joke
        speak(joke)  # Speak the joke
    elif "send email" in c.lower():
        parse_email_command(c)  # Parse and send email command
    elif "daily briefing" in c.lower():
        asyncio.run(daily_briefing())  # Provide daily briefing
    else:
        output = ai_process(c)  # Process command with AI
        speak(output)  # Speak AI response

# Asynchronous function to fetch news and speak it
async def fetch_news_and_speak():
    headlines = await fetch_news()
    
    if headlines:
        speak("Here are the top headlines from India:")
        for headline in headlines[:5]:  # Speak only top 5 headlines
            speak(headline)
    else:
        speak("Sorry, no news headlines are available at the moment.")


# Daily Briefing Function
async def daily_briefing():
    speak("Good morning! Here's your daily briefing.")

    # Fetch weather for the default city
    await fetch_weather("Delhi")

    # Fetch top news headlines
    await fetch_news_and_speak()

    # Check reminders for the day
    today_reminders = [reminder for reminder in reminders if reminder['time'].date() == datetime.now().date()]
    if today_reminders:
        speak("You have the following reminders today:")
        for reminder in today_reminders:
            speak(f"{reminder['message']} at {reminder['time'].strftime('%H:%M')}.")
    else:
        speak("You have no reminders for today.")

# Function to listen for the wake word
def detect_wake_word():
    porcupine = None
    recorder = None
    try:
        porcupine = pvporcupine.create(
            access_key='yourownaccesskey',
            keyword_paths=['path']
        )

        recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
        recorder.start()

        print("Listening for the wake word 'Robin'...")

        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word 'Robin' detected!")
                return True

    except KeyboardInterrupt:
        print("Stopping wake word detection...")
    finally:
        if porcupine is not None:
            porcupine.delete()
        if recorder is not None:
            recorder.delete()

def listen_for_command():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening for command...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            print(f"Command recognized: {command}")
            return command
    except sr.UnknownValueError:
        print("Sorry, I did not understand the command.")
        return None
    except sr.RequestError as e:
        print(f"Request error: {e}")
        return None

def process_command(command):
    if command:
        # Your existing command processing logic here
        speak(f"You said: {command}")
        # Add more command processing as needed

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

if __name__ == "__main__":
    speak("Initializing Robin")
    while True:
        if detect_wake_word():
            speak("Yes, how can I assist you?")
            command = listen_for_command()
            process_command(command)