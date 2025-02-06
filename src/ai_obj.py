import logging
import os
import threading
import json
from openai import OpenAI

HIST_THRESH = 10

logging.basicConfig(
    filename="logs/ai_reference.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


class OpenAI_obj:
    def __init__(self, config, read_fd):
        logger.debug(f"api key: {config["api_key"]}\tmodel: {config["model"]}")
        self.client = OpenAI(api_key=config["api_key"])
        self.history = []
        self.current_output = ""
        self.user_input = ""
        self.config = config

        self.polling = True
        self.pipe = os.fdopen(read_fd, "r", buffering=1)
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        logger.info("Starting blocking read loop")
        while self.polling:
            line = self.pipe.readline()  # Blocks until a line is available.
            if not line:                  # EOF reached.
                break
            try:
                data = json.loads(line)
                logger.info(f"Data RECEIVED: {data}")
                self.update_state(data)
            except json.JSONDecodeError as e:
                logger.error("Error decoding JSON: %s", e)
        logger.info("Exiting read loop")

    def update_state(self, data):
        """Update the object's state with the incoming JSON data."""
        self.history = data["history"]
        self.current_output = data["stdout"]
        logger.info(f"Updating state:\nHistory:{self.history}\nStdout:{self.current_output}")

    def stop(self):
        """Stop the polling thread and close the pipe."""
        logger.debug("Stop polling the input pipe")
        self.polling = False
        self.pipe.close()
        self.thread.join()
        logger.info("Polling stopped.")

    def update_user_input(self, user_input):
        logger.debug(f"User input updated to: {user_input}")
        self.user_input = user_input

    def ref_ai(self, shell, user_input, chunk_callback=None):
        logger.debug(
            f"API_CALL:\nUser input: {user_input}\nZsh history: {self.history}\nCurrent stdout: {self.current_output}"
        )

        stream = self.client.chat.completions.create(
            model=self.config["model"],
            messages=[
                {
                    "role": "system",
                    "content": "You are a Zsh assistant. Based on a Zsh command history, the current stdout, and the user input, make detailed expertise on how to proceed. Enclose code with ``` for easy parsing."
                },
                {
                    "role": "user",
                    "content": f"User input: {user_input}\nZsh history: {self.history}\nCurrent stdout: {self.current_output}"
                },
            ],
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None) is not None:
                text = delta.content
                if chunk_callback:
                    chunk_callback(text)
