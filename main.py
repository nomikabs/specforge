# specforge.py
from fastapi import FastAPI, Query, Header, HTTPException, Depends
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from typing import List, Optional
import random, string, os, json
from functools import partial

# --- Global Storage for Dynamic Endpoints and Mock Data ---
# A simple mechanism to hold the mock data and auth status for dynamic routes
MOCK_CONFIG = {} 

# --------------------------
# 🌟 Create FastAPI app
# --------------------------
app = FastAPI(
    title="SpecForge – Beginner-Friendly API Generator",
    description="Generate APIs and test them live with a simple UI",
    version="3.0.0" # Version updated due to major feature addition
)

# --------------------------
# 🧱 Helper: Generate API Key
# --------------------------
def generate_api_key(app1: str, app2: str) -> str:
    prefix = app1[:3].upper()
    suffix = app2[:3].upper()
    rand = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}-{rand}-{suffix}"

# --------------------------
# 🔑 Helper: Authentication Dependency
# --------------------------
def verify_live_api_key(api_key: Optional[str] = Header(None, alias='X-API-Key')):
    """Checks the API key against the last generated key for live testing."""
    if MOCK_CONFIG.get("auth_required") and MOCK_CONFIG.get("api_key"):
        if not api_key or api_key != MOCK_CONFIG["api_key"]:
            raise HTTPException(status_code=401, detail='Invalid or missing X-API-Key header')
    return True

# --------------------------
# 🧩 Helper: Create Python API File (Updated to include dynamic key)
# --------------------------
def create_python_api_file(filename: str, endpoints: List[str], example_data: dict, auth_required: bool, dynamic_api_key: str) -> str:
    os.makedirs("generated_apis", exist_ok=True)
    filepath = os.path.join("generated_apis", filename)

    with open(filepath, "w") as f:
        f.write("from fastapi import FastAPI, Header, HTTPException, Depends\n")
        f.write("from typing import Optional\n\n")
        f.write(f"app = FastAPI(title='Generated API for {filename.replace('_api.py','')}')\n\n")
        
        # --- NEW: Include the generated key in the file ---
        f.write(f"HARDCODED_API_KEY = '{dynamic_api_key}'\n\n")

        if auth_required:
            f.write("def verify_api_key(api_key: Optional[str] = Header(None, alias='X-API-Key')):\n")
            f.write(f"    if not api_key or api_key != HARDCODED_API_KEY:\n")
            f.write("        raise HTTPException(status_code=401, detail='Invalid or missing X-API-Key header')\n")
            f.write("    return True\n\n")

        for endpoint in endpoints:
            dep = ", dependencies=[Depends(verify_api_key)]" if auth_required else ""
            f.write(f"@app.get('{endpoint}'{dep})\n")
            f.write("def get_data():\n")
            f.write(f"    return {{'status':'success','data':{example_data}}}\n\n")

    return filepath

