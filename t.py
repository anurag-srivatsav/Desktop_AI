from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import requests
import json
from datetime import datetime, timedelta
import time as time_module
from datetime import time as dt_time
import pickle
import os
from PyQt5.QtWidgets import QSystemTrayIcon, QTabWidget, QStyleFactory
from PyQt5.QtCore import Qt
from win10toast import ToastNotifier
import threading
from playwright.sync_api import sync_playwright
import re
import speech_recognition as sr
import pyttsx3
import queue
import time
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Initialize Groq API
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Define theme colors
DARK_PURPLE = "#2D1B69"
LIGHT_PURPLE = "#6B4EE6"
ACCENT_PURPLE = "#8B6FFF"
TEXT_COLOR = "#FFFFFF"
SECONDARY_BG = "#1E1246"

class CustomQLineEdit(QtWidgets.QLineEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1E1246;
                border: 2px solid #6B4EE6;
                border-radius: 15px;
                padding: 8px 15px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #8B6FFF;
            }
        """)

class CustomQTextBrowser(QtWidgets.QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 15px;
                color: white;
                font-size: 14px;
            }
        """)
        
        self.setHtml("""
            <style>
                .message-container {
                    margin: 0px;
                    width: 100%;
                    display: block;
                    clear: both;
                }
                .user-message-container, .ai-message-container {
                    margin: 0px;
                    padding: 4px 15px;
                }
                .user-message{
                    color: skyblue;
                    padding: 4px 0px;
                    margin: 0;
                    max-width: 100%;
                    text-align: right;
                }
                
                .ai-message {
                    color: white;
                    padding: 4px 0px;
                    margin: 0;
                    max-width: 100%;
                    text-align: left;
                }
                .message-spacer {
                    height: 24px;
                    width: 100%;
                    display: block;
                }
            </style>
        """)
        
    def append_message(self, text, is_user=False):
        if is_user:
            html = f'''
                <div class="message-spacer"></div>
                <div class="user-message-container">
                    <div class="user-message">
                        <div style="font-size: 18px; font-weight: bold; color: skyblue;">Anurag:</div>
                        <div style="color: white;">{text}</div>
                    </div>
                </div>
                <br>
            '''
        else:
            html = f'''
                <div class="message-spacer"></div>
                <div class="ai-message-container">
                    <div class="ai-message">
                        <div style="font-size: 18px; font-weight: bold; color: white;">Personal Assistant:</div>
                        <div style="color: white;">{text}\n\n</div>
                    </div>
                </div>
                <br>
            '''
        
        # Append the HTML
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.setTextCursor(cursor)
        self.insertHtml(html)
        
        # Scroll to the bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class UserProfile:
    def __init__(self):
        self.name = ""
        self.occupation = ""  # student or professional
        self.wake_up_time = dt_time(7, 0)  # default 7 AM
        self.breakfast_time = dt_time(8, 0)
        self.lunch_time = dt_time(13, 0)
        self.dinner_time = dt_time(19, 0)
        self.bedtime = dt_time(22, 0)
        self.living_situation = ""  # alone or with family/friends
        self.daily_routines = []
        self.locations = []
        self.reminders = []
        self.calendar_events = []
        self.chat_history = []
        self.last_notification_times = {}  # To prevent duplicate notifications

    def to_dict(self):
        return {
            "name": self.name,
            "occupation": self.occupation,
            "wake_up_time": self.wake_up_time.strftime("%H:%M"),
            "breakfast_time": self.breakfast_time.strftime("%H:%M"),
            "lunch_time": self.lunch_time.strftime("%H:%M"),
            "dinner_time": self.dinner_time.strftime("%H:%M"),
            "bedtime": self.bedtime.strftime("%H:%M"),
            "living_situation": self.living_situation,
            "daily_routines": self.daily_routines,
            "locations": self.locations,
            "reminders": self.reminders,
            "calendar_events": self.calendar_events,
            "chat_history": self.chat_history
        }

    @staticmethod
    def from_dict(data):
        profile = UserProfile()
        profile.name = data.get("name", "")
        profile.occupation = data.get("occupation", "")
        profile.wake_up_time = datetime.strptime(data.get("wake_up_time", "07:00"), "%H:%M").time()
        profile.breakfast_time = datetime.strptime(data.get("breakfast_time", "08:00"), "%H:%M").time()
        profile.lunch_time = datetime.strptime(data.get("lunch_time", "13:00"), "%H:%M").time()
        profile.dinner_time = datetime.strptime(data.get("dinner_time", "19:00"), "%H:%M").time()
        profile.bedtime = datetime.strptime(data.get("bedtime", "22:00"), "%H:%M").time()
        profile.living_situation = data.get("living_situation", "")
        profile.daily_routines = data.get("daily_routines", [])
        profile.locations = data.get("locations", [])
        profile.reminders = data.get("reminders", [])
        profile.calendar_events = data.get("calendar_events", [])
        profile.chat_history = data.get("chat_history", [])
        return profile

class BrowserAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def start_browser(self):
        try:
            if not self.driver:
                # Use Chrome options to use existing profile
                options = webdriver.ChromeOptions()
                options.add_argument("user-data-dir=C:\\Users\\%USERNAME%\\AppData\\Local\\Google\\Chrome\\User Data")
                options.add_argument("profile-directory=Default")
                self.driver = webdriver.Chrome(options=options)
                self.wait = WebDriverWait(self.driver, 10)
                return True
            return True
        except Exception as e:
            print(f"Error starting browser: {str(e)}")
            return False
            
    def close_browser(self):
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
            return True
        except Exception as e:
            print(f"Error closing browser: {str(e)}")
            return False
            
    def open_youtube(self, search_query=None):
        try:
            if not self.start_browser():
                return False
            
            self.driver.get('https://www.youtube.com')
            
            if search_query:
                # Wait for search box and enter query
                search_box = self.wait.until(EC.presence_of_element_located((By.NAME, "search_query")))
                search_box.clear()
                search_box.send_keys(search_query)
                search_box.send_keys(Keys.RETURN)
                
                # Wait for results to load
                self.wait.until(EC.presence_of_element_located((By.ID, "video-title")))
            
            return True
        except Exception as e:
            print(f"Error opening YouTube: {str(e)}")
            return False
            
    def open_website(self, url):
        try:
            if not self.start_browser():
                return False
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"Error opening website: {str(e)}")
            return False
            
    def search_flights(self, origin, destination, date=None):
        try:
            if not self.start_browser():
                return False
                
            # Go to Google Flights
            self.driver.get('https://www.google.com/travel/flights')
            
            # Wait for and click the origin field
            origin_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Where from?']")))
            origin_field.clear()
            origin_field.send_keys(origin)
            time.sleep(1)
            
            # Wait for and click the destination field
            dest_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Where to?']")))
            dest_field.clear()
            dest_field.send_keys(destination)
            time.sleep(1)
            
            # Set date if provided
            if date:
                date_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Departure']")))
                date_field.clear()
                date_field.send_keys(date)
            
            # Click search
            search_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Search']")))
            search_button.click()
            
            # Wait for results
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']")))
            
            # Get flight results
            flights = self.driver.find_elements(By.CSS_SELECTOR, "div[role='main'] div[role='article']")
            results = []
            
            for flight in flights[:5]:  # Get top 5 results
                try:
                    airline = flight.find_element(By.CSS_SELECTOR, "div[aria-label*='airline']").text
                    price = flight.find_element(By.CSS_SELECTOR, "div[aria-label*='price']").text
                    time = flight.find_element(By.CSS_SELECTOR, "div[aria-label*='duration']").text
                    results.append(f"Airline: {airline}, Price: {price}, Duration: {time}")
                except:
                    continue
            
            return results
        except Exception as e:
            print(f"Error searching flights: {str(e)}")
            return None
            
    def tweet(self, message):
        try:
            if not self.start_browser():
                return False
                
            # Go to Twitter
            self.driver.get('https://twitter.com/home')
            
            # Wait for compose tweet button and click it
            compose_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/compose/tweet']")))
            compose_button.click()
            
            # Wait for tweet text area and enter message
            tweet_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']")))
            tweet_box.send_keys(message)
            
            # Click tweet button
            tweet_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-testid='tweetButton']")))
            tweet_button.click()
            
            # Wait for confirmation
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='toast']")))
            return True
        except Exception as e:
            print(f"Error tweeting: {str(e)}")
            return False

