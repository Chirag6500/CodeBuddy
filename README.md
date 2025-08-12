# CodeBuddy

CodeBuddy is a simple Python script to run code files, detect errors, and provide beginner-friendly explanations and suggested fixes.

## Features

- Detects programming language by file extension
- Runs code and captures errors
- Explains error messages with beginner-friendly descriptions
- Suggests fixes for common syntax errors

## Installation

1. Clone this repository:
git clone https://github.com/yourusername/codebuddy.git
cd codebuddy

2. Create a virtual environment and install dependencies:
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
Set your OpenAI API key as an environment variable:

3. setx OPENAI_API_KEY "your_api_key_here"

4. Run the script with a filename as an argument:
python codebuddy.py test_script.py
It will detect errors in your code and explain them with suggestions.

License
MIT License