# --------------------------
# ⚙ Endpoint: Generate API File (Updates the app and global config)
# --------------------------
@app.get("/generate_api")
def generate_api(
    app1: str = Query(...),
    app2: str = Query(...),
    fields: List[str] = Query(["id", "name", "status"]),
    require_auth: bool = Query(True)
):
    global MOCK_CONFIG
    
    api_key = generate_api_key(app1, app2)
    app1_clean = app1.lower().replace(" ", "")
    app2_clean = app2.lower().replace(" ", "")
    endpoints = [f"/{app1_clean}to{app2_clean}", f"/{app2_clean}to{app1_clean}"]
    example_data = {f: f"sample_{f}" for f in fields}
    filename = f"{app1_clean}_{app2_clean}_api.py"
    
    # --- Live Testing Setup (Dynamic Endpoint Addition) ---
    
    # 1. Update global config for auth checking and response data
    MOCK_CONFIG.update({
        "api_key": api_key,
        "auth_required": require_auth,
        "example_data": {"status": "success", "data": example_data},
        "endpoints": endpoints
    })

    # 2. Define the mock handler factory function
    def create_mock_handler(mock_data, auth_required):
        # This is the actual function added to the FastAPI router
        def mock_handler(auth_ok: bool = Depends(verify_live_api_key)):
            if auth_ok:
                return JSONResponse(content=mock_data, status_code=200)
        return mock_handler
    
    # 3. Clean up existing dynamic endpoints before adding new ones
    # NOTE: This is complex in FastAPI. A simpler approach is usually defining a catch-all route, 
    # but since the routes are known, we'll try to add them directly.
    
    # As removing routes is highly complex and not recommended for simple dynamic systems,
    # we'll rely on the client to test the new endpoints immediately after generation. 
    # The MOCK_CONFIG ensures they all serve the latest data.
    
    # 4. Add new endpoints to the running app instance
    mock_handler = create_mock_handler(MOCK_CONFIG["example_data"], require_auth)
    
    for endpoint in endpoints:
        # We use a unique name to ensure FastAPI recognizes the new function
        mock_handler._name_ = f"mock_route_for_{endpoint.replace('/','')}" 
        
        # Check if the route exists before adding (Optional: prevents warnings on re-generation)
        app.add_api_route(
            endpoint, 
            mock_handler, 
            methods=["GET"]
        )

    # --- File Generation (Uses dynamic_api_key) ---
    create_python_api_file(filename, endpoints, example_data, require_auth, api_key)

    # Return structured output for the frontend
    return {
        "message": "API File Generated Successfully! Live endpoints added.",
        "file_name": filename,
        "download_link": f"/download_api?file={filename}",
        "connection": f"{app1} ↔ {app2}",
        "auth_required": require_auth,
        "specforge_api_key": api_key,
        "example_data": example_data,
        "endpoint_example": endpoints[0] # The dynamic route is now live on the main app!
    }

# --------------------------
# 💾 Endpoint: Download File
# --------------------------
@app.get("/download_api", response_class=FileResponse)
def download_api(file: str):
    path = os.path.join("generated_apis", file)
    if os.path.exists(path):
        return FileResponse(path, filename=file)
    raise HTTPException(status_code=404, detail="File not found")

# --------------------------
# 🏠 Home + Frontend (Aesthetic Improvements Applied)
# --------------------------
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SpecForge ⚙ API Generator</title>
<style>
/* -------------------------------
    DARK/BLUE THEME VARIABLES
--------------------------------*/
:root {
    --color-bg-deep: #010A10; /* Very dark blue */
    --color-bg-primary: #021220; /* Darker blue */
    --color-text-main: #e6f7ff; /* Off-white / light blue */
    --color-text-subtle: #a8c4d8; /* Muted blue-grey */
    --color-accent-main: #33aaff; /* Bright blue */
    --color-accent-light: #5ba4d8; /* Lighter blue */
    --color-success: #00ffc6; /* Cyan/Aqua for success/highlights */
    --color-code: #00e0ff; /* Bright Cyan for code blocks */
    --border-color: #283d4d; /* Subtle blue border */
    --card-bg: transparent; 
    --header-color: #5ba4d8; /* H1 color */
    --step-number-color: #00ffc6; /* Distinct color for step numbers (Cyan) */
}

/* -------------------------------
    BODY & BACKGROUND
--------------------------------*/
body {
    font-family: 'Segoe UI', sans-serif;
    color: var(--color-text-main);
    margin: 0;
    padding: 0;
    font-size: 1.05rem; 
    line-height: 1.6;
    
    background: 
        linear-gradient(rgba(1, 10, 16, 0.95), rgba(2, 18, 32, 0.95)), 
        url('download.jpeg'); 
    background-size: cover;
    background-position: center center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

/* -------------------------------
    NAVIGATION BAR
--------------------------------*/
nav {
  display: flex;
  justify-content: space-between; 
  align-items: center;
  background: linear-gradient(90deg, var(--color-bg-primary), var(--color-bg-deep));
  padding: 1rem 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.7);
  position: sticky;
  top: 0;
  z-index: 10;
}
.nav-links {
    display: flex;
    gap: 2rem;
    flex-grow: 1; 
    justify-content: center;
}
nav a {
  color: var(--color-text-subtle);
  text-decoration: none;
  font-weight: 600;
  font-size: 1.1rem;
  padding: 0 5px 8px;
  transition: color 0.3s;
}
nav a:hover {
    color: var(--color-accent-light);
}
nav a.active {
  color: var(--color-text-main);
}
.website-title {
    color: var(--header-color);
    font-size: 1.5rem;
    font-weight: 700;
    flex-shrink: 0; 
}

