import subprocess
import shlex
import threading
import os
import json
from file_manager import file_manager

# List of dangerous commands or patterns we want to avoid
DANGEROUS_PATTERNS = ["rm ", "mv ", ">", ">>", "|", ";", "&", "$( ", "`", "wget", "curl"]

class ScanEngine:
    """
    Main scanner and agent logic.
    
    Callbacks:
    - output_cb: prints output to the console
    - done_cb: called when scanning stops
    - ai_query_cb: queries the AI provider
    - confirm_cb: asks the GUI/user to confirm command execution
    """

    def __init__(self, output_cb, done_cb, ai_query_cb=None, confirm_cb=None):
        self._output_cb   = output_cb
        self._done_cb     = done_cb
        self._ai_query_cb = ai_query_cb   # lambda prompt: str
        self._confirm_cb  = confirm_cb    # lambda cmd: bool
        self._running     = False
        self._process     = None
        self._thread      = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, ip: str, mask: str, details: str, tool_vars: dict):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._scan_loop,
            args=(ip, mask, details, tool_vars),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._process and self._process.poll() is None:
            self._process.kill()

    def _scan_loop(self, ip: str, mask: str, details: str, tool_vars: dict):
        target = f"{ip}/{mask}"
        self._out("=" * 60)
        self._out(f"[*] AGENT SESSION STARTED: {target}")
        self._out("=" * 60)

        history = []
        enabled_tools = [t for t, v in tool_vars.items() if v]
        
        iteration = 1
        max_iterations = 10 # Safety limit

        while self._running and iteration <= max_iterations:
            self._out(f"\n[Iteration {iteration}] Planning next step...")
            
            # 1. PLAN / DECIDE
            prompt = self._build_agent_prompt(target, details, enabled_tools, history)
            try:
                ai_response = self._ai_query_cb(prompt)
                decision = self._parse_ai_decision(ai_response)
            except Exception as e:
                self._out(f"[ERROR] AI planning failed: {e}")
                break

            thought = decision.get("thought", "No specific thought provided.")
            command = decision.get("command", "")
            status = decision.get("status", "continue").lower()

            self._out(f"[AI Thought] {thought}")

            if status == "finished" or not command:
                self._out("\n[✓] AI agent has completed the task.")
                if decision.get("summary"):
                    self._out(f"[Summary] {decision.get('summary')}")
                break

            # 2. CONFIRM
            if self._confirm_cb:
                self._out(f"[?] Requesting permission to run: {command}")
                confirmed = self._confirm_cb(command)
            else:
                confirmed = True # Fallback if no confirm_cb provided

            if not confirmed:
                self._out("[-] Command rejected by user.")
                history.append({
                    "iteration": iteration,
                    "command": command,
                    "result": "Rejected by user"
                })
                iteration += 1
                continue

            # 3. EXECUTE
            if not self._is_safe(command.split()):
                self._out(f"[!] Security Block: Command contains forbidden patterns.")
                result_str = "Execution blocked for security reasons."
            else:
                result = self._run_command(command)
                result_str = (
                    f"Exit Code: {result['exit_code']}\n"
                    f"STDOUT: {result['stdout']}\n"
                    f"STDERR: {result['stderr']}"
                )
            
            # 4. EVALUATE (will happen in next iteration via history)
            history.append({
                "iteration": iteration,
                "command": command,
                "result": result_str
            })
            
            iteration += 1

        if iteration > max_iterations:
            self._out("\n[!] Maximum iterations reached.")

        self._out("\n" + "=" * 60)
        self._out("[*] AGENT SESSION FINISHED")
        self._out("=" * 60)

        self._running = False
        self._done_cb()

    def _build_agent_prompt(self, target, details, enabled_tools, history):
        history_str = ""
        for h in history:
            history_str += f"Iteration {h['iteration']}:\nCommand: {h['command']}\nResult:\n{h['result']}\n---\n"

        prompt = (
            "You are an autonomous Penetration Testing Agent. Your goal is to explore the target and fulfill the user request.\n"
            f"Target: {target}\n"
            f"User Goal: {details}\n"
            f"Available Tools: {', '.join(enabled_tools)}\n\n"
            "History of previous steps:\n"
            f"{history_str if history else 'No steps taken yet.'}\n\n"
            "INSTRUCTIONS:\n"
            "1. Analyze the target and history.\n"
            "2. Decide the NEXT single command to run.\n"
            "3. If you have enough information to fulfill the user goal, set status to 'finished'.\n"
            "4. Respond ONLY with a valid JSON object in this format:\n"
            "{\n"
            "  \"thought\": \"Reasoning for this step\",\n"
            "  \"command\": \"The shell command to execute\",\n"
            "  \"status\": \"continue\" or \"finished\",\n"
            "  \"summary\": \"(Only if finished) A brief summary of findings\"\n"
            "}\n"
            "IMPORTANT: Do not include markdown formatting or backticks around the JSON. Provide only the raw JSON string."
        )
        return prompt

    def _parse_ai_decision(self, text):
        text = text.strip()
        # Remove potential markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```json"):
                text = "\n".join(lines[1:-1])
            else:
                text = "\n".join(lines[1:-1])
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON-like structure if it's buried in text
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
            raise ValueError(f"Failed to parse AI response as JSON: {text}")

    def _is_safe(self, cmd_list: list) -> bool:
        cmd_str = " ".join(cmd_list).lower()
        for pattern in DANGEROUS_PATTERNS:
            if pattern in cmd_str:
                return False
        return True

    def _run_command(self, command: str) -> dict:
        self._out(f"\n[+] EXECUTING: {command}")
        self._out("-" * 48)
        
        cmd = shlex.split(command)
        
        # File manager registration
        for i, arg in enumerate(cmd):
            if arg.startswith("-o") and len(arg) > 2:
                if i + 1 < len(cmd): file_manager.register_creation(cmd[i+1])
            elif arg in ["-oN", "-oX", "-oG", "-oA"]:
                if i + 1 < len(cmd): file_manager.register_creation(cmd[i+1])

        stdout_lines = []
        stderr_lines = []
        exit_code = -1

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Helper to read stream and output
            def read_stream(stream, lines, is_stderr=False):
                for line in iter(stream.readline, ""):
                    if not self._running:
                        break
                    stripped = line.rstrip()
                    lines.append(stripped)
                    prefix = "[STDERR] " if is_stderr else ""
                    self._out(prefix + stripped)
                stream.close()

            t1 = threading.Thread(target=read_stream, args=(self._process.stdout, stdout_lines))
            t2 = threading.Thread(target=read_stream, args=(self._process.stderr, stderr_lines, True))
            t1.start()
            t2.start()
            
            t1.join()
            t2.join()
            
            if self._running:
                exit_code = self._process.wait()
            else:
                self._process.kill()
                exit_code = -9
                
        except FileNotFoundError:
            err = f"Command not found: {cmd[0]}"
            self._out(f"[ERROR] {err}")
            stderr_lines.append(err)
        except Exception as e:
            self._out(f"[ERROR] {e}")
            stderr_lines.append(str(e))
            
        return {
            "stdout": "\n".join(stdout_lines),
            "stderr": "\n".join(stderr_lines),
            "exit_code": exit_code
        }

    def _out(self, text: str):
        self._output_cb(text)

