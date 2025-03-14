# AI Personal Assistant - Desktop AI🚀  

A smart AI-powered personal assistant designed to automate tasks, manage schedules, and assist with daily activities.  

## 🛠 Features  
👉 **Voice & Text Interaction** – Chat with your assistant via text or voice  
👉 **Task & Reminder Management** – Set tasks and get notified  
👉 **Desktop & Browser Control** – Open apps, search the web, and more  
👉 **Windows Notifications** – Get system alerts and reminders  

---

## 🔧 Installation  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/anurag-srivatsav/Desktop_AI.git
cd RK_Assistant
```

### 2️⃣ Install Dependencies  
```bash
pip install -r requirements.txt
```

### 3️⃣ Set Up Environment Variables  
Create a `.env` file in the root directory and add your API keys:  
```bash
GROQ_API_KEY=your_groq_api_key

```

### 4️⃣ Run the Application  
```bash
python main.py
```

---

## 💻 Setting Up as a Desktop AI (Auto-Launch on Startup)  
If you want the assistant to start automatically when your PC boots:  

1️⃣ Press `Win + R`, type `shell:startup`, and press Enter.  
2️⃣ Move the `start_assistant.bat` file into this folder.  
3️⃣ Restart your PC, and **Boom! 🎉 Your AI Assistant will launch on startup.**  

---

## 📝 License  
MIT License – Free to use and modify.  

---
# I'll break down this AI Personal Assistant application in detail: 


1. **Technology Stack & Dependencies**:
```python
- PyQt5: For the desktop GUI application
- Speech Recognition: For voice input processing
- pyttsx3: For text-to-speech capabilities
- Groq API: For AI language model responses
- Windows-specific libraries: win32gui, win32con, win32com for system control
- Requests: For API calls
- Various system utilities: webbrowser, subprocess, psutil
```

2. **Core Components**:

A. **User Interface (GUI)**:
- Built with PyQt5
- Dark theme with purple color scheme
- Main features:
  - Chat interface with message history
  - Collapsible sidebar for reminders and schedule
  - System tray integration
  - Profile information display

B. **Voice Assistant**:
- Wake word detection ("Hey Siri", "Hi Siri", etc.)
- Continuous background listening
- Natural speech synthesis with Microsoft Zira voice
- Command processing queue

C. **Profile Management**:
- Stores user information:
  - Personal details (name, occupation)
  - Daily schedule (wake up, meals, bedtime)
  - Living situation
  - Routines and preferences
- Persistent storage in JSON format

D. **Task Management**:
- Categories: study, work, personal, health, shopping, meetings
- Priority levels
- Due dates tracking
- Status management (pending/completed)

3. **Key Features**:

A. **System Control**:
- Application management (open/close apps)
- Volume and brightness control
- Window management (minimize/maximize)
- Spotify integration (play/pause/next/previous)

B. **Browser Automation**:
- Website navigation
- YouTube search
- Flight search (Ixigo integration)
- Maps integration
- Email composition
- Social media posting

C. **Schedule Management**:
- Customizable daily schedule
- Reminder system
- Calendar integration
- Notification system

4. **Workflow**:

A. **Initialization**:
1. Application starts
2. Loads user profile (or starts onboarding)
3. Initializes voice assistant
4. Sets up system tray
5. Starts background listeners

B. **User Interaction Flow**:
1. User can interact through:
   - Text input
   - Voice commands
   - GUI buttons
   - System tray menu

2. Command Processing:
   ```
   User Input → Command Parser → 
   → Desktop Commands
   → Browser Commands
   → AI Response
   → Action Execution
   ```

3. Response Generation:
   ```
   Input → Groq API → 
   → Context Processing →
   → Natural Language Response →
   → Voice/Text Output
   ```

5. **Target Users**:
This application is suitable for:
- Windows PC users
- People who want a personal assistant for daily tasks
- Users who prefer both voice and text interaction
- Students and professionals who need schedule management
- Anyone wanting an AI companion with system control capabilities

6. **System Requirements**:
- Operating System: Windows 10/11
- Python 3.7+
- Internet connection (for AI responses)
- Microphone (for voice commands)
- Speakers (for voice responses)

7. **Key Features for Different User Types**:

A. **Students**:
- Study schedule management
- Assignment reminders
- Research tools access
- Educational website quick access

B. **Professionals**:
- Meeting management
- Email composition
- Professional app control
- Calendar integration

C. **General Users**:
- Entertainment control (Spotify, YouTube)
- System management
- Web browsing
- Daily schedule assistance

8. **Security & Privacy**:
- Local profile storage
- API key security
- System-level permissions
- No cloud storage of personal data

9. **Extensibility**:
The code is modular and can be extended with:
- Additional AI models
- More system controls
- New browser automations
- Custom commands
- Additional UI features

10. **Error Handling**:
- Robust error handling for:
  - Voice recognition
  - API calls
  - System commands
  - File operations
  - User input validation