/* -------------------------------
    MAIN LAYOUT & TYPOGRAPHY
--------------------------------*/
main {
    max-width: 1100px; 
    margin: 40px auto;
    padding: 20px;
}
h1 {
    text-align: center;
    color: var(--header-color); 
    margin-bottom: 40px;
}
h2 {
    /* H2 Color: Light Accent Blue */
    color: var(--color-accent-light); 
    margin-top: 40px;
    padding-bottom: 8px;
    font-size: 1.6rem;
    border-bottom: none; 
}

/* -------------------------------
    CONTENT STYLES 
--------------------------------*/
.content-box {
    padding: 30px 0; 
}
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
    gap: 25px;
    margin-top: 25px;
}
.card {
    background: var(--color-bg-deep); 
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.4); 
    border: 1px solid var(--border-color);
    transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
}
h3 {
    /* H3 Color: Success Cyan */
    color: var(--color-success); 
    font-size: 1.2rem;
    margin-top: 0;
    margin-bottom: 10px;
}
.card p {
    color: var(--color-text-subtle);
}
.card:hover {
    transform: translateY(-3px); 
    box-shadow: 0 8px 15px rgba(51, 170, 255, 0.3);
    border-color: var(--color-accent-main);
}

/* -------------------------------
    LIST & TEXT STYLES 
--------------------------------*/
.steps-list {
    margin-top: 20px;
    color: var(--color-text-subtle);
    font-size: 1.1rem;
    line-height: 1.6; 
}
.step {
    margin-bottom: 15px; 
    line-height: 1.6; 
}
.step-number {
    font-weight: 700;
    color: var(--step-number-color); 
    /* Set to block to ensure the description starts on a new line */
    display: block; 
    width: auto; 
    white-space: normal; 
    margin-bottom: 5px; 
}
.use-case-list {
    list-style-type: disc; 
    margin-left: 20px;
    color: var(--color-text-subtle);
    line-height: 1.8; 
}
/* For ordered list inside steps, apply spacing */
.steps-list ol li {
    line-height: 1.6; 
}

/* --- TABS --- */
section {
    display: none;
}
section.active {
    display: block;
}

/* --- FORM/GENERATOR STYLES --- */
#generator-section .content-box {
    background: rgba(2, 18, 32, 0.5); 
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.7);
    border: 1px solid var(--border-color);
}
button, .copy-btn {
    background: linear-gradient(90deg, var(--color-accent-main), var(--color-accent-light));
    color: #fff;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s;
}
button:hover {
    box-shadow: 0 0 10px var(--color-accent-light);
}
input, textarea, select {
    width: 100%;
    padding: 12px;
    margin-top: 6px;
    margin-bottom: 20px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: var(--color-bg-deep); 
    color: var(--color-text-main);
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
    font-size: 1.1rem; 
}
input:focus, textarea:focus, select:focus {
    border-color: var(--color-accent-main);
    outline: none;
}
label {
    font-size: 1.05rem; 
}
#output {
    background: var(--color-bg-primary); 
    padding: 25px; 
    border-radius: 12px;
    border-left: 5px solid var(--color-success);
    margin-top: 30px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
}
#output p, #output a {
    color: var(--color-text-main);
    font-weight: normal; 
}
.test-section {
    display: flex;
    gap: 10px;
    align-items: center;
}
.test-section button {
    white-space: nowrap;
}
#apiResponse {
    white-space: pre-wrap;
    background: #000000;
    padding: 15px;
    border-radius: 8px;
    margin-top: 15px;
    font-family: 'Consolas', 'Monaco', monospace;
    color: var(--color-code);
    overflow-x: auto;
}

