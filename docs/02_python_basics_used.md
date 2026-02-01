# 🐍 Python Basics Used in This Project

This document explains the Python programming concepts we use in PiTimeLapse Lab. If you're new to Python, this will help you understand the code!

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

## Practice Exercises

Try these to test your understanding:

1. **Variables**: Change the default interval in `config.yaml` and see what happens.

2. **Functions**: Find the `format_duration` function in `utils.py` and trace through what it does with the input `125`.

3. **Classes**: Look at the `Session` class in `models.py`. What information does a session store?

4. **Loops**: In `capture.py`, find the main capture loop. What makes it stop?

5. **Error Handling**: In `camera_opencv.py`, what happens if the camera fails to capture a photo?

## Resources for Learning More

- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/) - Lots of beginner tutorials
- [Python for Everybody](https://www.py4e.com/) - Free course
- [Codecademy Python Course](https://www.codecademy.com/learn/learn-python-3)
