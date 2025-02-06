# Oscar's Shell

Oscar's Shell is an interactive AI-powered shell assistant designed to run within a Zsh instance. It leverages a pseudoterminal (PTY) to provide real-time assistance and feedback by linking the shell with an AI assistant. This integration is achieved using inter-process communication (IPC), allowing seamless interaction between the shell and the AI assistant.

## Features
- **Real-time AI Assistance**: Get instant feedback and recommendations from the AI assistant while working in the shell.
- **Seamless Integration with Zsh**: Designed specifically for Zsh users to enhance productivity.
- **Interactive PTY Support**: The shell and AI communicate through a pseudoterminal for a responsive experience.
- **Customizable AI Model**: Configure your preferred AI model and API key in `config.json`.
- **Cross-Platform GUI**: The AI assistant window is powered by `tk` and `pywebview` for a smooth user experience.

## Requirements
Ensure you have the following dependencies installed:
```
openai
tk
pywebview
```

## Setup
Oscar's Shell is specifically designed for use with the **Zsh** shell.

### Installation
1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Set up a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```sh
   pip3 install -r requirements.txt
   ```

## Configuration
Before running Oscar's Shell, configure your AI model and API key:
1. Open `config.json`
2. Set your API key and model preferences

Example:
```json
{
    "api_key": "your_openai_api_key",
    "model": "stream-enabled model"
}
```

## Usage
To start the interactive AI-powered shell:
```sh
python3 src/main.py
```

Once launched, the AI assistant window will open alongside the shell, allowing real-time interaction and feedback while executing commands.

## Contribution
Contributions are welcome! If you’d like to enhance the project, feel free to submit pull requests or report issues.

## Disclaimer
This project is provided "as is" without any warranty or guarantee. Use at your own discretion.

---

For further improvements or support, feel free to open an issue in the repository!


