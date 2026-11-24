# Programming Error Explanation System

**Explaining, Not Just Fixing: Classifying and Teaching Through Programming Errors**

## About the Project

The Programming Error Explanation System (PEES) is a web-based learning application designed to help students understand programming errors instead of simply correcting them.

It analyzes submitted code, identifies programming errors, classifies them, and provides explanations to help learners understand what went wrong.

The system also includes practice activities that allow students to improve their programming and debugging skills.

## Features

### 1. Code Analysis
- Submit code for analysis through the web interface.
- Identify syntax and runtime errors.
- Detect supported logical errors using expected output.
- Identify the programming language and relevant error line.
- Display error messages and explanations.

### 2. Error Explanation
- Explain why an error occurs.
- Help students understand the underlying programming concept.
- Present error information in a learner-friendly format.

### 3. Progressive Hints
- Provide hints to guide students towards understanding an error.
- Support step-by-step problem-solving rather than immediately revealing a correction.

### 4. Practice Section

The application includes two practice modes:

**Write the Code**
- Generate programming exercises based on selected topics.
- Allow students to write their own code.
- Check submitted answers.

**Spot the Error**
- Present code snippets containing programming mistakes.
- Allow students to identify the error type.
- Provide an option to specify the error line.
- Check submitted answers and display feedback.

### 5. Learning Topics

Practice exercises cover topics such as:
- Variables and variable definition
- List indexing
- Arithmetic and safe division
- Conditions
- Loops
- Strings
- Accumulating values
- Logical thinking

### 6. Multiple Language Options

The application currently detects Python and Java as available for code analysis.

C and C++ are listed in the language selection, but their execution requires GCC and G++ compilers to be installed and configured.

## Technology Stack

- **Programming Language:** Python
- **Backend:** Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Testing:** Python unittest

## Running the Project

Clone the repository:

```bash
git clone https://github.com/Lavina-04/Programming-Error-Explanation-System.git
```

Navigate to the project directory:

```bash
cd Programming-Error-Explanation-System
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5001
```

## Running Tests

Run the automated test suite:

```bash
python -m unittest discover -s tests -t .
```

The current test suite contains 48 tests, with 9 skipped in the latest recorded run.

## Project Objective

The objective of PEES is to make programming error analysis more understandable and educational for students.

Rather than focusing only on fixing code, the system encourages learners to identify mistakes, understand their causes, and develop better debugging skills.
