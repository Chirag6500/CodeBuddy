import sys
import subprocess
import tempfile
import os
from colorama import Fore, Style, init
from openai import OpenAI

# Initialize colorama
init(autoreset=True)

# Try to get API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# Common offline explanations & fixes
OFFLINE_FIXES = {
    "SyntaxError: expected ':'": (
        "You probably forgot a colon (:) at the end of a statement like for, if, while, or def.",
        "Add a colon at the end of the statement. Example:\nfor i in range(5):"
    ),
    "IndentationError:": (
        "Python relies on indentation (spaces or tabs). Make sure your code blocks are properly indented.",
        "Indent the lines that belong to the same block with the same number of spaces."
    ),
    "NameError:": (
        "You’re trying to use a variable or function that hasn’t been defined yet.",
        "Make sure you define the variable or function before using it."
    ),
    "TypeError:": (
        "You’re using a value in a way that’s not allowed for its type (e.g., adding a string to a number).",
        "Check the types of your variables and use them in compatible operations."
    )
}

def detect_language_from_extension(filename):
    ext_map = {
        ".py": "Python",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".js": "JavaScript"
    }
    _, ext = os.path.splitext(filename)
    return ext_map.get(ext, "Unknown")

def run_code(language, filepath):
    try:
        if language == "Python":
            result = subprocess.run(["python", filepath],
                                    capture_output=True, text=True, timeout=5)
        elif language == "Java":
            subprocess.run(["javac", filepath], capture_output=True, text=True)
            result = subprocess.run(["java", filepath.replace(".java", "")],
                                    capture_output=True, text=True, timeout=5)
        elif language in ["C", "C++"]:
            exe_file = tempfile.mktemp()
            compiler = "gcc" if language == "C" else "g++"
            subprocess.run([compiler, filepath, "-o", exe_file],
                           capture_output=True, text=True)
            result = subprocess.run([exe_file], capture_output=True, text=True, timeout=5)
        else:
            return None
        return result
    except subprocess.TimeoutExpired:
        return None

def explain_and_fix(error_msg, filepath):
    # First try offline match
    for key, (explanation, fix) in OFFLINE_FIXES.items():
        if key in error_msg:
            return explanation, fix, None

    # If API key is set, use OpenAI
    if client:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code_content = f.read()
            prompt = f"""
            The following code has an error:
            {code_content}

            Error:
            {error_msg}

            Please:
            1. Explain the error in beginner-friendly language.
            2. Provide a corrected version of the code.
            """
            ai_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = ai_response.choices[0].message["content"]

            # Try to extract fixed code from the AI's reply
            fixed_code = None
            if "```" in reply:
                parts = reply.split("```")
                if len(parts) >= 3:
                    fixed_code = parts[1]
                    # Remove language hint if present
                    if fixed_code.strip().startswith(("python", "java", "c", "cpp", "javascript")):
                        fixed_code = "\n".join(fixed_code.split("\n")[1:])

            return None, reply, fixed_code
        except Exception as e:
            return f"Could not get AI explanation: {e}", None, None
    
    return "No explanation available (offline mode).", None, None

def save_fixed_file(original_path, fixed_code):
    base, ext = os.path.splitext(original_path)
    fixed_path = f"{base}_fixed{ext}"
    with open(fixed_path, "w", encoding="utf-8") as f:
        f.write(fixed_code)
    return fixed_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(Fore.YELLOW + "Usage: python codebuddy.py <filename>")
        sys.exit(1)

    filepath = sys.argv[1]
    language = detect_language_from_extension(filepath)
    print(Fore.CYAN + f"[Detected Language] {language}\n")

    result = run_code(language, filepath)

    if result is None:
        print(Fore.RED + "⚠ Could not run code or language not supported.")
    elif result.returncode != 0:
        print(Fore.RED + "[Error Found]")
        print(result.stderr.strip())
        
        print("\n" + Fore.YELLOW + "[Explanation & Suggested Fix]")
        explanation, fix, fixed_code = explain_and_fix(result.stderr, filepath)
        if explanation:
            print(Fore.YELLOW + explanation)
        if fix:
            print(Fore.GREEN + "\nSuggested fix:\n" + fix)
        if fixed_code:
            fixed_path = save_fixed_file(filepath, fixed_code)
            print(Fore.CYAN + f"\n💾 Fixed version saved to: {fixed_path}")
    else:
        print(Fore.GREEN + "✅ No errors found. Code ran successfully!")
        print(result.stdout)

