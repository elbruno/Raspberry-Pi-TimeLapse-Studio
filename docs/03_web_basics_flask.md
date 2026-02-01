# 🌐 Web Basics with Flask

This document explains how the web interface in PiTimeLapse Lab works. We use a Python library called **Flask** to create the web application.

## What is a Web Application?

When you visit a website, your browser (Chrome, Firefox, etc.) sends a **request** to a **web server**. The server processes the request and sends back a **response** (usually an HTML page).

```
┌──────────────┐         Request          ┌──────────────┐
│              │  ─────────────────────>  │              │
│   Browser    │      "GET /gallery"      │   Server     │
│   (Client)   │                          │   (Flask)    │
│              │  <─────────────────────  │              │
└──────────────┘         Response         └──────────────┘
                    (HTML page)
```

## Flask: A Simple Web Framework

Flask makes it easy to create web applications in Python. Here's the simplest possible Flask app:

```python
from flask import Flask

# Create the Flask application
app = Flask(__name__)

# Define a "route" - what happens when someone visits "/"
@app.route("/")
def home():
    return "Hello, World!"

# Run the server
if __name__ == "__main__":
    app.run()
```

When you run this and visit `http://localhost:5000`, you'll see "Hello, World!"

## Routes

Routes connect URLs to Python functions. When someone visits a URL, the matching function runs.

```python
@app.route("/")
def index():
    return "This is the home page"

@app.route("/gallery")
def gallery():
    return "This is the gallery page"

@app.route("/settings")
def settings():
    return "This is the settings page"
```

**In our code (app.py):**
```python
@app.route("/")
def index():
    """Home page - shows current status and control buttons."""
    status = scheduler.get_status()
    return render_template("index.html", status=status)
```

## HTTP Methods

Different HTTP methods indicate different actions:

- **GET** - Retrieve information (loading a page)
- **POST** - Send information (submitting a form)

```python
# This route accepts both GET and POST
@app.route("/settings/save", methods=["POST"])
def save_settings():
    # Process the form data
    new_interval = request.form.get("interval_seconds")
    # Save settings...
    return redirect("/settings")
```

## Templates (HTML)

Instead of writing HTML directly in Python, we use **templates**. Templates are HTML files with special placeholders that get filled in with data.

### Template Syntax (Jinja2)

Flask uses Jinja2 templating. Here are the main features:

**Variables:** Use `{{ variable }}` to insert values
```html
<h1>Welcome, {{ username }}!</h1>
<p>You have {{ photo_count }} photos.</p>
```

**Conditionals:** Use `{% if %}` for logic
```html
{% if is_running %}
    <p class="status-running">Time-lapse is running!</p>
{% else %}
    <p class="status-stopped">Ready to start</p>
{% endif %}
```

**Loops:** Use `{% for %}` to repeat
```html
<ul>
{% for image in images %}
    <li>{{ image.name }}</li>
{% endfor %}
</ul>
```

### Template Inheritance

Templates can extend other templates, avoiding repetition.

**base.html** (the parent template):
```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}PiTimeLapse{% endblock %}</title>
</head>
<body>
    <nav>
        <!-- Navigation menu -->
    </nav>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>PiTimeLapse Lab</footer>
</body>
</html>
```

**index.html** (a child template):
```html
{% extends "base.html" %}

{% block title %}Dashboard - PiTimeLapse{% endblock %}

{% block content %}
<h1>Dashboard</h1>
<p>Status: {{ status.is_running }}</p>
{% endblock %}
```

The child fills in the "blocks" defined by the parent.

## The Request Object

When handling a request, you can access information about it:

```python
from flask import request

@app.route("/search")
def search():
    # Get query parameters from the URL
    # e.g., /search?query=sunset
    query = request.args.get("query", "")
    return f"Searching for: {query}"

@app.route("/settings/save", methods=["POST"])
def save_settings():
    # Get data from a form submission
    interval = request.form.get("interval_seconds")
    return f"Setting interval to: {interval}"
```

## Responses

Routes can return different types of responses:

```python
# Plain text
@app.route("/hello")
def hello():
    return "Hello!"

# HTML from a template
@app.route("/")
def index():
    return render_template("index.html", name="World")

# JSON for APIs
@app.route("/api/status")
def api_status():
    return jsonify({"is_running": True, "photos": 42})

# Redirect to another page
@app.route("/old-page")
def old_page():
    return redirect("/new-page")
```

## Static Files

Static files (CSS, JavaScript, images) don't change and are served directly.

```
static/
└── style.css
```

In HTML, reference them like this:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

The `url_for()` function generates the correct URL.

## Our API Endpoints

PiTimeLapse Lab has a REST API that returns JSON data. The web interface uses these to communicate with the server without reloading the page.

```
GET  /api/status                 - Get current status
POST /api/start                  - Start time-lapse
POST /api/stop                   - Stop time-lapse
GET  /api/sessions               - List all sessions
GET  /api/sessions/<id>          - Get one session's details
GET  /api/sessions/<id>/latest-images - Get recent images
```

**Example API response:**
```json
{
  "is_running": true,
  "current_session_id": "session_20240115_143022",
  "total_photos": 42,
  "last_capture_time": "2024-01-15T14:35:22"
}
```

## JavaScript in the Frontend

The web interface uses JavaScript to call the API and update the page without reloading.

```javascript
// Start the time-lapse (from index.html)
function startTimelapse() {
    // Call the API
    fetch('/api/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Show the result
            if (data.success) {
                alert("Started!");
                location.reload();  // Refresh the page
            } else {
                alert("Error: " + data.message);
            }
        });
}
```

This uses the **Fetch API** to make HTTP requests from JavaScript.

## CSS Styling

CSS (Cascading Style Sheets) controls how the pages look.

**Example from style.css:**
```css
/* Card component */
.card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Button styles */
.btn-success {
    background-color: #28a745;
    color: white;
}

.btn-success:hover {
    background-color: #218838;
}
```

## How It All Fits Together

Here's what happens when you click "Start Time-lapse":

1. **You click the button** in your browser

2. **JavaScript runs:**
   ```javascript
   fetch('/api/start', { method: 'POST' })
   ```

3. **Browser sends request** to the Flask server:
   ```
   POST /api/start HTTP/1.1
   Host: raspberrypi:8000
   ```

4. **Flask routes the request** to the right function:
   ```python
   @app.route("/api/start", methods=["POST"])
   def api_start():
       success, message = scheduler.start()
       return jsonify({"success": success, "message": message})
   ```

5. **The capture scheduler starts** a background thread

6. **Flask sends response:**
   ```json
   {"success": true, "message": "Time-lapse started!"}
   ```

7. **JavaScript handles the response** and shows a message

8. **Page reloads** to show the new status

## Try It Yourself

1. Open `templates/index.html` and find where the status is displayed

2. Open `static/style.css` and try changing a color

3. In `src/pitimelapse/app.py`, find the `/api/status` route and see what data it returns

4. Use your browser's Developer Tools (F12) to see the network requests when you click buttons

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [MDN Web Docs](https://developer.mozilla.org/) - Learn HTML, CSS, JavaScript
- [CSS Tricks](https://css-tricks.com/) - CSS tutorials and guides
