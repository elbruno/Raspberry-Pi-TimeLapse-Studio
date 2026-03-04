# 🐍 Python Basics Used in This Project

This document explains the Python programming concepts we use in PiTimeLapse Lab. If you're new to Python, this will help you understand the code!

> 💡 **Learning Tip:** Don't try to memorize everything at once. Read a section, then look at the actual code in `simple.py` to see it in action!

## Variables

Variables are like labeled boxes that store information.

```python
# Storing different types of data
name = "PiTimeLapse"          # Text (string)
interval = 10                  # Whole number (integer)
is_running = True              # True/False (boolean)
temperature = 23.5             # Decimal number (float)
```

**In our code:**
```python
# From config.py
camera_mode = "opencv"
interval_seconds = 10
overlay_timestamp = True
```

**🎓 Why This Matters:**
Variables let your program "remember" things. In our time-lapse app, we need to remember settings (like how often to take photos) and keep track of counts (like how many photos we've taken).

**💡 Try This:**
Open `simple.py` and change `INTERVAL_SECONDS = 10` to `INTERVAL_SECONDS = 5`. Run the script - photos will be taken twice as fast!

---

## Functions

Functions are reusable pieces of code that do a specific job.

```python
# Defining a function
def greet(name):
    """Say hello to someone."""
    return f"Hello, {name}!"

# Using (calling) the function
message = greet("World")
print(message)  # Output: Hello, World!
```

**In our code:**
```python
# From utils.py
def format_duration(seconds):
    """Convert seconds into a readable string like '2h 15m 30s'."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    # ... more code ...
    return formatted_string
```

Key parts:
- `def` starts the function definition
- The name comes after `def` (e.g., `format_duration`)
- Parameters go in parentheses (e.g., `seconds`)
- The docstring (in triple quotes) explains what the function does
- `return` sends back a result

**🎓 Why This Matters:**
Functions help you avoid repeating code. Instead of writing the same 10 lines every time you need to format a duration, you write it once as a function and call it whenever needed.

**💡 Try This:**
In `simple.py`, find the `main()` function. All the time-lapse logic is inside it. What would happen if you moved some code into a separate `capture_photo()` function?

---

## Classes and Objects

Classes are blueprints for creating objects. Objects combine data and functions together.

```python
# A simple class
class Dog:
    """A class representing a dog."""
    
    def __init__(self, name, age):
        """Initialize a new dog."""
        self.name = name  # Store the dog's name
        self.age = age    # Store the dog's age
    
    def bark(self):
        """Make the dog bark."""
        return f"{self.name} says: Woof!"

# Creating an object from the class
my_dog = Dog("Buddy", 3)
print(my_dog.name)   # Output: Buddy
print(my_dog.bark()) # Output: Buddy says: Woof!
```

**In our code:**
```python
# From storage.py
class StorageManager:
    """Manages file storage for time-lapse sessions."""
    
    def __init__(self, base_dir="./data"):
        """Initialize the storage manager."""
        self.base_dir = base_dir
        # Create the directory if it doesn't exist
        ensure_folder_exists(str(self.base_dir))
    
    def create_session_folder(self, session_id):
        """Create a new folder for a session."""
        # ... code to create folder ...
```

**🎓 Why This Matters:**
Classes help organize code into logical groups. The `StorageManager` class knows everything about saving and loading files. The `CaptureScheduler` class knows everything about taking photos. This makes the code easier to understand and maintain.

**💡 Try This:**
Look at `src/pitimelapse/models.py` - the `Session` class stores information about one time-lapse recording. What data does it keep track of?

---

## Dataclasses

Dataclasses are a simpler way to create classes that mainly store data.

```python
from dataclasses import dataclass

@dataclass
class Point:
    """A point in 2D space."""
    x: float
    y: float

# Easy to create
p = Point(10.0, 20.0)
print(p.x)  # Output: 10.0
```

**In our code:**
```python
# From models.py
@dataclass
class Session:
    """Represents a time-lapse recording session."""
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    interval_seconds: int = 10
    total_photos: int = 0
```

**🎓 Why This Matters:**
Dataclasses let you create "data containers" with less code. Instead of writing `__init__` and other methods, Python generates them for you. The `@dataclass` decorator (the `@` line above the class) is like telling Python "please add the standard methods for me."

---

## Lists and Dictionaries

### Lists
Lists store multiple items in order.

```python
# A list of colors
colors = ["red", "green", "blue"]
print(colors[0])  # Output: red (first item, index 0)

# Add an item
colors.append("yellow")

# Loop through all items
for color in colors:
    print(color)
```

### Dictionaries
Dictionaries store key-value pairs (like a real dictionary with words and definitions).

```python
# A dictionary of settings
settings = {
    "camera_mode": "opencv",
    "interval": 10,
    "enabled": True
}

# Access by key
print(settings["camera_mode"])  # Output: opencv

# Add or update
settings["port"] = 8000
```

**In our code:**
```python
# From models.py
def to_dict(self):
    """Convert session to a dictionary."""
    return {
        "id": self.id,
        "start_time": self.start_time.isoformat(),
        "total_photos": self.total_photos,
    }
```

**🎓 Why This Matters:**
Lists are used everywhere: storing a list of captured photos, a list of errors, a list of sessions. Dictionaries are perfect for configuration and API responses (like JSON data).

**💡 Try This:**
Look at `config.yaml` - it's basically a dictionary! Each setting name (like `camera_mode`) is a key, and each value (like `opencv`) is the associated data.

---

## Loops

Loops repeat code multiple times.

### For Loops
```python
# Loop 5 times
for i in range(5):
    print(f"Count: {i}")

# Loop through a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(f"I like {fruit}")
```

### While Loops
```python
# Keep running while a condition is true
count = 0
while count < 3:
    print(f"Count is {count}")
    count += 1  # Same as: count = count + 1
```

**In our code:**
```python
# From capture.py - The main capture loop
while not self._stop_event.is_set():
    # Take a photo
    self._capture_one_image()
    
    # Wait for the next capture time
    while datetime.now() < sleep_until:
        time.sleep(0.5)
```

**🎓 Why This Matters:**
The `while True` loop in `simple.py` is the heart of time-lapse! It keeps taking photos until you stop it. Understanding loops is essential for any program that repeats actions.

**💡 Try This:**
In `simple.py`, the camera warm-up uses `for _ in range(5):`. What happens if you change 5 to 10? The camera gets more time to adjust!

---

## Conditionals (If/Else)

Make decisions based on conditions.

```python
temperature = 25

if temperature > 30:
    print("It's hot!")
elif temperature > 20:
    print("It's nice!")
else:
    print("It's cold!")
```

**In our code:**
```python
# From config.py
def validate(self):
    errors = []
    
    if self.interval_seconds < 1:
        errors.append("Interval must be at least 1 second")
    
    if self.camera_mode not in ["opencv", "picamera2"]:
        errors.append("Invalid camera mode")
    
    return errors
```

**🎓 Why This Matters:**
Conditionals let your program make decisions. In `simple.py`, we use `if not cap.isOpened():` to check if the camera failed to open - and show a helpful error message if it did.

**💡 Try This:**
What if you wanted to take double-resolution photos during the day? You could add:
```python
from datetime import datetime
hour = datetime.now().hour
if 6 <= hour <= 18:
    WIDTH = 1920  # Day: high resolution
else:
    WIDTH = 640   # Night: low resolution
```

---

## Exception Handling (Try/Except)

Handle errors gracefully instead of crashing.

```python
try:
    # Code that might cause an error
    result = 10 / 0  # This will cause a division by zero error!
except ZeroDivisionError:
    # Handle the error
    print("Oops! Can't divide by zero.")
except Exception as e:
    # Handle any other error
    print(f"Something went wrong: {e}")
```

**In our code:**
```python
# From camera_opencv.py
def capture(self):
    try:
        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            logger.error("Failed to capture frame")
            return None
    except Exception as e:
        logger.error(f"Error capturing image: {e}")
        return None
```

**🎓 Why This Matters:**
Things go wrong: cameras disconnect, files fail to save, networks drop. Exception handling lets your program recover gracefully instead of crashing with an ugly error. In `simple.py`, we catch `KeyboardInterrupt` so pressing Ctrl+C prints a nice goodbye message instead of a stack trace.

**💡 Try This:**
In `simple.py`, the `try/except KeyboardInterrupt` block catches Ctrl+C. What happens if you remove the try/except and press Ctrl+C? (Hint: you'll see Python's default error message!)

---

## Modules and Imports

Split code into separate files and reuse it.

```python
# In utils.py
def format_duration(seconds):
    # ... code ...
    return result

# In another file
from utils import format_duration

duration_text = format_duration(3661)
print(duration_text)  # Output: 1h 1m 1s
```

**In our code:**
```python
# From app.py
from .config import AppConfig, load_config, save_config
from .storage import StorageManager
from .capture import CaptureScheduler
```

**🎓 Why This Matters:**
Big programs are split into multiple files (modules). This keeps each file focused on one thing. The main app imports what it needs from other modules.

**💡 Try This:**
Look at the top of `simple.py` - each `import` brings in code from a different module. What does `import time` give us? The ability to use `time.sleep()`!

---

## Type Hints

Type hints tell readers (and tools) what type of data to expect.

```python
def greet(name: str) -> str:
    """
    Greet someone by name.
    
    Args:
        name: The person's name (string)
    
    Returns:
        A greeting message (string)
    """
    return f"Hello, {name}!"
```

**In our code:**
```python
# From utils.py
def get_timestamp_string(
    dt: Optional[datetime] = None,
    format_style: str = "filename"
) -> str:
```

The `-> str` means the function returns a string.
`Optional[datetime]` means it can be a datetime OR None.

**🎓 Why This Matters:**
Type hints make code easier to understand. When you see `name: str`, you immediately know that `name` should be text, not a number. Python doesn't enforce these, but they help you and other programmers avoid mistakes.

---

## String Formatting (f-strings)

Create strings that include variable values.

```python
name = "Alice"
age = 15

# f-string (modern way)
message = f"My name is {name} and I am {age} years old."
print(message)  # Output: My name is Alice and I am 15 years old.

# Can include expressions
print(f"Next year I'll be {age + 1}")
```

**🎓 Why This Matters:**
F-strings are used everywhere in our code to create messages. In `simple.py`, we use `f"photo_{timestamp}.jpg"` to create unique filenames.

**💡 Try This:**
Change the filename pattern in `simple.py`. Instead of `f"photo_{timestamp}.jpg"`, try `f"timelapse_{photo_count:04d}.jpg"` - this creates filenames like `timelapse_0001.jpg`, `timelapse_0002.jpg`, etc.

---

## Practice Exercises

Try these to test your understanding:

1. **Variables**: Change the default interval in `config.yaml` and see what happens.

2. **Functions**: Find the `format_duration` function in `utils.py` and trace through what it does with the input `125`.

3. **Classes**: Look at the `Session` class in `models.py`. What information does a session store?

4. **Loops**: In `capture.py`, find the main capture loop. What makes it stop?

5. **Error Handling**: In `camera_opencv.py`, what happens if the camera fails to capture a photo?

---

## 🎯 Quick Reference Card

| Concept | Example | When to Use |
|---------|---------|-------------|
| Variable | `x = 10` | Store data for later |
| Function | `def greet(): return "Hi"` | Reusable code blocks |
| Class | `class Camera:` | Group related data and functions |
| List | `photos = ["a.jpg", "b.jpg"]` | Ordered collection |
| Dictionary | `{"width": 640}` | Key-value pairs |
| For loop | `for i in range(5):` | Repeat a known number of times |
| While loop | `while running:` | Repeat until condition is false |
| If/else | `if x > 0:` | Make decisions |
| Try/except | `try: ... except:` | Handle errors gracefully |
| Import | `import cv2` | Use code from other files |

---

## Resources for Learning More

- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/) - Lots of beginner tutorials
- [Python for Everybody](https://www.py4e.com/) - Free course
- [Codecademy Python Course](https://www.codecademy.com/learn/learn-python-3)