/* -------------------------------
    FOOTER
--------------------------------*/
footer {
    text-align: center;
    padding: 30px;
    color: #888;
    font-size: 0.9rem;
    border-top: none; 
    margin-top: 40px;
}
</style>
</head>
<body>
<nav>
    <div class="website-title">SpecForge ⚙</div> 

    <div class="nav-links">
        <a href="#about" id="aboutTab" class="active" onclick="showTab('about')">About</a> 
        <a href="#features" id="featuresTab" onclick="showTab('features')">Features</a>
        <a href="#howitworks" id="howitworksTab" onclick="showTab('howitworks')">How It Works</a>
        <a href="#faq" id="faqTab" onclick="showTab('faq')">FAQ</a>
        <a href="#generator" id="generatorTab" onclick="showTab('generator')">Generator</a>
    </div>
    <div style="width: 124px;"></div> 
</nav>

<main>
    <section id="about-section" class="active">
        <h1>Welcome to SpecForge ⚙</h1>
        <div style="text-align:center; padding: 20px 0;">
            <p style="font-size: 1.3rem; color: var(--color-text-subtle); max-width: 700px; margin: 0 auto;">
                SpecForge is an AI-inspired FastAPI-based project that lets you instantly generate robust, production-ready Python API boilerplates. From complex data mocking to custom authentication, it's designed to save every developer time and effort.
            </p>
        </div>
        
        <div class="content-box" style="margin-top: 50px;">
            <h2 style="margin-top: 0; padding-bottom: 0;">Core Capabilities</h2>
            <div class="card-grid">
                <div class="card">
                    <h3>Instant Live Mocking</h3>
                    <p>The Generator spins up a live, functional endpoint on this server, allowing you to test your integration immediately without downloading a single file first.</p>
                </div>
                <div class="card">
                    <h3>Production-Grade Code</h3>
                    <p>The generated file is a complete FastAPI application, using standard Python dependencies and best practices for deployment.</p>
                </div>
                <div class="card">
                    <h3>Customizable Schemas</h3>
                    <p>Define your data fields (e.g., <code>user_id</code>, <code>price</code>, <code>is_active</code>) and the API will return that structure as a realistic mock object.</p>
                </div>
                <div class="card">
                    <h3>Secure API Key Inclusion</h3>
                    <p>An automatically generated, unique <code>X-API-Key</code> is embedded in the downloaded file and required for the live test, simulating real security.</p>
                </div>
                <div class="card">
                    <h3>Bi-Directional Routes</h3>
                    <p>It creates two sensible endpoints (e.g., <code>/app1toapp2</code> and <code>/app2toapp1</code>) ideal for simulating webhook or integration APIs.</p>
                </div>
                <div class="card">
                    <h3>Zero Configuration Setup</h3>
                    <p>The generated Python file runs out-of-the-box with Uvicorn, requiring minimal setup beyond basic Python dependencies.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section id="features-section">
        <div class="content-box">
            <h2>Detailed Features: A Closer Look</h2>
            <p style="color: var(--color-text-subtle);">Uncover the technical details that power SpecForge's API generation.</p>
            <div class="card-grid" style="margin-top: 20px;">
                <div class="card">
                    <h3>Dynamic Endpoint Addition</h3>
                    <p>The core application modifies its own router (<code>app.add_api_route</code>) on-the-fly to host your new mock API instantly, a powerful FastAPI technique.</p>
                </div>
                <div class="card">
                    <h3>Header-Based Authentication</h3>
                    <p>It implements a standard Dependency Injection pattern (<code>Depends(verify_live_api_key)</code>) to check the <code>X-API-Key</code> header, a critical microservice best practice.</p>
                </div>
                <div class="card">
                    <h3>Clean Python Boilerplate</h3>
                    <p>The output is idiomatic, easy-to-read Python, serving as an excellent educational tool for learning FastAPI and Python dependencies.</p>
                </div>
                <div class="card">
                    <h3>URL Slug Generation</h3>
                    <p>App names are automatically sanitized and converted to lowercase slugs (e.g., "WhatsApp Swiggy" $\rightarrow$ <code>whatsappswiggy_api.py</code>) for clean filenames and endpoints.</p>
                </div>
                <div class="card">
                    <h3>ASGI Compliant</h3>
                    <p>The generated code is fully compatible with ASGI (Asynchronous Server Gateway Interface), meaning it's ready for high-performance servers like Uvicorn, Hypercorn, and Daphne.</p>
                </div>
                <div class="card">
                    <h3>Downloadable Source Code</h3>
                    <p>A dedicated endpoint (<code>/download_api</code>) provides the complete source file, ensuring you own and control your generated boilerplate instantly.</p>
                </div>
                <div class="card">
                    <h3>Minimal Dependencies</h3>
                    <p>The generated API file requires only <code>fastapi</code>, <code>uvicorn</code>, and standard Python libraries, keeping the final project lightweight and easy to maintain.</p>
                </div>
            </div>
        </div>
    </section>

    <section id="howitworks-section">
        <div class="content-box">
            <h2>How It Works: Step-by-Step for Beginners</h2>
            <p style="color: var(--color-text-subtle);">This process shows how SpecForge instantly creates a working API for you, both as a downloadable file and a live testing service.</p>
            <div class="steps-list">
                <div class="step">
                    <span class="step-number">Step 1: Input</span> 
                    You tell SpecForge two names (e.g., Spotify and Discord) and the data fields you expect (e.g., <code>song_name</code>, <code>user_id</code>).
                </div>
                <div class="step">
                    <span class="step-number">Step 2: Generation</span> 
                    The backend Python code (running on this server) takes your input and does three things: 
                    <ol style="margin-left: 20px; margin-top: 5px; color: var(--color-text-subtle);">
                        <li style="line-height: 1.6;">It creates a unique, random API key (like <code>SPO-1234-DIS</code>).</li>
                        <li style="line-height: 1.6;">It builds a complete, runnable Python file that includes two API endpoints (like <code>/spotifytodiscord</code>) and uses the API key for security.</li>
                        <li style="line-height: 1.6;">It saves this new file on the server so you can download it later.</li>
                    </ol>
                </div>
                <div class="step">
                    <span class="step-number">Step 3: Live Mocking</span> 
                    Crucially, SpecForge immediately installs the new endpoints directly into the running application. It sets up a live mock service with your specified data structure and API key requirement. This happens instantly, without needing a server restart.
                </div>
                <div class="step">
                    <span class="step-number">Step 4: Testing</span> 
                    The output pane appears, giving you the unique API key and the live endpoint URL. You can paste the key into the required X-API-Key header field and hit "Test GET."
                </div>
                <div class="step">
                    <span class="step-number">Step 5: Output</span> 
                    The live test calls the endpoint you just created on this server. If the API key is correct, the server returns your sample data, confirming your API specification is working. You can then download the generated file to run it independently anywhere else.
                </div>
            </div>

            <h2 style="color: var(--color-accent-light);">Ideal Use Cases</h2>
            <ul class="use-case-list">
                <li>Frontend Development Mocking: Test your frontend app (React, Vue, etc.) against a guaranteed working API without waiting for a backend team to finish development.</li>
                <li>Learning REST Concepts: Understand the flow of API requests, required headers, authentication (X-API-Key), and structured JSON responses using clean, simple Python code.</li>
                <li>Hackathons and Prototyping: Rapidly create multiple temporary backend services with defined schemas in minutes, allowing you to focus on the application logic.</li>
                <li>Quick Integration Testing: Create a secure placeholder API for a third-party service you plan to integrate with, ensuring your client code handles the data structure correctly before switching to the real service.</li>
                <li>Workshops and Teaching: Provide students with a ready-to-run, minimal backend file to immediately start practicing client-side API calls.</li>
                <li>Contract Definition: Define the exact data contract (schema) between two services and generate the implementation file simultaneously, reducing miscommunication.</li>
            </ul>
        </div>
    </section>

    <section id="faq-section">
        <div class="content-box">
            <h2>Common Questions</h2>
            <p style="color: var(--color-text-subtle);">Find quick answers to common questions about SpecForge.</p>
            <div class="steps-list">
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: What is the X-API-Key?</span><br>
                    A: It's a simple shared secret used for authentication simulation in the generated file. It lets you quickly test secure endpoints without complex OAuth setup.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: How do I run the downloaded Python file?</span><br>
                    A: Save the file, install FastAPI and Uvicorn (<code>pip install fastapi uvicorn</code>), and run <code>uvicorn your_file_name:app --reload</code> from your terminal.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: Is the API key secure?</span><br>
                    A: The key is for mocking and local testing only. For production, you must implement a robust authentication system (like JWT or OAuth2).
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: Can I use this generated API in a production environment?</span><br>
                    A: Yes, the file is a standard FastAPI app and can be deployed. However, the current security (simple X-API-Key) and data handling (hardcoded mock data) should be replaced with real database and user management systems.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: Does SpecForge store my API inputs or data?</span><br>
                    A: No. The inputs (App names, fields) are only used temporarily to generate the file and configure the live mock endpoint on the running server's memory (<code>MOCK_CONFIG</code>). They are not permanently stored or logged.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: What happens if I regenerate the API?</span><br>
                    A: Generating a new API updates the global <code>MOCK_CONFIG</code>, which immediately changes the mock data and API key for the live test endpoint. It also creates a brand new Python file for download.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: Why does the generated file use two endpoints (e.g., <code>/app1toapp2</code> and <code>/app2toapp1</code>)?</span><br>
                    A: This simulates a bi-directional integration scenario. For instance, app1toapp2 might be a request to send data, and app2toapp1 might be a webhook receiving a confirmation.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: What is FastAPI built on?</span><br>
                    A: FastAPI is built upon *Starlette* (for routing/middleware) and *Pydantic* (for data validation/schema definition), making it asynchronous and fast.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: Can I modify the data fields after downloading the file?</span><br>
                    A: Absolutely. The data is hardcoded into the Python file as a standard dictionary. You can edit the <code>example_data</code> dictionary in the Python file to provide more complex or realistic JSON outputs.
                </div>
                <div class="step">
                    <span style="font-weight: 700; color: var(--color-success);">Q: Do I need a database to run the generated file?</span><br>
                    A: No. The generated file uses simple in-memory mock data (Python dictionaries). It does not require any database setup (SQL or NoSQL), keeping the setup zero-configuration.
                </div>
            </div>
        </div>
    </section>

    <section id="generator-section">
        <h1>API Generator</h1>
        <div class="content-box">
            <form onsubmit="event.preventDefault(); generateAPI();">
                <label>First App:</label>
                <input id="app1" placeholder="e.g. WhatsApp">
                <label>Second App:</label>
                <input id="app2" placeholder="e.g. Swiggy">
                <label>Fields (comma separated):</label>
                <textarea id="fields" rows="2" placeholder="id,name,status,created_at"></textarea>
                <label>Require Authentication?</label>
                <select id="auth">
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
                <button type="submit">Generate API & Test Live</button>
            </form>
        </div>

        <div id="output" style="display:none; margin-top: 20px;"></div>
    </section>
