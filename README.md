# PyQtChat - Desktop AI Chatbot Application

A modern BYOK desktop chatbot application that provides a unified interface for interacting with multiple AI providers. Using LiteLLM, you can access various providers; including OpenAI, Anthropic, Google, and OpenRouter.

![PyQtChat](https://img.shields.io/badge/Python-3.7%2B-blue.svg)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg)
![LiteLLM](https://img.shields.io/badge/AI-LiteLLM-orange.svg)

https://github.com/user-attachments/assets/57236e75-648f-4fa9-8dbc-af54cef43487

![pqi1](https://github.com/user-attachments/assets/1c817589-efaa-464b-a935-75f8009be134)
![pqi2](https://github.com/user-attachments/assets/0a01b5b4-b651-4bb4-bf86-d603d361d843)

## Features

### Multi-Provider AI Support
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4.1 series
- **Anthropic**: Claude 3.5 Sonnet, Claude Opus 4, Claude Sonnet 4
- **Google**: Gemini 2.5 Pro/Flash Preview
- **OpenRouter**: Access to 100+ models through a single API
- **Custom Models**: Add your own LiteLLM-compatible models

### Advanced Chat Interface
- **Multi-Tab Support**: Manage multiple conversations simultaneously
- **Message Editing**: Edit and resend previous messages
- **Markdown Rendering**: Rich text formatting with syntax highlighting
- **Cost Tracking**: Real-time cost calculation per message and session
- **Auto-scroll**: Smooth conversation flow
- **Timestamps**: Optional message timestamps

### Customization & Themes
- **Dark/Light Mode**: Toggle between themes
- **Adjustable Font Size**: Scale interface text
- **Responsive Layout**: Resizable panels and windows
- **Window State Persistence**: Remembers size and position

### Import/Export
- **Multiple Formats**: JSON, Markdown, Plain Text
- **Conversation History**: Save and restore chat sessions
- **Cross-Platform**: Compatible export formats

### Configuration
- **Settings Dialog**: Centralized configuration management
- **Environment Variables**: Support for `.env` files
- **API Key Management**: Storage with QSettings
- **Custom API Endpoints**: Support for self-hosted models

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Windows, macOS, or Linux *(There might be problems with macOS or Linux options as this project was made on Windows and not really tested on other platforms)*
- Preferably use a Conda environment

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai_chatbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

### First Setup

1. **Configure API Keys**:
   - Open `Settings -> Preferences -> API Keys`
   - Add your API keys for desired providers
   - Alternatively, create a `.env` file with:
     ```
     OPENAI_API_KEY=your_openai_key
     ANTHROPIC_API_KEY=your_anthropic_key
     GEMINI_API_KEY=your_google_key
     OPENROUTER_API_KEY=your_openrouter_key
     ```
     *also works for the prebuilt executable*

2. **Select a Model**:
   - Choose a provider from the dropdown
   - Select your preferred model
   - View cost information in the control panel

3. **Start Chatting**:
   - Type your message in the input field
   - Press Enter or click "Send"
   - Enjoy the conversation!

## Configuration

### Settings Dialog
Access via `Settings → Preferences` or `Ctrl+,`:

#### API Keys Tab
- Configure API keys for all supported providers
- Environment variables take precedence over stored keys

#### Custom Models Tab
- Add custom LiteLLM-compatible models
- Format: `provider/model-name`
- Examples:
  ```
  openrouter/microsoft/wizardlm-2-8x22b
  ollama/llama3
  together_ai/meta-llama/Meta-Llama-3-8B-Instruct
  ```

#### Appearance Tab
- **Dark Mode**: Toggle between light and dark themes
- **Font Size**: Adjust interface font size

#### Chat Tab
- **Auto Scroll**: Automatically scroll to new messages
- **Show Timestamps**: Display message timestamps
- **Max Tokens**: Set maximum response length (1-10000)

## Usage Guide

### Basic Operations

#### Starting a New Chat
- Click "New Chat" in the sidebar
- Or use `Ctrl+N` (if implemented)

#### Managing Conversations
- **Rename**: Right-click tab → Rename or press `F2`
- **Delete**: Right-click tab → Delete or press `Ctrl+D`
- **Clear**: Use "Clear Chat" button (confirms before clearing)

#### Message Operations
- **Edit**: Click "Edit" on any user message
- **Resend**: Click "Resend" to retry with same message
- **Copy**: Click "Copy" to copy message to clipboard

#### Import/Export
- **Export**: `File → Export Chat` or `Ctrl+E`
- **Import**: `File → Import Chat` or `Ctrl+I`
- Supported formats: JSON, Markdown, Text

### Keyboard Shortcuts
- `Ctrl+,`: Open Settings
- `Ctrl+T`: Toggle Theme
- `Ctrl+E`: Export Current Chat
- `Ctrl+I`: Import Chat
- `Ctrl+D`: Delete Current Chat
- `Ctrl+N`: Create a New Chat
- `F2`: Rename Current Chat
- `Ctrl+Q`: Exit Application
- `Enter`: Send Message

### Cost Tracking
- Real-time cost calculation per message
- Session total displayed in info bar
- Supports all major model pricing
- Estimates based on LiteLLM cost database

## Building

### Development Build
```bash
dev_build.bat
```

### Production Build
```bash
build.bat
```

The executable will be created in `dist/` directory.

## Project Structure

```
ai_chatbot/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── build.bat              # Production build script
├── dev_build.bat          # Development build script
├── core/                  # Core application logic
│   ├── app_setup.py       # Application initialization
│   ├── chat_worker.py     # AI chat worker thread
│   ├── models.py          # Model management
│   └── settings.py        # Settings management
├── ui/                    # User interface components
│   ├── main_window.py     # Main application window
│   ├── chat_tab.py        # Individual chat tab
│   ├── chat_message.py    # Message display widget
│   └── settings_dialog.py # Settings configuration dialog
├── utils/                 # Utility modules
│   ├── cost_tracker.py    # Cost calculation utilities
│   ├── export.py          # Import/export functionality
│   ├── logger.py          # Logging configuration
│   ├── style_manager.py   # Theme and styling
│   └── window_utils.py    # Window state management
├── resources/             # Application resources
│   ├── icon.ico           # Application icon
│   ├── styles.css         # Light theme styles
│   └── styles_dark.css    # Dark theme styles
└── logs/                  # Application logs (auto-created)
```

## Troubleshooting

### Common Issues

#### API Key Invalid
- Verify API keys in Settings
- Try to create an `.env` file with relevant variables

#### Model not found
- Verify model name in provider documentation
- Check if model requires special access
- Try a different model from the same provider

#### Cost tracking unavailable
- With LiteLLM, OpenRouter models are missing cost data
- Some custom models may also not have cost data

#### Font/Display Issues
- Try adjusting font size in Settings
- Toggle between light/dark mode
- Restart application after theme changes

### Logging
- Logs are stored in `logs/` directory
- Daily log rotation with format: `chatbot_YYYYMMDD.log`
- Log level: INFO (console and file)
- If using prebuilt executable, logs will be found at `%Temp%/_MEIxxxxxx/logs` on Windows, where `xxxxxx` is a random number.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Create an issue for bug reports
- Check existing issues before creating new ones
- Include logs and system information in bug reports

---

**Made with ❤️ by [Starosti](https://github.com/Starosti/)**
