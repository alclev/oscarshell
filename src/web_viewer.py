import webview
import threading
import sys
import os
from ai_obj import OpenAI_obj

sys.stderr = open(os.devnull, 'w')

# HTML Template for WebView
html_template = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>OpenAI Stream</title>
  <link href="https://fonts.googleapis.com/css?family=Roboto:400,500&display=swap" rel="stylesheet">
  <!-- Marked.js (for Markdown parsing) -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    * {
      box-sizing: border-box;
      font-family: 'Roboto', sans-serif;
    }
    body {
      margin: 0;
      background: #f0f2f5;
      color: #333;
    }
    .container {
      max-width: 800px;
      margin: 2rem auto;
      padding: 1rem;
    }
    h2 {
      text-align: center;
      margin-bottom: 1rem;
    }
    .output {
      background: #fff;
      border-radius: 8px;
      padding: 1.5rem;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      min-height: 300px;
      overflow-y: auto;
    }
    #outputText {
      margin: 0;
    }
    /* Basic styling for any Markdown elements */
    #outputText p {
      margin: 0.5em 0;
      line-height: 1.5;
    }
    #outputText h1, #outputText h2, #outputText h3 {
      margin: 1em 0 0.5em;
    }
    #outputText ul {
      margin-left: 1.5em;
    }
    .input-group {
      display: flex;
      margin-top: 1rem;
    }
    .input-group input {
      flex: 1;
      padding: 0.75rem;
      border: 1px solid #ccc;
      border-right: none;
      border-radius: 4px 0 0 4px;
      outline: none;
      font-size: 1rem;
    }
    .input-group button {
      padding: 0.75rem 1.5rem;
      border: none;
      background: #007bff;
      color: #fff;
      font-size: 1rem;
      cursor: pointer;
      border-radius: 0 4px 4px 0;
      transition: background 0.3s;
    }
    .input-group button:hover {
      background: #0056b3;
    }

    /* Code block styling */
    .code-container {
      position: relative;
      background-color: #f7f7f7;
      border-radius: 8px;
      padding: 1em;
      margin: 1em 0;
      font-family: "Roboto Mono", monospace;
      line-height: 1.5;
    }
    .copy-button {
      position: absolute;
      top: 0.5em;
      right: 0.5em;
      background: #eee;
      border: none;
      cursor: pointer;
      padding: 0.3em 0.6em;
      border-radius: 4px;
      font-size: 0.85rem;
    }
    .copy-button:hover {
      background: #ccc;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>Live OpenAI Stream</h2>
    <div class="output">
      <!-- We'll place parsed markdown here -->
      <div id="outputText"></div>
    </div>
    <div class="input-group">
      <input type="text" id="userInput" placeholder="Type your message here..." />
      <button onclick="sendInput()">Send</button>
    </div>
  </div>

  <script>
    // Keep a global variable to store all text so far
    let cumulativeText = "";

    // Configure marked for nicer line breaks, etc.
    marked.setOptions({
      breaks: true,         // Convert line breaks into <br>
      mangle: false         // (Optional) Avoid changing email-like text
    });

    // Convert raw text to HTML with Marked.
    // Then wrap code blocks with .code-container and a copy button.
    function parseAndFormat(rawText) {
      // Convert to HTML with Marked
      let html = marked.parse(rawText);

      // Use a DOM parser to manipulate the generated HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');

      // For each <code> block inside a <pre>, wrap it in our custom container
      doc.querySelectorAll('pre > code').forEach(codeElem => {
        const preElem = codeElem.parentElement;

        // Create our container
        const container = doc.createElement('div');
        container.classList.add('code-container');

        // Create the copy button
        const copyBtn = doc.createElement('button');
        copyBtn.classList.add('copy-button');
        copyBtn.innerText = 'Copy';
        copyBtn.setAttribute('onclick', 'copyCode(this)');

        // Move the <pre> block into the container
        container.appendChild(copyBtn);
        container.appendChild(preElem.cloneNode(true));

        // Replace the old <pre> with our new container
        preElem.replaceWith(container);
      });

      // Return the modified HTML
      return doc.body.innerHTML;
    }

    // Appends new content to the #outputText div by re-rendering everything so far
    function appendText(newChunk) {
      const outputDiv = document.getElementById('outputText');
      // Accumulate the new chunk into our total text
      cumulativeText += newChunk;
      // Convert the entire cumulative text to Markdown, then HTML, then add copy buttons for code
      const formatted = parseAndFormat(cumulativeText);
      // Replace everything in outputText with the newly formatted text
      outputDiv.innerHTML = formatted;
      // Scroll to bottom after rendering
      window.scrollTo(0, document.body.scrollHeight);
    }

    // Copy code to clipboard with fallback for older browsers or non-secure contexts
    function copyCode(button) {
      const codeElement = button.parentElement.querySelector("code");
      if (!codeElement) {
        console.error("No <code> element found in parent container.");
        return;
      }
      const codeToCopy = codeElement.innerText;

      if (navigator.clipboard && window.isSecureContext) {
        // Modern method
        navigator.clipboard.writeText(codeToCopy)
          .then(() => {
            button.innerText = "Copied!";
            setTimeout(() => {
              button.innerText = "Copy";
            }, 2000);
          })
          .catch((err) => {
            console.error("Failed to copy text: ", err);
            button.innerText = "Error";
            setTimeout(() => {
              button.innerText = "Copy";
            }, 2000);
          });
      } else {
        // Fallback for non-secure contexts or older engines
        const textArea = document.createElement("textarea");
        textArea.value = codeToCopy;
        textArea.style.position = "fixed";  // avoid scrolling
        textArea.style.opacity = 0;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
          document.execCommand('copy');
          button.innerText = "Copied!";
          setTimeout(() => {
            button.innerText = "Copy";
          }, 2000);
        } catch (err) {
          console.error("Failed to copy text: ", err);
          button.innerText = "Error";
          setTimeout(() => {
            button.innerText = "Copy";
          }, 2000);
        }
        document.body.removeChild(textArea);
      }
    }

    // Send user input to Python
    function sendInput() {
      const inputEl = document.getElementById('userInput');
      const inputValue = inputEl.value;
      if (inputValue.trim() !== "") {
        window.pywebview.api.receive_input(inputValue);
        inputEl.value = "";
      }
    }

    // Allow Enter key to send message
    document.getElementById('userInput').addEventListener('keydown', function(event) {
      if (event.key === "Enter") {
        event.preventDefault();
        sendInput();
      }
    });
  </script>
</body>
</html>
"""

window = None  # Global reference for WebView window

def send_to_window(text):
    """Send content dynamically to the WebView UI."""
    global window
    if window:
        # Evaluate JavaScript to call our appendText function in the browser
        window.evaluate_js(f'appendText({repr(text)})')
    else:
        print("WebView is not initialized yet.")

class Api:
    def __init__(self, config, read_fd):
        self.ai_obj = OpenAI_obj(config, read_fd)

    def receive_input(self, text):
        # Show user input in the UI (just prepend some markdown formatting)
        send_to_window(f"\n\n**User Input:** {text}\n")
        # Pass input to your AI object
        self.ai_obj.update_user_input(text)
        # Stream back AI output in chunks; each chunk calls send_to_window
        self.ai_obj.ref_ai(shell=None, user_input=text, chunk_callback=send_to_window)

def webview_run(config, read_fd):
    global window
    api = Api(config, read_fd)

    window = webview.create_window(
        "Oscar's Shell",
        html=html_template,
        js_api=api
    )
    webview.start()