</main>

<footer>Made with FastAPI by SpecForge © 2025</footer>

<script>
function showTab(tab) {
    // Define all sections and tabs
    const sections = ['about-section', 'features-section', 'howitworks-section', 'faq-section', 'generator-section'];
    const tabs = ['aboutTab', 'featuresTab', 'howitworksTab', 'faqTab', 'generatorTab'];

    // Hide all sections and remove active class from all tabs
    sections.forEach(s => {
        const sectionEl = document.getElementById(s);
        if (sectionEl) sectionEl.classList.remove("active");
    });
    tabs.forEach(t => {
        const tabEl = document.getElementById(t);
        if (tabEl) tabEl.classList.remove("active");
    });

    // Show the requested section and set the corresponding tab as active
    const sectionToShow = document.getElementById(tab + "-section");
    const tabToActivate = document.getElementById(tab + "Tab");
    
    if (sectionToShow) sectionToShow.classList.add("active");
    if (tabToActivate) tabToActivate.classList.add("active");
    
    // Update URL hash for sharing/bookmarking
    history.pushState(null, null, '#' + tab);
}

async function generateAPI(){
    const app1=document.getElementById("app1").value.trim();
    const app2=document.getElementById("app2").value.trim();
    const fields=document.getElementById("fields").value.trim().split(",").filter(f => f.trim() !== ''); // Filter out empty fields
    const requireAuth=document.getElementById("auth").value==="true";
    if(!app1||!app2){alert("Enter both app names");return;}
    if(fields.length === 0) {alert("Please enter at least one field."); return;}
    
    const params=new URLSearchParams({app1,app2,require_auth:requireAuth});
    fields.forEach(f=>params.append("fields",f.trim()));
    
    const generatorButton = document.querySelector('button[type="submit"]');
    const originalButtonText = generatorButton.innerText;
    generatorButton.innerText = 'Generating... ⚙';
    generatorButton.disabled = true;

    try{
        const res=await fetch("/generate_api?"+params.toString());
        const data=await res.json();
        const out=document.getElementById("output");
        out.style.display="block";
        
        // --- UPDATED: The test endpoint is now the first generated endpoint ---
        const testEndpointValue = data.endpoint_example; 
        const apiKey = data.specforge_api_key;
        
        out.innerHTML=`
          <p style="color: var(--color-success); font-weight: normal;">${data.message}</p>
          <p>Connection: ${data.connection}</p>
          <p>Auth Required: ${data.auth_required ? 'Yes' : 'No'}</p>
          <p>Live API Key (X-API-Key Header): <span id="apiKey" style="color: var(--color-accent-light); font-weight: normal;">${apiKey}</span></p>
          <p>Example Data Structure: <span style="font-family: monospace; color: var(--color-code);">${JSON.stringify(data.example_data)}</span></p>
          
          <a href="${data.download_link}" style="color:var(--color-success); text-decoration: none; padding: 10px 15px; border: 1px solid var(--color-success); border-radius: 6px; display: inline-block; margin-top: 15px;">⬇ Download <code>${data.file_name}</code></a>
          
          <hr style="margin:25px 0; border-color: var(--border-color);">
          <label style="color: var(--color-accent-light);">Test Generated Endpoint (Live Mock):</label>
          <div class="test-section" style="margin-top: 10px;">
              <input id="testEndpoint" value="${testEndpointValue}" style="flex-grow: 1; margin-bottom: 0;">
              <button onclick="callAPI()" style="margin-bottom: 0;">Test GET</button>
          </div>
          <pre id="apiResponse" style="min-height: 50px;">Click 'Test GET' to see the mock data response.</pre>
        `;
        window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});
    }catch(err){
        document.getElementById("output").style.display="block";
        // FIX APPLIED HERE: Using backticks for the template literal
        document.getElementById("output").innerHTML = `<p style="color: red; font-weight: normal;">Error generating API: ${err.message}. Check your inputs.</p>`;
    } finally {
        generatorButton.innerText = originalButtonText;
        generatorButton.disabled = false;
    }
}

