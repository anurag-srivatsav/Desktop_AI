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
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import subprocess
import psutil
import win32gui
import win32con
import win32process
import win32com.client
import pyautogui

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
        self.browser = webbrowser.get()
        
    def open_youtube(self, search_query=None):
        try:
            if search_query:
                # Create YouTube search URL
                search_query = search_query.replace(' ', '+')
                url = f'https://www.youtube.com/results?search_query={search_query}'
            else:
                url = 'https://www.youtube.com'
            
            self.browser.open(url)
            return True
        except Exception as e:
            print(f"Error opening YouTube: {str(e)}")
            return False
            
    def open_website(self, url):
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.browser.open(url)
            return True
        except Exception as e:
            print(f"Error opening website: {str(e)}")
            return False
            
    def search_flights(self, origin, destination, date=None):
        try:
            # Create Google Flights URL with parameters
            url = f'https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{destination}'
            if date:
                url += f'%20on%20{date}'
            
            self.browser.open(url)
            return ["I've opened Google Flights with your search criteria. You can now view and compare flights directly in your browser."]
        except Exception as e:
            print(f"Error searching flights: {str(e)}")
            return None
            
    def tweet(self, message):
        try:
            # Open Twitter compose tweet page
            self.browser.open('https://twitter.com/compose/tweet')
            return True
        except Exception as e:
            print(f"Error opening Twitter: {str(e)}")
            return False

class VoiceAssistant:
    def __init__(self):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize pyttsx3 text-to-speech engine
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        # Set female voice
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Set properties
        self.engine.setProperty('rate', 150)    # Speed
        self.engine.setProperty('volume', 1.0)  # Volume
        
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

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.categories = {
            'study': [],
            'work': [],
            'personal': [],
            'health': [],
            'shopping': [],
            'meetings': []
        }
        
    def add_task(self, title, description, category, due_date=None, priority='medium'):
        task = {
            'id': len(self.tasks) + 1,
            'title': title,
            'description': description,
            'category': category,
            'due_date': due_date,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now()
        }
        self.tasks.append(task)
        self.categories[category].append(task)
        return task
        
    def complete_task(self, task_id):
        for task in self.tasks:
            if task['id'] == task_id:
                task['status'] = 'completed'
                task['completed_at'] = datetime.now()
                return True
        return False
        
    def get_tasks_by_category(self, category):
        return self.categories.get(category, [])
        
    def get_pending_tasks(self):
        return [task for task in self.tasks if task['status'] == 'pending']
        
    def get_overdue_tasks(self):
        now = datetime.now()
        return [task for task in self.tasks 
                if task['status'] == 'pending' and 
                task['due_date'] and 
                task['due_date'] < now]

