import os
import pty
import select
import tty
import sys
import termios
import logging
import re
import json

import tempfile
from pathlib import Path
import tokenize
from io import BytesIO

READ_CHUNK = 1024
OUTPUT_CHUNK = 2048
HISTORY_LIM = 10

# Global configs
logging.basicConfig(
    filename="logs/shell_instance.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)

class Zsh_Shell():

    def __init__(self, pipe_fd):
            self.history = []
            self.current_output = ""
            self.pipe = os.fdopen(pipe_fd, "w", buffering=1)
            logger.debug(f"Establishing pipe with file descriptor: {self.pipe}")

    def process_input(self, data):
        logger.debug(f"Processing user input: {data}")
        if len(self.history) >= HISTORY_LIM: self.history.pop(0)
        if data: self.history.append(data)
        return data  

    def process_output(self, data):
        clean_data = self.clean_output(data)
        self.current_output = clean_data
        logger.debug(f"Processing user output: {clean_data}")
        data_dict = {
            "history" : self.history,
            "stdout" : self.current_output
        }
        data_json = json.dumps(data_dict)
        logger.debug(f"Sending data over pipe: {data_json}")
        self.pipe.write(data_json + '\n')
        self.pipe.flush()
        return data  

    def clean_output(self, raw_output: bytes) -> str:
        logger.debug("Cleaning output...")
        logger.debug(f"Raw bytes: {raw_output}")
        # Convert bytes to a string
        decoded_output = raw_output.decode("utf-8", errors="ignore")
        
        # Remove ANSI escape sequences
        no_ansi = re.sub(r"\x1b\[\??[0-9;]*[a-zA-Z]", "", decoded_output)
        
        # Remove OSC escape sequences (they start with ESC ] and end with BEL)
        no_osc = re.sub(r"\x1b\].*?\x07", "", no_ansi)
        
        # Remove carriage returns and normalize line breaks
        normalized = no_osc.replace("\r", "")
        
        # Remove the shell prompt and command echoes
        cleaned = re.sub(r"\(oscar\).*?%\s*", "", normalized)
        
        # Remove redundant blank lines
        no_blanks = re.sub(r"\n\s*\n", "\n", cleaned).strip()
        
        # Remove redundant spaces
        final_output = re.sub(r"\s+", " ", no_blanks)
        
        # Truncate if necessary
        if len(final_output) >= OUTPUT_CHUNK: final_output = final_output[:OUTPUT_CHUNK]

        return final_output


    def create_temp_rc(self):
        logger.debug("Create temp rc")
        """Create a temporary .zshrc file with a custom PS1."""
        temp_dir = tempfile.TemporaryDirectory()
        temp_zshrc_path = Path(temp_dir.name) / ".zshrc"
        content = ""
        home_dir = os.getenv("HOME")
        curr_zsh = os.path.join(home_dir, ".zshrc")
        with open(curr_zsh, "r") as f:
            content = f.read()
        with open(temp_zshrc_path, "w") as f:
            f.write(content)
            f.write(f'export PS1="(oscar) $PS1"\n')
        return temp_dir

    def interact_with_shell(self):
        logger.debug("Interact with shell, main func")
        # Save the current terminal settings
        original_stdin_settings = termios.tcgetattr(sys.stdin)
        
        # Start a new Bash session
        pid, fd = pty.fork()

        if pid == 0:  # Child process
            # Create a temporary .zshrc with the desired PS1
            temp_dir = self.create_temp_rc()
            # Set ZDOTDIR to the temporary directory
            os.environ["ZDOTDIR"] = temp_dir.name
            # Launch zsh
            os.execvp("zsh", ["zsh", "--login", "-i"])

        else:  # Parent process
            try:
                # Set the parent process terminal to raw mode
                tty.setraw(sys.stdin.fileno())
                temp_dir = None 
                logger.info("Started a new Zsh instance.")
                input_buffer = ""
                output_buffer = b""
                capturing = False

                while True:
                    # Wait for input/output events
                    rlist, _, _ = select.select([fd, sys.stdin.fileno()], [], [])
                    
                    for source in rlist:
                        if source == fd:  # Output from Bash
                            output = os.read(fd, READ_CHUNK)
                            if b"(oscar)" in output and not output_buffer == b'':
                                self.process_output(output_buffer)
                                output_buffer = b""
                                capturing = False
                            if capturing: 
                                output_buffer += output

                            # logger.debug(f"Raw output received: {output}")

                            if not output:
                                logger.info("Shell session ended.")
                                return  # Bash session ended
                            
                            os.write(sys.stdout.fileno(), output)
                            
                        elif source == sys.stdin.fileno():  # User input
                            char = os.read(sys.stdin.fileno(), 1).decode(errors="replace")  # Read a single character
                            if char == "\r":  # Enter key
                                os.write(fd, ("\n").encode())
                                self.process_input(input_buffer)  
                                capturing = True
                                input_buffer = ""
                            elif char in ("\x7f", "\b"):  # Backspace handling
                                if len(input_buffer) > 0:
                                    input_buffer = input_buffer[:-1]  # Remove the last character from the buffer
                                    # Send a backspace sequence to the terminal for visual feedback
                                    os.write(fd, b"\b \b")
                            else:
                                input_buffer += char  # Append the character to the buffer
                                # Instead of sending the character to the shell, write it to the terminal for echo
                                os.write(fd, char.encode())

            except Exception as e:
                logger.error(f"An error occurred: {e}")
            finally:
                if self.pipe:
                    self.pipe.close()
                    logger.info("Closing pipe.")
                # Restore the original terminal settings
                
                if not sys.stdin.isatty():
                    logger.error("sys.stdin is not a TTY!")
                else:
                    termios.tcsetattr(fd, termios.TCSADRAIN, original_stdin_settings)
                    logger.info("Terminal settings restored.")
                # Cleanup the temporary directory
                if temp_dir:
                    temp_dir.cleanup()
                    logger.info("Temporary directory cleaned up.")
                os.close(fd)
                logger.info("Shell session closed.")
    
if __name__ == '__main__': 
    pipe_fd = int(os.environ.get("WRITE_FD"))
    shell = Zsh_Shell(pipe_fd)
    shell.interact_with_shell()