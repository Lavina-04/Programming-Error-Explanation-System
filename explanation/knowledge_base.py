"""Rule-based teaching content, shared across languages.

Each group describes one *concept*. Compiler/interpreter specific error names
are mapped onto groups through ALIASES. Text may contain {placeholders} such as
{container}, {ident}, {line}; they are filled from the real code and error.
`notes` adds language-specific sentences to the explanation.
"""

GROUPS = {
    "index": {
        "concept": "Zero-based indexing",
        "cause": "Your code asked for a position in {a_container} that does not exist.",
        "detail": "Positions in {a_container} are numbered starting from 0, so {a_container} with n items has valid positions 0 to n-1.",
        "question": "How many items does the {container} have, and what is its last valid position?",
        "hints": [
            "Look at the line the error points to and find the index (the number in square brackets).",
            "Count the items in the {container}. Remember that the first item is at position 0, not 1.",
            "The last valid index is the length minus 1. Make sure your index is between 0 and that value.",
        ],
        "approach": "Compare the index you use with the length of the {container}, then either change the index or make sure the {container} really has that many items.",
        "fixes": [
            "Use an index between 0 and length - 1 (the last item is at length - 1).",
            "Check first that 0 <= index < length before reading the item.",
            "If this happens inside a loop, make the loop stop before the index reaches the length.",
        ],
        "outcome": "Understand zero-based indexing and valid index ranges.",
        "notes": {
            "C": "C does not always crash on a bad index; it may silently read memory that is not yours, which is why this is dangerous.",
            "C++": "std::vector::at() reports a bad index with an exception, while [] silently reads outside the vector.",
        },
    },
    "key": {
        "concept": "Dictionary keys",
        "cause": "You looked up a key that is not in the dictionary.",
        "detail": "A dictionary only knows the keys that were added to it. Spelling and letter case must match exactly.",
        "question": "Which keys does your dictionary actually contain?",
        "hints": ["Print the dictionary just before the failing line.",
                  "Compare the key you are using with the keys you see, character by character.",
                  "Use an existing key, or check with `key in dictionary` before reading it."],
        "approach": "Find out which keys exist and decide whether the lookup key is wrong or the key was never added.",
        "fixes": ["Use a key that exists in the dictionary.",
                  "Use dictionary.get(key) to get None instead of an error when the key is missing.",
                  "Check `if key in dictionary:` before reading it."],
        "outcome": "Understand how dictionary lookups work and how to check for missing keys.",
    },
    "name": {
        "concept": "Variables and scope",
        "cause": "The name `{ident}` is used, but the compiler does not know what it refers to.",
        "detail": "A variable or function must be created before the line that uses it, and it must be spelled exactly the same way each time (upper and lower case are different).",
        "question": "Where do you create `{ident}`, and is it spelled identically on this line?",
        "hints": ["Look for typos in the name on the reported line.",
                  "Search your code for the place where `{ident}` is created. Is it before this line?",
                  "A name created inside a function or block is not visible outside of it. Check where `{ident}` lives."],
        "approach": "Make sure the name is created before it is used, spelled the same way, and visible from the line that uses it.",
        "fixes": ["Fix the spelling so it matches the declaration.",
                  "Create the variable before using it.",
                  "Move the declaration to a place where this line can see it."],
        "outcome": "Understand declaring variables before use, spelling, and scope.",
        "notes": {
            "Python": "In Python a name is created the first time you assign to it, so the assignment must run before this line.",
            "Java": "In Java a variable needs a type when it is declared (for example `int count = 0;`) and is only visible inside the block where it was declared.",
            "C": "In C, library functions also need their #include (for example `#include <stdio.h>` for printf).",
            "C++": "For names like cout, cin or string, check the #include and the std:: prefix (or `using namespace std;`).",
        },
    },
    "type": {
        "concept": "Data types",
        "cause": "A value of one type was used where a different type is needed.",
        "detail": "Every value has a type (for example whole number, decimal number, text). An operation only works when the types fit together.",
        "question": "What are the types of the values on this line?",
        "hints": ["Find every value or variable that appears on the reported line.",
                  "Write down the type of each one. Do they match what the operation needs?",
                  "Convert the value to the needed type, or change the variable's type."],
        "approach": "Identify the types involved, then convert one of the values or change a declaration so the types agree.",
        "fixes": ["Convert the value to the right type before using it.",
                  "Change the variable's declared type so it can hold this kind of value."],
        "outcome": "Understand that operations require compatible types and how to convert between them.",
        "notes": {
            "Python": "For example, you cannot add a number to text with `+`; convert with str() or int() first.",
            "Java": "Java checks types at compile time. Assigning a decimal to an int, or text to a number, needs a different type or an explicit cast.",
            "C": "C converts some types silently, but assigning incompatible types (such as text to an int) is an error or a dangerous warning.",
            "C++": "C++ is strict about conversions such as const char* to int. Use the right type, or convert explicitly.",
        },
    },
    "value": {
        "concept": "Valid values and conversion",
        "cause": "A function received a value of the right type but with content it cannot use.",
        "detail": "For example, the text 'abc' is a string, but it cannot be converted into a number because it is not made of digits.",
        "question": "What exactly is being converted or passed on this line, and could it contain something unexpected?",
        "hints": ["Print the value just before the failing line.",
                  "Does it contain spaces, letters, or an empty string where only digits are allowed?",
                  "Validate or clean the input first, or handle the failure explicitly."],
        "approach": "Check what value reaches this line and make sure it has the expected form before converting it.",
        "fixes": ["Make sure the text only contains digits before converting it.",
                  "Catch the conversion error and ask for the input again."],
        "outcome": "Understand input validation and safe conversion.",
    },
    "zero": {
        "concept": "Arithmetic and division",
        "cause": "Your program divided a number by zero.",
        "detail": "Division by zero has no defined result, so the program stops. The denominator must never be zero.",
        "question": "Which value is the denominator on this line, and when can it become zero?",
        "hints": ["Find the division (/ or %) on the reported line.",
                  "Which variable is on the right-hand side? What value does it have when the error happens?",
                  "Check the denominator is not zero before dividing."],
        "approach": "Trace where the denominator gets its value and guard the division with a check.",
        "fixes": ["Add a condition so the division only happens when the denominator is not zero.",
                  "Fix the earlier calculation that wrongly produced zero."],
        "outcome": "Understand why division by zero fails and how to guard against it.",
        "notes": {"C": "In C, integer division by zero is undefined behaviour and usually crashes; floating-point division gives inf instead."},
    },
    "attribute": {
        "concept": "Objects and attributes",
        "cause": "You used an attribute or method that this kind of value does not have.",
        "detail": "Each type only offers certain methods. For example, a number has no `.append()` and a list has no `.upper()`.",
        "question": "What type is the value before the dot, and does that type offer this method?",
        "hints": ["Check the spelling of the attribute or method name.",
                  "Print type(value) to see what you actually have.",
                  "Look up the methods available for that type."],
        "approach": "Confirm the value's real type and use a method that type provides.",
        "fixes": ["Fix a misspelled method name.", "Convert the value to the type that has this method."],
        "outcome": "Understand that methods belong to specific types.",
    },
    "null": {
        "concept": "Null and invalid references",
        "cause": "Your code tried to use something that points to nothing.",
        "detail": "A variable that holds null (or a null pointer) does not refer to any object or memory, so calling a method or reading through it fails.",
        "question": "Which variable on this line could be null, and where should it have been given a value?",
        "hints": ["Find the variable that is used with a dot, arrow or star on the reported line.",
                  "Trace back: where is that variable assigned? Could it still be null?",
                  "Make sure the object is created, or check for null before using it."],
        "approach": "Find the variable that is null and make sure it is created or assigned before this line.",
        "fixes": ["Create the object (or allocate the memory) before using it.",
                  "Check `if (variable != null)` (or `!= NULL`) before using it."],
        "outcome": "Understand null references and why they must be checked.",
        "notes": {"C": "In C this is a null pointer dereference: reading or writing address 0 crashes the program.",
                  "C++": "Dereferencing a null pointer is undefined behaviour and usually crashes."},
    },
    "syntax": {
        "concept": "Language syntax",
        "cause": "The code is not written in the form the language expects.",
        "detail": "Every language has strict grammar rules. When one is broken, the compiler cannot understand the line and reports a syntax error, sometimes on the line after the real mistake.",
        "question": "Does the reported line (and the one just before it) follow the language's grammar exactly?",
        "hints": ["Read the reported line and the line just above it slowly.",
                  "Check for missing or extra brackets, quotes, colons, commas or semicolons.",
                  "Compare the line with a working example of the same kind of statement."],
        "approach": "Check the reported line and the line before it against the correct form of the statement.",
        "fixes": ["Correct the punctuation or keyword that is missing or misplaced.",
                  "Compare with a working example of the same statement."],
        "outcome": "Learn to read syntax errors and locate the real mistake.",
    },
    "indentation": {
        "concept": "Python indentation",
        "cause": "The indentation of this line does not follow Python's block rules.",
        "detail": "Python uses indentation, not braces, to mark which lines belong inside if, for, while and def. Lines in the same block must be indented by the same amount.",
        "question": "Which lines belong inside the block, and are they all indented the same way?",
        "hints": ["Look at the line above the error. Does it end with a colon?",
                  "Lines after a colon must be indented one level (normally 4 spaces).",
                  "Use spaces only, and keep the same amount for every line in the block."],
        "approach": "Indent the statements inside the block consistently and keep other lines at their original level.",
        "fixes": ["Indent the body of the block by 4 spaces.",
                  "Remove extra indentation from lines that are not inside a block."],
        "outcome": "Understand how indentation defines blocks in Python.",
    },
    "semicolon": {
        "concept": "Statement terminators",
        "cause": "A statement is missing its ending semicolon.",
        "detail": "In Java, C and C++, every statement ends with a semicolon. The compiler often notices the problem only when it reaches the next line.",
        "question": "Which statement just before the reported position is missing its semicolon?",
        "hints": ["Look at the reported line and the line just above it.",
                  "Which statement there does not end with `;`?",
                  "Add the semicolon at the end of that statement."],
        "approach": "Find the statement that ends without a semicolon, usually on the reported line or the one above.",
        "fixes": ["Add `;` at the end of the incomplete statement."],
        "outcome": "Remember that statements end with a semicolon.",
    },
    "bracket": {
        "concept": "Matching brackets",
        "cause": "A bracket, parenthesis or brace is missing or does not match its partner.",
        "detail": "Every opening ( [ or { needs a matching closing one in the right order.",
        "question": "Can you pair each opening bracket on this line with a closing one?",
        "hints": ["Count the opening and closing brackets on the reported line.",
                  "Check the lines above too; an earlier line may be unfinished.",
                  "Add or remove brackets until each opening one has a partner."],
        "approach": "Pair up the brackets one by one, starting from the reported line.",
        "fixes": ["Add the missing closing bracket.", "Remove the extra bracket."],
        "outcome": "Learn to check that brackets are balanced.",
    },
    "closing_brace": {
        "concept": "Code blocks and braces",
        "cause": "The file ended before every block was closed.",
        "detail": "Each { must have a matching }. One is missing, so the compiler reached the end of the file while still inside a block.",
        "question": "Which block (method, loop or if) is never closed?",
        "hints": ["Check that the number of { equals the number of } in the whole file.",
                  "Indent your code consistently so unclosed blocks are easy to see.",
                  "Add the missing } where the block should end."],
        "approach": "Match each opening brace with a closing brace and add the missing one where its block ends.",
        "fixes": ["Add the missing } where the block ends."],
        "outcome": "Understand how braces delimit blocks.",
    },
    "string": {
        "concept": "String literals",
        "cause": "A piece of text was opened with a quote but never closed.",
        "detail": "Text in quotes must start and end with the same kind of quote on the same line.",
        "question": "Does every opening quote on this line have a closing quote?",
        "hints": ["Look for a missing closing quote on the reported line.",
                  "If the text itself contains a quote, it must be escaped.",
                  "Make sure the opening and closing quotes are the same kind."],
        "approach": "Add the missing closing quote, or escape quotes that belong inside the text.",
        "fixes": ["Add the closing quote.", "Escape quotes inside the text with a backslash."],
        "outcome": "Understand how string literals are delimited.",
    },
    "missing_return": {
        "concept": "Function return values",
        "cause": "A function that promises to return a value can finish without returning one.",
        "detail": "If a function has a return type other than void, every path through it must end with a return statement.",
        "question": "Is there a path through the function (an if without else, for example) that ends without `return`?",
        "hints": ["Read the function from top to bottom and follow every if/else branch.",
                  "Which path reaches the closing brace without a return?",
                  "Add a return for that path."],
        "approach": "Make sure every possible path returns a value of the declared type.",
        "fixes": ["Add a return statement at the end of the function.", "Add an else branch that also returns."],
        "outcome": "Understand that every path must return a value.",
    },
    "uninitialized": {
        "concept": "Variable initialisation",
        "cause": "A variable is used before it was given a value.",
        "detail": "A local variable has no useful value until you assign one. Reading it first gives garbage (C/C++) or a compile error (Java).",
        "question": "Is there a path where the variable is read before it is assigned?",
        "hints": ["Find where the variable is declared.", "Is it assigned on every path before this line?", "Give it an initial value when you declare it."],
        "approach": "Initialise the variable when you declare it, or assign it on all paths before use.",
        "fixes": ["Initialise it when declaring it, for example `int total = 0;`."],
        "outcome": "Understand why variables must be initialised.",
    },
    "duplicate": {
        "concept": "Unique declarations",
        "cause": "The same name was declared more than once in the same scope.",
        "detail": "Within one scope each variable or function name can be declared only once.",
        "question": "Where else is this name declared?",
        "hints": ["Search for the name in your code.", "Do you really need two variables, or only one?", "Rename one, or remove the repeated declaration."],
        "approach": "Keep a single declaration, or give each variable a different name.",
        "fixes": ["Rename one of the variables.", "Remove the second declaration and just assign the value."],
        "outcome": "Understand that names must be unique within a scope.",
    },
    "arguments": {
        "concept": "Function calls and parameters",
        "cause": "A function was called with the wrong number or types of arguments.",
        "detail": "A function defines exactly which parameters it needs. A call must provide matching values in the right order.",
        "question": "How many parameters does the function declare, and what types?",
        "hints": ["Find the function definition.", "Compare its parameters with the values in your call.", "Match the number, order and types of the arguments."],
        "approach": "Compare the call with the function definition and fix the arguments.",
        "fixes": ["Pass the correct number of arguments.", "Convert arguments to the types the function expects."],
        "outcome": "Understand how arguments must match parameters.",
    },
    "undefined_ref": {
        "concept": "Linking",
        "cause": "The program uses a function that was declared but never defined (or main is missing).",
        "detail": "Compiling checks each file; linking joins everything together. The linker reports that it cannot find the body of a function that your code calls.",
        "question": "Is the function actually written somewhere, with exactly the same name and parameters?",
        "hints": ["Read the name of the missing function in the message.", "Is it defined, and spelled the same as in the call?", "If it is `main`, check that your program has a main function."],
        "approach": "Write the missing function, or correct the name or signature so the definition matches the call.",
        "fixes": ["Define the missing function.", "Fix the spelling or parameters so the call matches the definition."],
        "outcome": "Understand the difference between declaring and defining functions.",
    },
    "header": {
        "concept": "Header files",
        "cause": "An #include refers to a file the compiler cannot find.",
        "detail": "Standard headers use angle brackets such as <stdio.h>. A misspelled name or a missing file cannot be loaded.",
        "question": "Is the header name spelled exactly right?",
        "hints": ["Check the spelling of the file in #include.", "Standard headers use <...>, your own files use \"...\".", "C++ headers have no .h, for example <iostream>."],
        "approach": "Correct the header name or add the file.",
        "fixes": ["Correct the name in the #include line."],
        "outcome": "Understand how #include finds header files.",
    },
    "implicit_decl": {
        "concept": "Function declarations",
        "cause": "A function is called before the compiler knows it exists.",
        "detail": "In C, calling a function that has not been declared (often a missing #include) makes the compiler guess, which can cause wrong behaviour.",
        "question": "Which header declares this function?",
        "hints": ["Which function does the message mention?", "Which #include provides it?", "Add the #include at the top of the file."],
        "approach": "Add the correct #include or declare the function before using it.",
        "fixes": ["Add the #include for that function, e.g. <stdio.h> for printf."],
        "outcome": "Understand declarations and headers.",
    },
    "format": {
        "concept": "Format specifiers",
        "cause": "A printf/scanf format does not match the type of the value passed.",
        "detail": "%d is for int, %f for double, %s for text, %c for a character. A mismatch prints garbage or crashes.",
        "question": "Which format symbol belongs to which value on this line?",
        "hints": ["Match each % symbol with its value, in order.", "What is the type of each value?", "Use the specifier that fits the type."],
        "approach": "Pair each format specifier with its value and fix any that do not match.",
        "fixes": ["Use %d for int, %f for double, %s for strings, %c for char."],
        "outcome": "Understand matching format specifiers to types.",
    },
    "segfault": {
        "concept": "Memory access",
        "cause": "The program touched memory it is not allowed to use, so the operating system stopped it.",
        "detail": "Common causes are using a null or uninitialised pointer, going past the end of an array, or using memory after it was freed.",
        "question": "Which pointer or array is used on (or just before) the crashing line?",
        "hints": ["Find every pointer and array used near the crash.", "Is any pointer null or never assigned?", "Is any array index larger than the array size minus 1?"],
        "approach": "Print values or use a debugger to find which pointer or index is invalid, then correct it.",
        "fixes": ["Initialise pointers before use.", "Keep array indexes inside 0 .. size-1."],
        "outcome": "Understand what a segmentation fault means.",
    },
    "buffer_overflow": {
        "concept": "Array bounds",
        "cause": "The program read or wrote beyond the end of an array or buffer.",
        "detail": "An array of n items only owns n slots. Using a slot outside that range touches memory that belongs to something else, which can corrupt data or crash.",
        "question": "How large is the array, and what index is used on the reported line?",
        "hints": ["Find the array on the reported line and its declared size.", "What is the largest index your code can reach?", "Keep the index between 0 and size - 1."],
        "approach": "Compare the largest index your code reaches with the array size and fix the loop or index.",
        "fixes": ["Use a loop condition such as i < size.", "Make the array large enough for the data."],
        "outcome": "Understand array bounds and buffer overflows.",
    },
    "memory_misuse": {
        "concept": "Memory lifetime",
        "cause": "The program used or freed memory in an invalid way.",
        "detail": "Memory must not be used after free() or delete, a pointer must be freed only once, and local variables disappear when their function returns.",
        "question": "Where is this memory freed or created, and is it used after that?",
        "hints": ["Find where the memory is freed.", "Is it used (or freed) again later?", "Set the pointer to NULL after freeing and do not use it again."],
        "approach": "Track the life of the memory: created, used, freed once, never used afterwards.",
        "fixes": ["Do not use memory after freeing it.", "Free each allocation exactly once."],
        "outcome": "Understand memory lifetime and ownership.",
    },
    "recursion": {
        "concept": "Recursion and base cases",
        "cause": "A function kept calling itself until the call stack was full.",
        "detail": "Every recursive function needs a base case that stops the recursion, and each call must move closer to it.",
        "question": "What is the base case, and does each call get closer to it?",
        "hints": ["Find the function that calls itself.", "Where does it stop calling itself?", "Make sure the argument changes towards the base case."],
        "approach": "Add or correct the base case and make sure each call makes progress.",
        "fixes": ["Add a base case that returns without a recursive call.", "Change the argument so it moves towards the base case."],
        "outcome": "Understand base cases in recursion.",
    },
    "timeout": {
        "concept": "Loops and termination",
        "cause": "The program ran for too long and was stopped; it may be in an infinite loop.",
        "detail": "A loop only ends when its condition becomes false. If nothing inside the loop changes the condition, it never ends.",
        "question": "What changes inside the loop so that its condition eventually becomes false?",
        "hints": ["Find the loop that could keep running.", "Which variable does the condition depend on?", "Make sure that variable is updated inside the loop."],
        "approach": "Check the loop condition and make sure the loop body moves towards ending it.",
        "fixes": ["Update the loop variable inside the loop.", "Correct the condition."],
        "outcome": "Understand loop termination.",
    },
    "input_eof": {
        "concept": "Reading input",
        "cause": "The program tried to read input, but none was available.",
        "detail": "input() or scanf waits for the user to type something. When the program runs without any input it reaches the end of the input and fails.",
        "question": "How many values does your program read, and did you provide that many?",
        "hints": ["Count how many times your program asks for input.", "Use the Input box to provide one line per request.", "Provide the values in the same order your program reads them."],
        "approach": "Provide the input values your program asks for.",
        "fixes": ["Type the needed values into the Input box, one per line."],
        "outcome": "Understand how programs read input.",
    },
    "cast": {
        "concept": "Type casting",
        "cause": "An object was converted to a type it does not really belong to.",
        "detail": "A cast only works when the object really is of that type.",
        "question": "What is the real type of the object being cast?",
        "hints": ["Find the cast on the reported line.", "What type does the object really have?", "Cast only to a type the object truly has."],
        "approach": "Make sure the object has the type you cast it to.",
        "fixes": ["Use `instanceof` before casting."],
        "outcome": "Understand safe casting.",
    },
    "import": {
        "concept": "Modules and imports",
        "cause": "Python could not find the module you tried to import.",
        "detail": "A module must be installed and spelled exactly right.",
        "question": "Is the module name spelled correctly, and is it installed?",
        "hints": ["Check the spelling.", "Is it part of the standard library or a package that must be installed?", "Install the package, or use a different module."],
        "approach": "Fix the name or install the missing package.",
        "fixes": ["Correct the module name.", "Install it with pip."],
        "outcome": "Understand imports.",
    },
    "file": {
        "concept": "Files and paths",
        "cause": "The program tried to open a file that does not exist.",
        "detail": "The path is relative to where the program runs. Here the program runs in an empty temporary folder, so it cannot see your own files.",
        "question": "Does this file exist at exactly this path?",
        "hints": ["Check the file name and extension.", "Is the path relative to where the program runs?", "Create the file in the program first, or avoid reading files here."],
        "approach": "Check the path and whether the file exists before opening it.",
        "fixes": ["Create the file before reading it.", "Use the correct path."],
        "outcome": "Understand file paths.",
    },
    "static_context": {
        "concept": "Static and instance members",
        "cause": "A non-static member was used from a static method such as main.",
        "detail": "Static methods belong to the class, not to an object, so they cannot use instance fields or methods directly.",
        "question": "Do you need an object to use this member?",
        "hints": ["Is the method you call marked static?", "main is static.", "Make the member static, or create an object first."],
        "approach": "Either make the member static or call it on an object.",
        "fixes": ["Add `static` to the method or field.", "Create an object and call the method on it."],
        "outcome": "Understand static versus instance members.",
    },
    "unreported": {
        "concept": "Checked exceptions",
        "cause": "Code that can throw a checked exception is neither caught nor declared.",
        "detail": "Java forces you to handle checked exceptions with try/catch or to declare them with `throws`.",
        "question": "Which call can throw this exception?",
        "hints": ["Find the call named in the message.", "Wrap it in try/catch.", "Or add `throws` to the method."],
        "approach": "Handle the exception with try/catch or declare it with throws.",
        "fixes": ["Wrap the call in try/catch.", "Add `throws ExceptionName` to the method."],
        "outcome": "Understand checked exceptions.",
    },
    "final": {
        "concept": "Constants",
        "cause": "A value declared as constant (final / const) was changed.",
        "detail": "A constant can be given a value once; assigning again is not allowed.",
        "question": "Does this variable really have to be constant?",
        "hints": ["Find where it is declared final or const.", "Do you need to change it later?", "Remove final/const or stop modifying it."],
        "approach": "Decide whether the value is truly constant.",
        "fixes": ["Remove final/const from the declaration.", "Use a different variable for the new value."],
        "outcome": "Understand constants.",
    },
    "overflow": {
        "concept": "Number limits",
        "cause": "A calculation produced a number too large for its type.",
        "detail": "Each number type stores a limited range. Going beyond it wraps around or fails.",
        "question": "How large can the result get, and does the type have room?",
        "hints": ["Find the calculation.", "Estimate the largest value.", "Use a bigger type such as long."],
        "approach": "Choose a type big enough for the results.",
        "fixes": ["Use a larger type such as long long."],
        "outcome": "Understand number ranges.",
    },
    "uncaught": {
        "concept": "Exceptions",
        "cause": "An exception was thrown and nothing caught it, so the program stopped.",
        "detail": "The program reported the exception type and message. Use that message to find the cause, then handle it or prevent it.",
        "question": "What does the exception message tell you about the cause?",
        "hints": ["Read the exception type and message carefully.", "Which operation can throw it?", "Prevent the cause, or catch it with try/catch."],
        "approach": "Use the message to find the cause, then prevent or catch it.",
        "fixes": ["Check the values before the operation.", "Catch the exception with try/catch."],
        "outcome": "Understand exceptions.",
    },
    "main_method": {
        "concept": "Program entry point",
        "cause": "Java could not find a correct main method to start.",
        "detail": "A Java program starts in `public static void main(String[] args)`.",
        "question": "Does your class contain exactly that method signature?",
        "hints": ["Check the spelling of main.", "It must be public static void.", "It needs a String[] parameter."],
        "approach": "Add or correct the main method.",
        "fixes": ["Use `public static void main(String[] args)`."],
        "outcome": "Understand where programs start.",
    },
    "out_of_memory": {
        "concept": "Memory usage",
        "cause": "The program tried to use more memory than allowed.",
        "detail": "Creating huge lists or arrays, or looping while allocating, can use up memory.",
        "question": "What part of your program allocates a lot of memory?",
        "hints": ["Find loops that keep adding data.", "How large can the data become?", "Reduce the size or free memory."],
        "approach": "Find what grows without limit and bound it.",
        "fixes": ["Use smaller data or stop the loop earlier."],
        "outcome": "Understand memory limits.",
    },
    "generic_compile": {
        "concept": "Reading compiler messages",
        "cause": "The compiler could not accept this line.",
        "detail": "Compiler messages describe the first problem found. Start with the first message and the line it points to; later messages are often a result of it.",
        "question": "What does the original message say, and which part of the line does it refer to?",
        "hints": ["Read the original message word by word.", "Look at the reported line and the one above.", "Fix the first error, then compile again."],
        "approach": "Fix the first reported error and run again; others often disappear.",
        "fixes": ["Fix the first error and rerun."],
        "outcome": "Learn to read compiler messages.",
    },
    "generic": {
        "concept": "Debugging",
        "cause": "{message}",
        "detail": "Read the error message, find the line it reports, and check the values and types used there.",
        "question": "What values and types are involved on this line?",
        "hints": ["Read the error message carefully.", "Inspect the reported line.", "Check the values and types used in that line."],
        "approach": "Use the message and the line number to narrow down the cause, then test with a small example.",
        "fixes": ["Inspect the reported line and revise the operation using the error message."],
        "outcome": "Practise a systematic debugging routine.",
    },
}

