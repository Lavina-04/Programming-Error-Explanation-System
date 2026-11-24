# Programming Error Explanation System (PEES)

### Explaining, Not Just Fixing — Helping Students Understand Their Programming Mistakes

PEES (Programming Error Explanation System) is an educational programming assistance platform designed to help students understand, identify, and learn from programming errors.

Instead of simply displaying technical compiler messages or providing corrected code, PEES focuses on explaining why an error occurs, identifying its category, guiding students through progressive hints, and strengthening their programming knowledge through interactive practice.

The system provides a unified environment for analysing and practising programs written in Python, Java, C, and C++.

---

## 1. Problem Statement

Programming beginners frequently struggle to understand compiler errors, runtime exceptions, and logical mistakes. Traditional development environments often display technical error messages that are difficult for students to interpret.

Most automated code-fixing tools focus on correcting code rather than explaining the underlying programming concepts.

PEES addresses this problem by focusing on error identification, classification, explanation, and learning.

## 2. Project Objectives

- Identify common programming errors.
- Classify errors into meaningful categories.
- Display relevant error messages and line references.
- Explain why an error occurs in understandable language.
- Provide progressive hints to encourage independent debugging.
- Improve programming knowledge through interactive exercises.
- Support multiple programming languages through a unified interface.

## 3. Key Features

### 3.1 Code Analysis

Students can submit source code and analyse it through the platform.

Features include:
- Programming language selection.
- Code compilation and execution where supported.
- Syntax and compilation error detection.
- Runtime error identification.
- Logical error checking using expected output.
- Error classification and line references.
- Structured explanations of identified errors.

### 3.2 Error Explanation Engine

The explanation engine focuses on helping students understand the cause of programming mistakes.

It provides structured explanations covering:
- What went wrong.
- Why the error occurred.
- Where the problem is located.
- Which programming concept is involved.

### 3.3 Progressive Hint System

Instead of immediately revealing the complete solution, PEES provides hints progressively.

This approach encourages students to:
- Understand the problem independently.
- Identify mistakes step by step.
- Develop debugging skills.
- Learn the concepts behind programming errors.

### 3.4 Interactive Practice Module

PEES includes interactive exercises to strengthen programming fundamentals.

**Write the Code**

Students receive a programming problem and write their own code to solve it.

**Spot the Error**

Students examine a program containing an error, identify the mistake, and select its relevant category and line.

### 3.5 Multi-Language Support

PEES supports four programming languages:

| Language | Execution Environment |
|---|---|
| Python | Python Interpreter |
| Java | Java Compiler and Runtime |
| C | GCC Compiler |
| C++ | G++ Compiler |

## 4. Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| Python Execution | Python Interpreter |
| Java Execution | JDK |
| C Compilation | GCC |
| C++ Compilation | G++ |
| Testing | Python unittest |
| Development Environment | Visual Studio Code |

---

## 5. System Workflow

1. Student opens the PEES application.
2. Student selects a programming language.
3. Student enters or submits source code.
4. The system analyses, compiles, or executes the program.
5. Identified errors are classified into relevant categories.
6. The system displays error information, line references, and explanations.
7. Students can request progressive hints to understand the issue.
8. Students can strengthen their programming knowledge through interactive exercises.

---

## 6. Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- Java Development Kit (JDK)
- GCC and G++ for C and C++ support

### Step 1: Clone the Repository

```bash
git clone https://github.com/Lavina-04/Programming-Error-Explanation-System.git
```

Navigate to the project directory:

```bash
cd Programming-Error-Explanation-System
```

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure C and C++ Compilers on Windows

PEES uses GCC and G++ through the MSYS2 UCRT64 toolchain.

Install MSYS2 from:

https://www.msys2.org/

Open the MSYS2 UCRT64 terminal and execute:

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-gcc
```

Add the following directory to the Windows PATH environment variable:

```text
C:\msys64\ucrt64\bin
```

Verify the installation:

```bash
gcc --version
g++ --version
```

### Step 5: Verify Java Installation

```bash
java --version
javac --version
```

### Step 6: Run the Application

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5001
```

---

## 7. Running Automated Tests

PEES includes automated tests for different application components.

Run the test suite from the project root:

```bash
python -m unittest discover -s tests -t .
```

The test suite covers:
- Core analysis functionality.
- API behaviour.
- Error explanations.
- Programming language handling.

The latest recorded test run completed 48 tests, with 9 skipped. Test results may depend on the available environment and installed language tools.

---

## 8. Current Limitations

- Error detection depends on the capabilities of the relevant language analyzer and compiler.
- Logical errors require expected output or another basis for comparison.
- Explanations currently use structured, rule-based logic; external LLM/API integration is not yet implemented.
- Compiler-dependent features require the appropriate compiler or runtime to be installed.
- Secure execution isolation is necessary before deploying the application as a public code-execution service.

---

## 9. Future Enhancements

- LLM-powered contextual programming explanations.
- More advanced error classification.
- Improved logical error detection.
- Personalised learning paths.
- Student performance tracking and analytics.
- Expanded programming practice questions.
- Additional programming language support.
- VS Code extension integration.

---

## 10. Project Information

| Detail | Information |
|---|---|
| Project Name | Programming Error Explanation System (PEES) |
| Project Type | Final-Year B.Tech CSE Project |
| Developer | Lavina Solanki |
| Institution | Bikaner Technical University |

---

**PEES — Understand the Error. Learn the Concept. Improve Your Code.**