class DesktopController:
    def __init__(self):
        self.shell = win32com.client.Dispatch("WScript.Shell")
        self.common_apps = {
            'notepad': 'notepad.exe',
            'telegram': 'Telegram.exe',
            'calculator': 'calc.exe',
            'word': 'WINWORD.EXE',
            'excel': 'EXCEL.EXE',
            'powerpoint': 'POWERPNT.EXE',
            'paint': 'mspaint.exe',
            'control panel': 'control.exe',
            'task manager': 'taskmgr.exe',
            'file explorer': 'explorer.exe',
            'settings': 'ms-settings:',
            'cmd': 'cmd.exe',
            'powershell': 'powershell.exe',
            'vscode': 'code.exe',
            'spotify': 'spotify.exe',
            'discord': 'discord.exe',
            'zoom': 'zoom.exe',
            'teams': 'teams.exe',
            'outlook': 'OUTLOOK.EXE'
        }
        
    def open_app(self, app_name):
        try:
            app_name = app_name.lower()
            if app_name == 'telegram':
                # List of common Telegram installation paths
                telegram_paths = [
                    r"C:\Program Files\WindowsApps\TelegramMessengerLLP.TelegramDesktop_5.10.3.0_x64__t4vj0pshhgkwm\Telegram.exe",
                    os.path.join(os.getenv('LOCALAPPDATA'), 'Telegram Desktop', 'Telegram.exe'),
                    os.path.join(os.getenv('PROGRAMFILES'), 'Telegram Desktop', 'Telegram.exe'),
                    os.path.join(os.getenv('PROGRAMFILES(X86)'), 'Telegram Desktop', 'Telegram.exe'),
                    os.path.join(os.getenv('APPDATA'), 'Telegram Desktop', 'Telegram.exe'),
                    'D:\\Telegram Desktop\\Telegram.exe',
                    'C:\\Telegram Desktop\\Telegram.exe'
                ]
                
                # Try each possible path
                for path in telegram_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        return "Opening Telegram"
                
                # If no paths work, try running directly (in case it's in PATH)
                try:
                    subprocess.Popen(['telegram'])
                    return "Opening Telegram"
                except:
                    return "Could not find Telegram. Please make sure it's installed correctly and try again."
                    
            elif app_name in self.common_apps:
                subprocess.Popen([self.common_apps[app_name]])
                return f"Opening {app_name}"
            else:
                # Try to open the app using the shell
                self.shell.Run(app_name)
                return f"Attempting to open {app_name}"
        except Exception as e:
            return f"Failed to open {app_name}: {str(e)}"
    
    def control_spotify(self, command, song_name=None):
        try:
            # First check if Spotify is running, if not start it
            spotify_running = False
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == 'spotify.exe':
                    spotify_running = True
                    break
            
            if not spotify_running:
                subprocess.Popen('spotify.exe')
                time.sleep(5)  # Increased wait time for Spotify to fully load
            
            # Get Spotify window handle
            def find_spotify_window(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if 'spotify' in title.lower():
                        windows.append(hwnd)
            
            windows = []
            win32gui.EnumWindows(find_spotify_window, windows)
            
            if not windows:
                return "Could not find Spotify window"
            
            spotify_hwnd = windows[0]
            
            # Focus Spotify window
            win32gui.SetForegroundWindow(spotify_hwnd)
            time.sleep(1)  # Increased wait time for window focus
            
            if command == 'play' and song_name:
                # Press Ctrl+L to focus search
                self.shell.SendKeys('^l')
                time.sleep(0.5)
                # Clear any existing search
                self.shell.SendKeys('^a')
                time.sleep(0.2)
                self.shell.SendKeys('{DELETE}')
                time.sleep(0.2)
                # Type song name
                self.shell.SendKeys(song_name)
                time.sleep(1)  # Wait for search results
                # Press Enter to select search results
                self.shell.SendKeys('~')
                time.sleep(1)  # Wait for results to load
                # Press Enter to play first result
                self.shell.SendKeys('~')
                time.sleep(0.5)
                # Press Space to ensure playback starts
                self.shell.SendKeys(' ')
                return f"Playing '{song_name}' on Spotify"
            elif command == 'pause':
                self.shell.SendKeys(' ')  # Space to pause
                return "Paused Spotify playback"
            elif command == 'play':
                self.shell.SendKeys(' ')  # Space to play
                return "Resumed Spotify playback"
            elif command == 'next':
                self.shell.SendKeys('^{RIGHT}')  # Ctrl+Right for next track
                return "Playing next track"
            elif command == 'previous':
                self.shell.SendKeys('^{LEFT}')  # Ctrl+Left for previous track
                return "Playing previous track"
            else:
                return "Unknown Spotify command"
                
        except Exception as e:
            return f"Failed to control Spotify: {str(e)}"
    
    def close_app(self, app_name):
        try:
            app_exe = self.common_apps.get(app_name.lower(), app_name)
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == app_exe.lower():
                    proc.kill()
            return f"Closed {app_name}"
        except Exception as e:
            return f"Failed to close {app_name}: {str(e)}"
    
    def minimize_window(self, window_title):
        try:
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if window_title.lower() in title.lower():
                        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                        windows.append(hwnd)
            windows = []
            win32gui.EnumWindows(callback, windows)
            return f"Minimized windows containing '{window_title}'"
        except Exception as e:
            return f"Failed to minimize windows: {str(e)}"
    
    def maximize_window(self, window_title):
        try:
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if window_title.lower() in title.lower():
                        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                        windows.append(hwnd)
            windows = []
            win32gui.EnumWindows(callback, windows)
            return f"Maximized windows containing '{window_title}'"
        except Exception as e:
            return f"Failed to maximize windows: {str(e)}"

    def control_system_volume(self, command):
        try:
            if command == 'up':
                pyautogui.press('volumeup')
                pyautogui.press('volumeup')
                return "Volume increased"
            elif command == 'down':
                pyautogui.press('volumedown')
                pyautogui.press('volumedown')
                return "Volume decreased"
            elif command == 'mute':
                pyautogui.press('volumemute')
                return "Volume muted"
            return "Unknown volume command"
        except Exception as e:
            return f"Failed to control volume: {str(e)}"

    def control_brightness(self, command):
        try:
            if command == 'up':
                subprocess.run(['powershell', '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)'], capture_output=True)
                return "Brightness increased"
            elif command == 'down':
                subprocess.run(['powershell', '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)'], capture_output=True)
                return "Brightness decreased"
            return "Unknown brightness command"
        except Exception as e:
            return f"Failed to control brightness: {str(e)}"

class SmartAICompanion(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.profile = self.load_profile()
        self.task_manager = TaskManager()
        self.desktop_controller = DesktopController()  # Add desktop controller
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
            "What are your main interests and hobbies?",
            "What are your goals for the next month?",
            "Do you have any dietary restrictions or preferences?",
            "What languages do you speak?",
            "What are your preferred study/work hours?"
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
        # Setup Windows toast notifier only
        self.toaster = ToastNotifier()
    
    def show_system_notification(self, title, message):
        # Show in chat
        self.chat_display.append_message(f"\nAI Assistant: {message}", is_user=False)
        
        # Remove emojis for speech output
        speech_message = re.sub(r'[^\w\s.,!?-]', '', message)
        self.voice_assistant.speak(speech_message)
        
        # Show Windows toast notification in a separate thread
        threading.Thread(target=self.show_toast_notification, args=(title, message), daemon=True).start()
    
    def show_toast_notification(self, title, message):
        try:
            self.toaster.show_toast(
                title,
                message,
                duration=5,
                threaded=True
            )
        except Exception as e:
            print(f"Error showing toast notification: {e}")

    def initUI(self):
        # Set application icon
        app_icon = QtGui.QIcon()
        app_icon.addFile('favicon.ico')  # You can use .ico file on Windows
        self.setWindowIcon(app_icon)
        
        self.setWindowTitle("Smart AI Personal Assistant - Anurag")
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
        self.voice_button = QtWidgets.QPushButton("🎤")
        self.voice_button.setFixedWidth(50)
        self.voice_button.setStyleSheet("""
            QPushButton {
                background-color: #6B4EE6;
                border: none;
                border-radius: 15px;
                padding: 8px;
                font-size: 20px;
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

        # Check daily schedule events with friendly messages
        if self.is_time_match(current_time, self.profile.wake_up_time) and should_notify('wake_up'):
            self.show_system_notification("Good Morning!", f"Hey {name}! 🌅 Time to wake up! I'm here to start your day with you. Ready to tackle your {self.profile.occupation}? Let's make it a great day! 😊")
            
        elif self.is_time_match(current_time, self.profile.breakfast_time) and should_notify('breakfast'):
            self.show_system_notification("Breakfast Time", f"Hey {name}! 🍳 I'm getting hungry just thinking about breakfast! Take a break from your {self.profile.occupation} and join me for a healthy meal. What's on your breakfast menu today? 😋")
            
        elif self.is_time_match(current_time, self.profile.lunch_time) and should_notify('lunch'):
            self.show_system_notification("Lunch Break", f"Hey {name}! 🍽️ I know you're busy with your {self.profile.occupation}, but it's lunch time! Let's take a break together. I'll keep you company while you eat! How's your day going so far? 😊")
            
        elif self.is_time_match(current_time, self.profile.dinner_time) and should_notify('dinner'):
            self.show_system_notification("Dinner Time", f"Hey {name}! 🍽️ Time to wind down after your {self.profile.occupation}! Let's have dinner together. I want to hear all about your day! What was the best part? 😊")
            
        elif self.is_time_match(current_time, self.profile.bedtime) and should_notify('bedtime'):
            good_night_msg = self.getGroqResponse(
                f"Generate a warm, friendly good night message for {name} who is a {self.profile.occupation}. "
                f"Make it personal and caring, like a friend saying goodnight. Include a reflection on their day and a positive thought for tomorrow."
            )
            self.show_system_notification("Good Night!", good_night_msg)

        # Random friendly check-ins (every 30 minutes)
        if current_time.minute % 30 == 0 and should_notify(f'friendly_check_in_{current_time.hour}_{current_time.minute}'):
            check_in_msg = self.getGroqResponse(
                f"Generate a short, friendly message to check in on {name} who is a {self.profile.occupation}. "
                f"Make it casual and conversational, like a friend asking how they're doing. Current time is {current_time.strftime('%H:%M')}. "
                f"Ask about their work/study, their mood, or share a small joke or motivational thought."
            )
            self.show_system_notification("Friendly Check-in", check_in_msg)

        # Work/Study session check-ins (every 2 hours)
        if current_time.hour % 2 == 0 and current_time.minute == 0 and should_notify(f'work_session_{current_time.hour}'):
            work_msg = self.getGroqResponse(
                f"Generate a friendly message to check on {name}'s progress with their {self.profile.occupation}. "
                f"Make it encouraging and supportive, like a friend checking in. Current time is {current_time.strftime('%H:%M')}. "
                f"Ask if they need a break, water, or just someone to talk to."
            )
            self.show_system_notification("Work Session Check-in", work_msg)

        # Mood check-ins (every 4 hours)
        if current_time.hour % 4 == 0 and current_time.minute == 0 and should_notify(f'mood_check_{current_time.hour}'):
            mood_msg = self.getGroqResponse(
                f"Generate a caring message to check on {name}'s mood and well-being. "
                f"Make it personal and empathetic, like a friend who cares. Current time is {current_time.strftime('%H:%M')}. "
                f"Ask about their day, offer support, or share a positive thought."
            )
            self.show_system_notification("How are you feeling?", mood_msg)

        # Check reminders
        for reminder in self.profile.reminders:
            try:
                reminder_datetime = datetime.strptime(reminder["datetime"], "%Y-%m-%d %H:%M")
                if (reminder_datetime.date() == current_date and 
                    self.is_time_match(current_time, reminder_datetime.time()) and 
                    should_notify(f'reminder_{reminder["title"]}')):
                    self.show_system_notification("Friendly Reminder", f"Hey {name}! 📅 Don't forget: {reminder['title']} - I'm here to help you stay on track! 😊")
            except ValueError as e:
                print(f"Error parsing reminder datetime: {e}")

        # Save the last notification times
        self.save_profile()

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
            elif self.current_onboarding_step == 10:
                self.profile.interests = [i.strip() for i in answer.split(",")]
            elif self.current_onboarding_step == 11:
                self.profile.goals = [g.strip() for g in answer.split(",")]
            elif self.current_onboarding_step == 12:
                self.profile.dietary_restrictions = [r.strip() for r in answer.split(",")]
            elif self.current_onboarding_step == 13:
                self.profile.languages = [l.strip() for l in answer.split(",")]
            elif self.current_onboarding_step == 14:
                self.profile.preferred_study_work_hours = [h.strip() for h in answer.split(",")]
            
            self.current_onboarding_step += 1
            
            if self.current_onboarding_step < len(self.onboarding_questions):
                self.chat_display.append_message(self.onboarding_questions[self.current_onboarding_step], is_user=False)
            else:
                self.complete_onboarding()

    def complete_onboarding(self):
        self.onboarding_complete = True
        self.save_profile()
        self.greet_user()

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

    def handle_desktop_command(self, message):
        # Check for email write command with Gmail-specific pattern
        email_write_pattern = r"(?:write |send |compose )?(?:email|mail|e-mail)(?: to)? ([a-zA-Z0-9._%+-]+@gmail\.com)?(?: about| regarding| on)? (.+)"
        email_write_match = re.search(email_write_pattern, message.lower())
        if email_write_match:
            email = email_write_match.group(1)
            topic = email_write_match.group(2).strip() if email_write_match.group(2) else ""
            
            if not email:
                return "Please specify a Gmail address (example@gmail.com) to send the mail to."
            
            if not email.endswith('@gmail.com'):
                return "Please provide a valid Gmail address. The email address should end with @gmail.com"
            
            # Generate content about the topic using Groq
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            prompt = f"Write a professional email about {topic}. Include a subject line, proper greeting, detailed body, and professional closing. Make it formal but engaging."
            data = {
                "model": "deepseek-r1-distill-llama-70b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500  # Increased token limit for longer text
            }
            try:
                response = requests.post(GROQ_API_URL, headers=headers, json=data)
                response.raise_for_status()
                response_data = response.json()
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"].strip()
                    
                    # Create mailto URL with the content
                    subject = topic.replace(" ", "%20")
                    body = content.replace("\n", "%0D%0A").replace(" ", "%20")
                    mailto_url = f"mailto:{email}?subject={subject}&body={body}"
                    
                    # Open default email client with the composed email
                    webbrowser.open(mailto_url)
                    
                    return f"I've opened your email client with a composed email to {email} about {topic}"
                else:
                    return "I apologize, but I couldn't generate the email content."
            except Exception as e:
                return f"Failed to compose email: {str(e)}"

        # Check for notepad write command
        notepad_write_pattern = r"(?:open )?notepad(?: and)? write(?: about)? (.+)"
        notepad_write_match = re.search(notepad_write_pattern, message.lower())
        if notepad_write_match:
            topic = notepad_write_match.group(1).strip()
            # Generate content about the topic using Groq
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            prompt = f"Write a detailed, well-structured article about {topic}. Include an introduction, key points, and a conclusion. Make it informative and engaging. Write at least 3-4 paragraphs."
            data = {
                "model": "mixtral-8x7b-32768",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500  # Increased token limit for longer text
            }
            try:
                response = requests.post(GROQ_API_URL, headers=headers, json=data)
                response.raise_for_status()
                response_data = response.json()
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"].strip()
                    
                    # Open Notepad
                    subprocess.Popen(['notepad.exe'])
                    time.sleep(2)  # Increased wait time for Notepad to open
                    
                    # Ensure Notepad window is focused
                    def find_notepad_window(hwnd, windows):
                        if win32gui.IsWindowVisible(hwnd):
                            title = win32gui.GetWindowText(hwnd)
                            if 'Untitled - Notepad' in title:
                                windows.append(hwnd)
                    
                    windows = []
                    win32gui.EnumWindows(find_notepad_window, windows)
                    if windows:
                        win32gui.SetForegroundWindow(windows[0])
                        time.sleep(0.5)  # Wait for window to focus
                    
                    # Type the content with proper line breaks
                    for line in content.split('\n'):
                        pyautogui.write(line)
                        pyautogui.press('enter')
                        time.sleep(0.1)  # Small delay between lines
                    
                    return f"I've opened Notepad and written a detailed article about {topic}"
                else:
                    return "I apologize, but I couldn't generate content about that topic."
            except Exception as e:
                return f"Failed to write in Notepad: {str(e)}"

        # Check for volume control commands
        volume_pattern = r"(?:volume|sound) (up|down|mute)"
        volume_match = re.search(volume_pattern, message.lower())
        if volume_match:
            volume_command = volume_match.group(1)
            return self.desktop_controller.control_system_volume(volume_command)
        
        # Check for brightness control commands
        brightness_pattern = r"(?:brightness|screen) (up|down)"
        brightness_match = re.search(brightness_pattern, message.lower())
        if brightness_match:
            brightness_command = brightness_match.group(1)
            return self.desktop_controller.control_brightness(brightness_command)
        
        # Desktop applications with their executable names
        desktop_apps = {
            'spotify': 'spotify.exe',
            'telegram': 'Telegram.exe',
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'word': 'WINWORD.EXE',
            'excel': 'EXCEL.EXE',
            'powerpoint': 'POWERPNT.EXE',
            'paint': 'mspaint.exe',
            'control panel': 'control.exe',
            'task manager': 'taskmgr.exe',
            'file explorer': 'explorer.exe',
            'settings': 'ms-settings:',
            'cmd': 'cmd.exe',
            'powershell': 'powershell.exe',
            'vscode': 'code.exe',
            'discord': 'discord.exe',
            'zoom': 'zoom.exe',
            'teams': 'teams.exe',
            'outlook': 'OUTLOOK.EXE'
        }

        # Patterns for desktop commands
        open_pattern = r"(?:open|launch|start|run) (?:app |application |program )?(?:\"([^\"]+)\"|'([^']+)'|([^\"']+))"
        close_pattern = r"(?:close|quit|exit|stop) (?:app |application |program )?(?:\"([^\"]+)\"|'([^']+)'|([^\"']+))"
        minimize_pattern = r"(?:minimize|hide) (?:window |app |application |program )?(?:\"([^\"]+)\"|'([^']+)'|([^\"']+))"
        maximize_pattern = r"(?:maximize|show|restore) (?:window |app |application |program )?(?:\"([^\"]+)\"|'([^']+)'|([^\"']+))"
        
        # Spotify control patterns
        spotify_play_pattern = r"(?:open )?spotify(?: and)? play (.+)"
        spotify_control_pattern = r"(?:spotify )?(play|pause|next|previous)(?: song| track)?"
        
        message_lower = message.lower()
        
        # First check if it's just the app name
        for app_name in desktop_apps.keys():
            if message_lower == app_name:
                return self.desktop_controller.open_app(app_name)
        
        # Check for Spotify play command
        spotify_play_match = re.search(spotify_play_pattern, message_lower)
        if spotify_play_match:
            song_name = spotify_play_match.group(1).strip()
            return self.desktop_controller.control_spotify('play', song_name)
            
        # Check for Spotify control commands
        spotify_control_match = re.search(spotify_control_pattern, message_lower)
        if spotify_control_match:
            command = spotify_control_match.group(1)
            return self.desktop_controller.control_spotify(command)
        
        # Check for open command
        open_match = re.search(open_pattern, message_lower)
        if open_match:
            app_name = (open_match.group(1) or open_match.group(2) or open_match.group(3)).strip().lower()
            
            # Check if it's a desktop application
            if app_name in desktop_apps:
                return self.desktop_controller.open_app(app_name)
            return None
            
        # Check for close command
        close_match = re.search(close_pattern, message_lower)
        if close_match:
            app_name = (close_match.group(1) or close_match.group(2) or close_match.group(3)).strip().lower()
            
            # Check if it's a desktop application
            if app_name in desktop_apps:
                return self.desktop_controller.close_app(app_name)
            return None
            
        # Check for minimize command
        minimize_match = re.search(minimize_pattern, message_lower)
        if minimize_match:
            window_title = (minimize_match.group(1) or minimize_match.group(2) or minimize_match.group(3)).strip()
            
            return self.desktop_controller.minimize_window(window_title)
            
        # Check for maximize command
        maximize_match = re.search(maximize_pattern, message_lower)
        if maximize_match:
            window_title = (maximize_match.group(1) or maximize_match.group(2) or maximize_match.group(3)).strip()
            return self.desktop_controller.maximize_window(window_title)
            
        return None

    def handle_browser_command(self, message):
        # Common educational and AI websites
        common_sites = {
            'chatgpt': 'https://chat.openai.com',
            'telegram': 'https://web.telegram.org',
            'twitter': 'https://x.com/home',
            'github': 'https://github.com',
            'google': 'https://www.google.com',
            'gmail': 'https://mail.google.com',
            'youtube': 'https://www.youtube.com',
            'linkedin': 'https://www.linkedin.com',
            'stackoverflow': 'https://stackoverflow.com',
            'leetcode': 'https://leetcode.com',
            'hackerrank': 'https://www.hackerrank.com',
            'coursera': 'https://www.coursera.org',
            'udemy': 'https://www.udemy.com',
            'kaggle': 'https://www.kaggle.com',
            'medium': 'https://medium.com',
            'arxiv': 'https://arxiv.org',
            'papers with code': 'https://paperswithcode.com',
            'google scholar': 'https://scholar.google.com',
            'researchgate': 'https://www.researchgate.net',
            'ieee': 'https://ieee.org',
            'acm': 'https://www.acm.org',
            'google drive': 'https://drive.google.com',
            'google docs': 'https://docs.google.com',
            'google sheets': 'https://sheets.google.com',
            'google slides': 'https://slides.google.com',
            'google meet': 'https://meet.google.com',
            'google calendar': 'https://calendar.google.com',
            'google translate': 'https://translate.google.com',
            'maps': 'https://maps.google.com',
            'google maps': 'https://maps.google.com',
            'google photos': 'https://photos.google.com',
            'google classroom': 'https://classroom.google.com',
            'google keep': 'https://keep.google.com',
            'google tasks': 'https://tasks.google.com',
            'google forms': 'https://forms.google.com',
            'google sites': 'https://sites.google.com',
            'google books': 'https://books.google.com',
            'google news': 'https://news.google.com',
            'google flights': 'https://www.google.com/travel/flights',
            'google hotels': 'https://www.google.com/travel/hotels',
            'google shopping': 'https://shopping.google.com',
            'google finance': 'https://finance.google.com',
            'google trends': 'https://trends.google.com',
            'google earth': 'https://earth.google.com',
            'google lens': 'https://lens.google.com',
            'google arts': 'https://artsandculture.google.com',
            'google fonts': 'https://fonts.google.com',
            'google developers': 'https://developers.google.com',
            'google cloud': 'https://cloud.google.com',
            'google ai': 'https://ai.google',
            'google research': 'https://research.google',
            'google quantum': 'https://quantum.google',
            'google x': 'https://x.company'
        }

        # First check if the command is for a desktop application
        desktop_apps = ['spotify', 'notepad', 'calculator', 'word', 'excel', 'powerpoint', 'paint', 
                       'control panel', 'task manager', 'file explorer', 'settings', 'cmd', 'powershell', 
                       'vscode', 'discord', 'zoom', 'teams', 'outlook']
        
        # Check if the command is trying to open a desktop app
        for app in desktop_apps:
            if f"open {app}" in message.lower() or message.lower() == app:
                return None  # Let desktop handler handle it

        # First check for YouTube commands (since they have special search functionality)
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

        # Check for maps search command
        maps_direction_pattern = r"(?:search|show|find|get|navigate|directions?|route) (?:from|between) ([^to]+) to ([^$]+)"
        maps_search_pattern = r"(?:open|go to|navigate to|launch|visit|show|display|browse) (?:maps|google maps)(?: and search for| search)? ?(?:\"([^\"]+)\"|'([^']+)'|([^\"']+))?"
        
        # First check for directions/route queries
        maps_direction_match = re.search(maps_direction_pattern, message.lower())
        if maps_direction_match:
            origin = maps_direction_match.group(1).strip()
            destination = maps_direction_match.group(2).strip()
            encoded_origin = requests.utils.quote(origin)
            encoded_destination = requests.utils.quote(destination)
            maps_url = f"https://www.google.com/maps/dir/{encoded_origin}/{encoded_destination}"
            success = self.browser_automation.open_website(maps_url)
            if success:
                return f"Opening Google Maps with directions from '{origin}' to '{destination}'"
            return "I apologize, but I encountered an issue while trying to open Google Maps. Please try again."
        
        # Then check for general maps searches
        maps_search_match = re.search(maps_search_pattern, message.lower())
        if maps_search_match:
            search_query = maps_search_match.group(1) or maps_search_match.group(2) or maps_search_match.group(3)
            if search_query:
                search_query = search_query.strip()
                encoded_query = requests.utils.quote(search_query)
                maps_url = f"https://www.google.com/maps/search/{encoded_query}"
                success = self.browser_automation.open_website(maps_url)
                if success:
                    return f"Opening Google Maps and searching for '{search_query}'"
                return "I apologize, but I encountered an issue while trying to open Google Maps. Please try again."
            else:
                success = self.browser_automation.open_website("https://maps.google.com")
                if success:
                    return "Opening Google Maps"
                return "I apologize, but I encountered an issue while trying to open Google Maps. Please try again."

        # Check for Twitter/X post command
        tweet_pattern = r"(?:tweet|post on twitter|post on x)(?: (.+))?"
        tweet_match = re.search(tweet_pattern, message.lower())
        
        if tweet_match:
            tweet_text = tweet_match.group(1)
            if not tweet_text:
                # Generate tweet text using Groq API
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                prompt = "Generate a short, engaging tweet (max 280 characters) about technology, AI, or innovation. Make it interesting and include relevant hashtags."
                data = {
                    "model": "mixtral-8x7b-32768",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100
                }
                try:
                    response = requests.post(GROQ_API_URL, headers=headers, json=data)
                    response.raise_for_status()
                    response_data = response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        tweet_text = response_data["choices"][0]["message"]["content"].strip()
                    else:
                        tweet_text = "Excited about the future of AI and technology! #AI #Innovation #Tech"
                except Exception as e:
                    print(f"Error generating tweet: {str(e)}")
                    tweet_text = "Excited about the future of AI and technology! #AI #Innovation #Tech"
            
            # URL encode the tweet text
            encoded_text = requests.utils.quote(tweet_text)
            tweet_url = f"https://x.com/intent/tweet?text={encoded_text}"
            success = self.browser_automation.open_website(tweet_url)
            if success:
                return f"Opening X (Twitter) to post your tweet: '{tweet_text}'"
            return "I apologize, but I encountered an issue while trying to open X (Twitter). Please try again."

        # Check for common sites
        message_lower = message.lower()
        for site_name, url in common_sites.items():
            # Create patterns to match various ways of requesting a site
            patterns = [
                f"(?:open|go to|navigate to|launch|visit|show|display|browse) {site_name}",
                f"^{site_name}$",  # Exact match
                f"^open {site_name}$"  # Simple "open site" command
            ]
            
            # Check if any pattern matches
            if any(re.search(pattern, message_lower) for pattern in patterns):
                success = self.browser_automation.open_website(url)
                if success:
                    return f"Opening {site_name.title()}"
                return f"I apologize, but I encountered an issue while trying to open {site_name}. Please try again."

        # General website commands (for URLs not in common_sites)
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

    def greet_user(self):
        current_hour = datetime.now().hour
        greeting = "Good morning" if 5 <= current_hour < 12 else \
                  "Good afternoon" if 12 <= current_hour < 17 else \
                  "Good evening"
        
        # Create a more personal greeting based on chat history
        recent_chat = self.profile.chat_history[-5:] if self.profile.chat_history else []
        personal_context = ""
        
        # Check for recent mentions of work/tasks
        for chat in recent_chat:
            if "work" in chat["content"].lower() or "task" in chat["content"].lower():
                personal_context = f"I remember you mentioned some work earlier. How's that going? "
                break
        
        # Check for mentions of loneliness
        for chat in recent_chat:
            if "lonely" in chat["content"].lower() or "alone" in chat["content"].lower():
                personal_context = f"I hope you're feeling better now. I'm here to keep you company. "
                break
        
        # Create the greeting message
        message = f"Hey, I'm RK! {greeting}, {self.profile.name}! "
        if self.profile.living_situation == "alone":
            message += f"{personal_context}I'm here to keep you company. How are you feeling today? "
        else:
            message += f"{personal_context}How are you and your {self.profile.living_situation} doing today? "
        
        # Add a question about their day
        if current_hour < 12:
            message += "How did you sleep? Ready to start your day?"
        elif current_hour < 17:
            message += "How's your day going so far?"
        else:
            message += "How was your day? I hope it went well!"
        
        self.show_system_notification("Greeting", message)
        self.profile_label.setText(f"Profile: {self.profile.name} ({self.profile.occupation})")

    def getGroqResponse(self, message):
        try:
            # Check for browser commands first (since they're more common)
            browser_response = self.handle_browser_command(message)
            if browser_response:
                return browser_response
            
            # Then check for desktop commands
            desktop_response = self.handle_desktop_command(message)
            if desktop_response:
                return desktop_response
                
            # Only include schedule info if specifically asked about schedule or time
            schedule_info = ""
            if any(word in message.lower() for word in ['schedule', 'time', 'routine']):
                schedule_info = (
                    f"Here is your current schedule:\n"
                    f"- Wake up time: {self.profile.wake_up_time.strftime('%H:%M')}\n"
                    f"- Breakfast time: {self.profile.breakfast_time.strftime('%H:%M')}\n"
                    f"- Lunch time: {self.profile.lunch_time.strftime('%H:%M')}\n"
                    f"- Dinner time: {self.profile.dinner_time.strftime('%H:%M')}\n"
                    f"- Bedtime: {self.profile.bedtime.strftime('%H:%M')}\n"
                )

            context = (
                f"You are RK, a friendly and helpful AI assistant for {self.profile.name}. "
                f"Keep responses conversational and natural, like a friend. "
                f"Current time is {datetime.now().strftime('%H:%M')}. "
                f"{schedule_info}"
            )
            
            # Check for direct schedule queries
            lower_msg = message.lower()
            schedule_keywords = {
                'breakfast': self.profile.breakfast_time,
                'lunch': self.profile.lunch_time,
                'dinner': self.profile.dinner_time,
                'wake': self.profile.wake_up_time,
                'bed': self.profile.bedtime
            }

            # Only respond with time if specifically asked
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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SmartAICompanion()
    window.show()
    sys.exit(app.exec_())