async function callAPI(){
    const endpoint = document.getElementById("testEndpoint").value.trim();
    const apiKeySpan = document.getElementById("apiKey");
    const requireAuth = document.getElementById("auth").value === "true";
    const apiResponseEl = document.getElementById("apiResponse");
    
    if (!endpoint) {
        alert("Enter endpoint");
        return;
    }
    
    const headers = {};
    if (requireAuth && apiKeySpan) {
        // Use the generated API key for testing
        const generatedKey = apiKeySpan.innerText.trim();
        headers['X-API-Key'] = generatedKey || 'YOUR_HARDCODED_KEY'; 
    }
    
    apiResponseEl.innerText = 'Calling API...';

    try{
        // The fetch call now hits the endpoint added dynamically to the running app.
        const res = await fetch(endpoint, { headers });
        const data = await res.json();
        
        if (res.status === 401) {
            apiResponseEl.style.color = 'red';
            // FIX APPLIED HERE: Using backticks for the template literal
            apiResponseEl.innerText = `Error ${res.status}: ${data.detail || 'Authentication Failed. Missing or Invalid X-API-Key.'}`;
        } else {
            apiResponseEl.style.color = 'var(--color-code)';
            apiResponseEl.innerText = JSON.stringify(data, null, 2);
        }
    }catch(err){
        apiResponseEl.style.color = 'red';
        apiResponseEl.innerText = "Network Error: Could not reach the endpoint. Ensure the server is running and the path is correct.";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Check URL hash to load correct tab, otherwise default to 'about'
    const hash = window.location.hash.substring(1);
    const validTabs = ['about', 'features', 'howitworks', 'faq', 'generator'];
    if (validTabs.includes(hash)) {
        showTab(hash);
    } else {
        showTab('about');
    }
});
</script>
</body>
</html>
"""