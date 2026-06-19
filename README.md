# Aegix

**Aegix** is an autonomous penetration testing agent interface designed to assist security professionals in automated network exploration, vulnerability scanning, and security assessment. Featuring a modern graphical user interface and utilizing advanced Large Language Models (LLMs), Aegix plans, confirms, executes, and evaluates security commands in a safe, controlled manner.

---

## Academic Notice
This application was developed by **Dávid Sventek** as an **Engineering Project** at the **Department of Information Networks (KIS)**, **Faculty of Management Science and Informatics (FRI)**, **University of Žilina (UNIZA)**, Slovakia.

---

## Key Features

- **Autonomous Agent Mode**: Set target IP addresses and network masks, provide custom assessment details, and let the AI agent iteratively analyze, plan, and execute scan sequences.
- **Dual AI Provider Support**:
  - **Groq API**: High-speed cloud-based inference using Llama models.
  - **Ollama**: Local, offline LLM processing to maintain maximum security and privacy.
- **Security & Safety Safeguards**:
  - Built-in command validation to prevent the execution of destructive or unauthorized patterns (e.g., `rm`, `mv`, redirection blocks).
  - High-impact or complex commands must be confirmed via interactive prompt before they are executed.
- **Integrated Interactive AI Chat**: Chat in real-time with an AI assistant specialized in security operations.
- **Secure Key Encryption**: Sensitive credentials (such as Groq API keys) are safely encrypted and decrypted locally using the AES-256 (Fernet) algorithm.
- **Workspace Tracker & File Manager**: Automatically registers and tracks files/directories generated during scans for clean execution and safe removal.
- **Localization**: Native support for English (EN) and Slovak (SK) language toggles.

---

## Project Architecture

The codebase is modular and structured as follows:

- **`main.py`**: The application entry point. Handles X11 forwarding validation and initiates the graphical interface.
- **`GUI.py`**: The main user interface, developed using `customtkinter`. Controls menus, settings, terminal consoles, and interactive windows.
- **`scanner.py`**: The background scanning loop engine. Manages AI communication, handles shell execution, tracks process output logs in real-time, and applies safety constraints.
- **`ai_engine.py`**: Handles API requests to either Groq or Ollama endpoints, parsing responses cleanly.
- **`config.py`**: Manages the JSON configuration file (`config.json`) and handles AES-based cryptography to store sensitive API keys securely.
- **`file_manager.py`**: Safely tracks and deletes files created by testing tools, keeping the environment clean.
- **`lang.py`**: Simple translation management interface.

---

## Prerequisites & Dependencies

To run Aegix locally, you need **Python 3.8+** installed. The application depends on the following libraries:

- `customtkinter` (for the modern dark/light GUI)
- `cryptography` (for secure API key storage)
- `requests` (for calling Groq and Ollama APIs)

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Pentester
   ```

2. **Install dependencies:**
   You can install the required packages using `pip`:
   ```bash
   pip install customtkinter cryptography requests
   ```

3. **Configure the AI provider:**
   Make sure either Ollama is running locally or you have a valid Groq API key.
   - For **Groq**: Obtain your key from the Groq console.
   - For **Ollama**: Ensure your local instance is active (typically on port `11434`) and the desired model (e.g., `llama3`) is downloaded.

---

## Usage

Run the main application using:

```bash
sudo python main.py
```

### Quick Guide:
1. **Target Setup**: Fill in the Target IP (e.g., `10.0.0.0`) and Subnet Mask.
2. **Set up your LLM**: in settings configure your LLM for the aplication to communicate with.
3. **Details / Rules**: Write down specific instructions or goals for the agent in the "Details" textbox.
4. **Select Tools**: Check the target tools you want the agent to use (e.g., `nmap`, `enum4linux`, `SQLmap`).
5. **Run Agent**: Click **RUN**.
6. **Confirmation**: When the AI proposes a command, review the pop-up and confirm or decline execution.