class VoiceAssistant:
    def __init__(self):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of speech
        self.engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        
        # Get available voices and set a female voice if available
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Queue for speech tasks
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        
    def listen(self):
        text = ""
        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5)
                print("Processing speech...")
                text = self.recognizer.recognize_google(audio)
                print(f"Recognized: {text}")
        except sr.WaitTimeoutError:
            print("No speech detected")
            return "TIMEOUT"
        except sr.UnknownValueError:
            print("Could not understand audio")
            return "UNKNOWN"
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return "ERROR"
        return text
        
    def speak(self, text):
        if not text:
            return
            
        def speak_task():
            self.is_speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            self.is_speaking = False
            
        # Run speech in a separate thread
        thread = threading.Thread(target=speak_task)
        thread.daemon = True
        thread.start()

class SmartAICompanion(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.profile = self.load_profile()
        self.onboarding_complete = bool(self.profile.name)
        self.current_onboarding_step = 0
        self.onboarding_questions = [
            "Hello! I'm your AI Personal Assistant. What's your name?",
            "Are you a student or a professional?",
            "What time do you usually wake up? (HH:MM)",
            "What are your usual meal times?\nBreakfast (HH:MM):",
            "Lunch (HH:MM):",
            "Dinner (HH:MM):",
            "What time do you go to bed? (HH:MM)",
            "Do you live alone or with family/friends?",
            "Tell me about your daily routines (e.g., work, gym, study). Separate with commas:",
            "What are the places you frequently visit? Separate with commas:",
        ]
        self.browser_automation = BrowserAutomation()
        self.voice_assistant = VoiceAssistant()
        self.is_listening = False
        self.voice_button = None  # Will store reference to voice button
        self.setup_notifications()
        self.initUI()
        self.setup_timer()
        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_PURPLE};
                color: {TEXT_COLOR};
                font-family: 'Segoe UI', Arial;
            }}
            QPushButton {{
                background-color: {LIGHT_PURPLE};
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_PURPLE};
            }}
            QGroupBox {{
                border: 2px solid {LIGHT_PURPLE};
                border-radius: 15px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 5px;
                color: {TEXT_COLOR};
            }}
            QListWidget {{
                background-color: {SECONDARY_BG};
                border: none;
                border-radius: 15px;
                padding: 10px;
                color: white;
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {DARK_PURPLE};
            }}
            QTabBar::tab {{
                background-color: {SECONDARY_BG};
                color: white;
                padding: 8px 20px;
                margin: 2px;
                border-radius: 10px;
            }}
            QTabBar::tab:selected {{
                background-color: {LIGHT_PURPLE};
            }}
        """)

    def setup_notifications(self):
        # Setup system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        app_icon = QtGui.QIcon()
        app_icon.addFile('https://res.cloudinary.com/dvlgixtg8/image/upload/v1739472351/Krishna-avatar.png', QtCore.QSize(64,64))
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.show()
        
        # Setup Windows toast notifier
        self.toaster = ToastNotifier()
        
        # Create icon if it doesn't exist
        if not os.path.exists('https://res.cloudinary.com/dvlgixtg8/image/upload/v1739472351/Krishna-avatar.png'):
            self.create_default_icon()
    
    def create_default_icon(self):
        # Create a simple colored icon
        icon_size = 64
        icon = QtGui.QPixmap(icon_size, icon_size)
        icon.fill(QtGui.QColor('#2196F3'))  # Material Blue color
        
        # Add text
        painter = QtGui.QPainter(icon)
        painter.setPen(QtGui.QColor('white'))
        font = QtGui.QFont('Arial', 30, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.drawText(icon.rect(), QtCore.Qt.AlignCenter, 'AI')
        painter.end()
        
        # Save icon
        icon.save('https://res.cloudinary.com/dvlgixtg8/image/upload/v1739472351/Krishna-avatar.png')

    def show_system_notification(self, title, message):
        # Show in chat
        self.chat_display.append_message(f"\nAI Assistant: {message}", is_user=False)
        
        # Show system tray notification
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
        
        # Show Windows toast notification in a separate thread
        threading.Thread(target=self.show_toast_notification, args=(title, message), daemon=True).start()
    
    def show_toast_notification(self, title, message):
        try:
            self.toaster.show_toast(
                title,
                message,
                icon_path="https://res.cloudinary.com/dvlgixtg8/image/upload/v1739472351/Krishna-avatar.png",
                duration=5,
                threaded=True
            )
        except Exception as e:
            print(f"Error showing toast notification: {e}")

    def initUI(self):
        self.setWindowTitle("Smart AI Personal Assistant")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        main_layout = QtWidgets.QHBoxLayout()
        
        # Left panel (Chat)
        left_panel = QtWidgets.QVBoxLayout()
        
        # Profile section
        profile_group = QtWidgets.QGroupBox("Profile")
        profile_layout = QtWidgets.QHBoxLayout()
        self.profile_label = QtWidgets.QLabel("Welcome!")
        self.profile_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        profile_layout.addWidget(self.profile_label)
        profile_group.setLayout(profile_layout)
        left_panel.addWidget(profile_group)

        # Chat section
        chat_group = QtWidgets.QGroupBox("Chat")
        chat_layout = QtWidgets.QVBoxLayout()
        
        self.chat_display = CustomQTextBrowser()
        chat_layout.addWidget(self.chat_display)
        
        input_layout = QtWidgets.QHBoxLayout()
        self.user_input = CustomQLineEdit()
        self.user_input.setPlaceholderText("Type your message here...")
        self.user_input.returnPressed.connect(self.sendMessage)
        
        # Add voice input button next to text input
        self.voice_button = QtWidgets.QPushButton()
        # Create microphone icon
        mic_icon = QtGui.QIcon()
        mic_icon.addPixmap(QtGui.QPixmap("mic.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.voice_button.setIcon(mic_icon)
        self.voice_button.setIconSize(QtCore.QSize(24, 24))
        self.voice_button.setFixedWidth(50)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #6B4EE6;
                border: none;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #8B6FFF;
            }
            QPushButton:pressed {
                background-color: #2D1B69;
            }
        """)
        self.voice_button.setToolTip("Click to speak")
        self.voice_button.clicked.connect(self.toggle_voice_input)
        
        # Add send button back
        send_button = QtWidgets.QPushButton("Send")
        send_button.setFixedWidth(100)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #6B4EE6;
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8B6FFF;
            }
            QPushButton:pressed {
                background-color: #2D1B69;
            }
        """)
        send_button.clicked.connect(self.sendMessage)
        
        input_layout.addWidget(self.user_input)
        input_layout.addWidget(self.voice_button)
        input_layout.addWidget(send_button)
        chat_layout.addLayout(input_layout)
        
        chat_group.setLayout(chat_layout)
        left_panel.addWidget(chat_group, stretch=1)
        
        # Add left panel to main layout
        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_panel)
        main_layout.addWidget(left_widget, stretch=2)

        # Right panel (Tabs for Reminders and Settings)
        right_panel = QTabWidget()
        right_panel.setFixedWidth(400)
        
        # Reminders tab
        reminders_tab = QtWidgets.QWidget()
        reminders_layout = QtWidgets.QVBoxLayout()
        
        self.reminders_list = QtWidgets.QListWidget()
        add_reminder_btn = QtWidgets.QPushButton("+ Add Reminder")
        add_reminder_btn.clicked.connect(self.addReminder)
        
        reminders_layout.addWidget(self.reminders_list)
        reminders_layout.addWidget(add_reminder_btn)
        reminders_tab.setLayout(reminders_layout)
        
        # Schedule tab
        schedule_tab = QtWidgets.QWidget()
        schedule_layout = QtWidgets.QVBoxLayout()
        schedule_info = QtWidgets.QTextBrowser()
        schedule_info.setStyleSheet("""
            QTextBrowser {
                background-color: #1E1246;
                border: none;
                border-radius: 15px;
                padding: 15px;
                color: white;
            }
        """)
        schedule_info.setText(f"""
            Daily Schedule:
            • Wake up: {self.profile.wake_up_time.strftime('%H:%M')}
            • Breakfast: {self.profile.breakfast_time.strftime('%H:%M')}
            • Lunch: {self.profile.lunch_time.strftime('%H:%M')}
            • Dinner: {self.profile.dinner_time.strftime('%H:%M')}
            • Bedtime: {self.profile.bedtime.strftime('%H:%M')}
        """)
        schedule_layout.addWidget(schedule_info)
        schedule_tab.setLayout(schedule_layout)
        
        # Add tabs
        right_panel.addTab(reminders_tab, "Reminders")
        right_panel.addTab(schedule_tab, "Schedule")
        
        main_layout.addWidget(right_panel)
        
        self.setLayout(main_layout)
        
        # Start onboarding if not complete
        if not self.onboarding_complete:
            self.start_onboarding()
        else:
            self.greet_user()

    def setup_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_schedule)
        self.timer.start(60000)  # Check every minute

    def check_schedule(self):
        current_time = datetime.now().time()
        current_date = datetime.now().date()
        name = self.profile.name

        # Function to check if notification should be sent
        def should_notify(event_type):
            last_time = self.profile.last_notification_times.get(event_type)
            if not last_time or (datetime.now() - last_time) > timedelta(minutes=30):
                self.profile.last_notification_times[event_type] = datetime.now()
                return True
            return False

        # Check daily schedule events
        if self.is_time_match(current_time, self.profile.wake_up_time) and should_notify('wake_up'):
            self.show_system_notification("Good Morning!", f"Rise and shine, {name}! 🌅 Time to start your day!")
            
        elif self.is_time_match(current_time, self.profile.breakfast_time) and should_notify('breakfast'):
            self.show_system_notification("Breakfast Time", f"Hey {name}, it's breakfast time! 🍳 Don't forget to eat well!")
            
        elif self.is_time_match(current_time, self.profile.lunch_time) and should_notify('lunch'):
            self.show_system_notification("Lunch Break", f"Lunch time, {name}! 🍽️ Take a break and enjoy your meal!")
            
        elif self.is_time_match(current_time, self.profile.dinner_time) and should_notify('dinner'):
            self.show_system_notification("Dinner Time", f"Dinner time, {name}! 🍽️ Time to recharge!")
            
        elif self.is_time_match(current_time, self.profile.bedtime) and should_notify('bedtime'):
            good_night_msg = self.getGroqResponse(f"Generate a short, personalized good night message for {name} who is a {self.profile.occupation}")
            self.show_system_notification("Good Night!", good_night_msg)

        # Check reminders
        for reminder in self.profile.reminders:
            try:
                reminder_datetime = datetime.strptime(reminder["datetime"], "%Y-%m-%d %H:%M")
                if (reminder_datetime.date() == current_date and 
                    self.is_time_match(current_time, reminder_datetime.time()) and 
                    should_notify(f'reminder_{reminder["title"]}')):
                    self.show_system_notification("Reminder", f"📅 {reminder['title']}")
            except ValueError as e:
                print(f"Error parsing reminder datetime: {e}")

    def is_time_match(self, current_time, target_time):
        return (current_time.hour == target_time.hour and 
                current_time.minute == target_time.minute)

    def start_onboarding(self):
        self.chat_display.append_message(self.onboarding_questions[0], is_user=False)

    def process_onboarding_answer(self, answer):
        if self.current_onboarding_step < len(self.onboarding_questions):
            if self.current_onboarding_step == 0:
                self.profile.name = answer
            elif self.current_onboarding_step == 1:
                self.profile.occupation = answer.lower()
            elif self.current_onboarding_step == 2:
                self.profile.wake_up_time = datetime.strptime(answer, "%H:%M").time()
            elif self.current_onboarding_step == 3:
                self.profile.breakfast_time = datetime.strptime(answer, "%H:%M").time()
            elif self.current_onboarding_step == 4:
                self.profile.lunch_time = datetime.strptime(answer, "%H:%M").time()
            elif self.current_onboarding_step == 5:
                self.profile.dinner_time = datetime.strptime(answer, "%H:%M").time()
            elif self.current_onboarding_step == 6:
                self.profile.bedtime = datetime.strptime(answer, "%H:%M").time()
            elif self.current_onboarding_step == 7:
                self.profile.living_situation = answer.lower()
            elif self.current_onboarding_step == 8:
                self.profile.daily_routines = [r.strip() for r in answer.split(",")]
            elif self.current_onboarding_step == 9:
                self.profile.locations = [l.strip() for l in answer.split(",")]
            
            self.current_onboarding_step += 1
            
            if self.current_onboarding_step < len(self.onboarding_questions):
                self.chat_display.append_message(self.onboarding_questions[self.current_onboarding_step], is_user=False)
            else:
                self.complete_onboarding()

    def complete_onboarding(self):
        self.onboarding_complete = True
        self.save_profile()
        self.greet_user()

    def greet_user(self):
        current_hour = datetime.now().hour
        greeting = "Good morning" if 5 <= current_hour < 12 else \
                  "Good afternoon" if 12 <= current_hour < 17 else \
                  "Good evening"
        
        message = f"{greeting}, {self.profile.name}! "
        if self.profile.living_situation == "alone":
            message += "How are you doing today? 😊"
        else:
            message += f"How are you and your {self.profile.living_situation} doing today? 😊"
        
        self.chat_display.append_message(message, is_user=False)
        self.profile_label.setText(f"Profile: {self.profile.name} ({self.profile.occupation})")

    def toggle_voice_input(self):
        if self.is_listening:
            self.is_listening = False
            self.voice_button.setStyleSheet("""
                QPushButton {
                    background-color: #6B4EE6;
                    border: none;
                    border-radius: 15px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #8B6FFF;
                }
                QPushButton:pressed {
                    background-color: #2D1B69;
                }
            """)
            return
            
        self.is_listening = True
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                border: none;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF6666;
            }
        """)
        
        def listen_task():
            text = self.voice_assistant.listen()
            self.is_listening = False
            
            # Reset button style
            self.voice_button.setStyleSheet("""
                QPushButton {
                    background-color: #6B4EE6;
                    border: none;
                    border-radius: 15px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #8B6FFF;
                }
                QPushButton:pressed {
                    background-color: #2D1B69;
                }
            """)
            
            if text and text not in ["TIMEOUT", "UNKNOWN", "ERROR"]:
                self.user_input.setText(text)
                self.sendMessage()
            elif text == "TIMEOUT":
                self.chat_display.append_message("No speech detected. Please try again.", is_user=False)
            elif text == "UNKNOWN":
                self.chat_display.append_message("Could not understand audio. Please try again.", is_user=False)
            elif text == "ERROR":
                self.chat_display.append_message("There was an error processing your speech. Please try again.", is_user=False)
        
        # Run speech recognition in a separate thread
        thread = threading.Thread(target=listen_task)
        thread.daemon = True
        thread.start()

    def sendMessage(self):
        message = self.user_input.text().strip()
        if not message:
            return
            
        self.chat_display.append_message(message, is_user=True)
        self.user_input.clear()
        
        if not self.onboarding_complete:
            self.process_onboarding_answer(message)
        else:
            # Add to chat history
            self.profile.chat_history.append({"role": "user", "content": message})
            
            # Get AI response
            response = self.getGroqResponse(message)
            self.profile.chat_history.append({"role": "assistant", "content": response})
            
            # Display and speak the response
            self.chat_display.append_message(response, is_user=False)
            self.voice_assistant.speak(response)
            self.save_profile()

    def handle_browser_command(self, message):
        # YouTube commands
        youtube_pattern = r"(?:open youtube|youtube)(?: and search for| search)? ?(?:\"([^\"]+)\"|'([^']+)'|([^\"']+))?"
        youtube_match = re.search(youtube_pattern, message.lower())
        
        if youtube_match:
            search_query = youtube_match.group(1) or youtube_match.group(2) or youtube_match.group(3)
            if search_query:
                search_query = search_query.strip()
            success = self.browser_automation.open_youtube(search_query)
            if success:
                return f"Opening YouTube{' and searching for ' + search_query if search_query else ''}"
            return "I apologize, but I encountered an issue while trying to open YouTube. Please try again."
            
        # Flight search commands
        flight_pattern = r"search for flights from (\w+) to (\w+)(?: on (.+))?"
        flight_match = re.search(flight_pattern, message.lower())
        
        if flight_match:
            origin, destination, date = flight_match.groups()
            results = self.browser_automation.search_flights(origin, destination, date)
            if results:
                return f"Here are the top flight options:\n" + "\n".join(results)
            return "I apologize, but I couldn't find flight information. Please try again."
            
        # Twitter commands
        tweet_pattern = r"tweet (.+)"
        tweet_match = re.search(tweet_pattern, message.lower())
        
        if tweet_match:
            message = tweet_match.group(1)
            success = self.browser_automation.tweet(message)
            if success:
                return "Your tweet has been posted successfully!"
            return "I apologize, but I couldn't post your tweet. Please try again."
            
        # General website commands
        website_pattern = r"open (?:website |url |link |chrome )?(?:\"([^\"]+)\"|'([^']+)'|([^\"']+))"
        website_match = re.search(website_pattern, message.lower())
        
        if website_match:
            url = website_match.group(1) or website_match.group(2) or website_match.group(3)
            url = url.strip()
            success = self.browser_automation.open_website(url)
            if success:
                return f"Opening website: {url}"
            return "I apologize, but I encountered an issue while trying to open the website. Please try again."
            
        return None

    def getGroqResponse(self, message):
        try:
            # Check for browser automation commands first
            browser_response = self.handle_browser_command(message)
            if browser_response:
                return browser_response
                
            # Continue with existing Groq API response logic
            # Enhanced context with specific schedule information
            schedule_info = (
                f"Their daily schedule is:\n"
                f"- Wake up time: {self.profile.wake_up_time.strftime('%H:%M')}\n"
                f"- Breakfast time: {self.profile.breakfast_time.strftime('%H:%M')}\n"
                f"- Lunch time: {self.profile.lunch_time.strftime('%H:%M')}\n"
                f"- Dinner time: {self.profile.dinner_time.strftime('%H:%M')}\n"
                f"- Bedtime: {self.profile.bedtime.strftime('%H:%M')}\n"
            )

            context = (
                f"You are a personal AI assistant for {self.profile.name}, who is a {self.profile.occupation}. "
                f"They live {self.profile.living_situation}. "
                f"Their daily routines include: {', '.join(self.profile.daily_routines)}. \n"
                f"{schedule_info}\n"
                f"When asked about meal times or schedule, always refer to the exact times listed above. "
                f"Current time is {datetime.now().strftime('%H:%M')}. "
                f"You can modify their schedule using UPDATE_PROFILE command with a JSON structure."
            )
            
            # Check for schedule-related keywords
            lower_msg = message.lower()
            schedule_keywords = {
                'breakfast': self.profile.breakfast_time,
                'lunch': self.profile.lunch_time,
                'dinner': self.profile.dinner_time,
                'wake': self.profile.wake_up_time,
                'bed': self.profile.bedtime
            }

            # Direct schedule queries
            for keyword, time_value in schedule_keywords.items():
                if keyword in lower_msg and 'time' in lower_msg:
                    return f"Your {keyword} time is scheduled for {time_value.strftime('%H:%M')}."

            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            messages = [{"role": "system", "content": context}]
            messages.extend(self.profile.chat_history[-5:])
            messages.append({"role": "user", "content": message})
            
            data = {
                "model": "mixtral-8x7b-32768",
                "messages": messages,
                "max_tokens": 150
            }
            
            response = requests.post(GROQ_API_URL, headers=headers, json=data)
            response.raise_for_status()
            
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                ai_response = response_data["choices"][0]["message"]["content"]
                
                # Check if the response contains profile modification commands
                if "UPDATE_PROFILE:" in ai_response:
                    self.handle_profile_update(ai_response)
                    ai_response = ai_response.split("UPDATE_PROFILE:")[0].strip()
                
                return ai_response
            else:
                return "I'm having trouble understanding. Could you please rephrase that?"
                
        except Exception as e:
            return f"I apologize, but I'm having trouble responding right now. {str(e)}"

    def handle_profile_update(self, response):
        try:
            update_part = response.split("UPDATE_PROFILE:")[1].strip()
            updates = json.loads(update_part)
            
            # Update profile attributes
            for key, value in updates.items():
                if hasattr(self.profile, key):
                    if key.endswith('_time'):
                        setattr(self.profile, key, datetime.strptime(value, "%H:%M").time())
                    else:
                        setattr(self.profile, key, value)
            
            self.save_profile()
            self.show_system_notification("Profile Updated", "Your profile has been updated with new information!")
        except Exception as e:
            print(f"Error updating profile: {str(e)}")

    def addReminder(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Reminder")
        layout = QtWidgets.QFormLayout()

        # Create input fields
        title = QtWidgets.QLineEdit()
        date = QtWidgets.QDateEdit()
        date.setCalendarPopup(True)
        date.setDate(QtCore.QDate.currentDate())
        time = QtWidgets.QTimeEdit()
        time.setTime(QtCore.QTime.currentTime())

        # Add fields to layout
        layout.addRow("Title:", title)
        layout.addRow("Date:", date)
        layout.addRow("Time:", time)

        # Add buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Create reminder with proper datetime format
            reminder_datetime = datetime.combine(
                date.date().toPyDate(),
                time.time().toPyTime()
            )
            
            reminder = {
                "title": title.text(),
                "datetime": reminder_datetime.strftime("%Y-%m-%d %H:%M")
            }
            
            self.profile.reminders.append(reminder)
            self.reminders_list.addItem(f"{reminder['datetime']} - {reminder['title']}")
            self.save_profile()
            
            # Show immediate notification for testing
            self.show_system_notification(
                "Reminder Added", 
                f"New reminder set for {reminder['datetime']}: {reminder['title']}"
            )

    def save_profile(self):
        with open("user_profile.json", "w") as f:
            json.dump(self.profile.to_dict(), f, indent=4)

    def load_profile(self):
        try:
            with open("user_profile.json", "r") as f:
                return UserProfile.from_dict(json.load(f))
        except FileNotFoundError:
            return UserProfile()

    def closeEvent(self, event):
        # Remove browser closing since we're using system browser
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SmartAICompanion()
    window.show()
    sys.exit(app.exec_())