ALIASES = {}


def _alias(group, names):
    for name in names:
        ALIASES[name] = group


_alias("index", ["IndexError", "ArrayIndexOutOfBoundsException", "StringIndexOutOfBoundsException",
                 "IndexOutOfBoundsException", "ArrayOutOfBounds", "NegativeArraySizeException"])
_alias("key", ["KeyError"])
_alias("name", ["NameError", "UnboundLocalError", "UndeclaredIdentifier"])
_alias("type", ["TypeError", "TypeMismatch", "BadOperandTypes"])
_alias("value", ["ValueError", "NumberFormatException", "InputMismatchException"])
_alias("zero", ["ZeroDivisionError", "ArithmeticException", "DivisionByZero", "FloatingPointException"])
_alias("attribute", ["AttributeError"])
_alias("null", ["NullPointerException", "NullPointerDereference"])
_alias("syntax", ["SyntaxError", "TabError"])
_alias("indentation", ["IndentationError"])
_alias("semicolon", ["MissingSemicolon"])
_alias("bracket", ["MissingBracket"])
_alias("closing_brace", ["MissingClosingBrace"])
_alias("string", ["UnclosedString"])
_alias("missing_return", ["MissingReturn"])
_alias("uninitialized", ["UninitializedVariable"])
_alias("duplicate", ["DuplicateDeclaration"])
_alias("arguments", ["WrongArguments"])
_alias("undefined_ref", ["UndefinedReference"])
_alias("header", ["MissingHeader"])
_alias("implicit_decl", ["ImplicitDeclaration"])
_alias("format", ["FormatMismatch"])
_alias("segfault", ["SegmentationFault"])
_alias("buffer_overflow", ["HeapBufferOverflow", "StackBufferOverflow", "GlobalBufferOverflow"])
_alias("memory_misuse", ["HeapUseAfterFree", "StackUseAfterScope", "DoubleFree", "InvalidFree"])
_alias("recursion", ["RecursionError", "StackOverflowError", "StackOverflow"])
_alias("timeout", ["TimeLimitExceeded"])
_alias("input_eof", ["EOFError", "NoSuchElementException"])
_alias("cast", ["ClassCastException"])
_alias("import", ["ImportError", "ModuleNotFoundError"])
_alias("file", ["FileNotFoundError"])
_alias("static_context", ["StaticContext"])
_alias("unreported", ["UnreportedException"])
_alias("final", ["FinalReassignment"])
_alias("overflow", ["SignedIntegerOverflow", "OverflowError"])
_alias("uncaught", ["UncaughtException", "ProgramError", "UndefinedBehavior"])
_alias("main_method", ["MissingMainMethod"])
_alias("out_of_memory", ["MemoryError", "OutOfMemoryError"])
_alias("generic_compile", ["CompilationError", "ClassFileNameMismatch"])


def lookup(error_name):
    key = ALIASES.get(error_name)
    if key:
        return key, GROUPS[key]
    return "generic", GROUPS["generic"]
