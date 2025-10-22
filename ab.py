# ctf_more_fun.py
from flask import Flask, request, render_template_string, send_file, abort, jsonify, Response
import hmac, hashlib, io, base64

app = Flask(__name__)

SECRET_KEY = b"CHANGE_THIS_TO_A_LONG_RANDOM_KEY"
CHALLENGE_ID = "shadowbreak_mission"
# Step tokens (server-side expected values)
STEP1_TOKEN = "secret_message"       # ROT13(frperg_zrffntr)
# STEP2 will be base64 of "next_path:/hidden" => bmV4dF9wYXRoOi9oaWRkZW4=
STEP2_TOKEN_DECODED = "next_path:/hidden"

def team_flag(team_id: str, challenge_id: str) -> str:
    msg = f"{team_id}|{challenge_id}".encode()
    sig = hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()[:12]
    return f"flag{{{challenge_id}_{team_id}_{sig}}}"

# --- Routes ---

@app.route("/")
def index():
    html = """
    <h1>Operation ShadowBreak — Mission Micro</h1>
    <p>A hacker left a short note. Follow the steps to capture the flag.</p>
    <ul>
      <li>Step 1: Download the note and decode it (ROT13)</li>
      <li>Step 2: Submit the decoded token to receive the next clue (Base64)</li>
      <li>Step 3: Use the final clue to make a special request and get your team flag</li>
    </ul>
    <p><a href="/note.txt">Download the note</a></p>
    <hr>
    <h3>Submit token (Step 1 → Step 2)</h3>
    <form action="/step2" method="post">
      Team ID: <input name="team_id" placeholder="team1" required><br><br>
      Token: <input name="token" placeholder="decoded token from note" required><br><br>
      <button>Submit</button>
    </form>
    """
    return render_template_string(html)

@app.route("/note.txt")
def note():
    # Clue only (ROT13 text)
    content = "found this on the hacker's desk:\n\nfrperg_zrffntr\n\ntry rot13\n"
    # Use Response and set Content-Disposition to force download across browsers/Flask versions
    resp = Response(content, mimetype="text/plain")
    resp.headers["Content-Disposition"] = 'attachment; filename="note.txt"'
    return resp

@app.route("/step2", methods=["POST"])
def step2():
    team_id = request.form.get("team_id","").strip()
    token = request.form.get("token","").strip()
    if not team_id or not token:
        return "Missing team_id or token", 400
    if token != STEP1_TOKEN:
        return "Incorrect token for Step 1", 403

    # Provide next clue (Base64 of "next_path:/hidden") — participants must decode it
    clue = base64.b64encode(STEP2_TOKEN_DECODED.encode()).decode()
    # show small hint about using CyberChef or base64 decode
    return render_template_string("""
      <h3>Good job — Step 2 unlocked</h3>
      <p>Clue (Base64): <code>{{clue}}</code></p>
      <p>Decode the Base64 to find the next path. Hint: CyberChef or `base64 -d`</p>
      <hr>
      <p>When you get the next path, you must access it with a special header to retrieve your flag.</p>
      <p>Final step: Use a tool that can set custom headers (curl, Postman, Burp).</p>
    """, clue=clue)

@app.route("/hidden")
def hidden():
    # This endpoint will only return the flag if the correct custom header is present:
    # X-Shadow-Token: open_sesame
    # and a team_id param is present
    team_id = request.args.get("team_id","").strip()
    hdr = request.headers.get("X-Shadow-Token","")
    if not team_id:
        return "Missing team_id query parameter. Example: /hidden?team_id=team1", 400
    if hdr != "open_sesame":
        return "You need to include a special header to access the flag. Hint: X-Shadow-Token: open_sesame", 403

    flag = team_flag(team_id, CHALLENGE_ID)
    return render_template_string("""
      <h2>Mission Complete</h2>
      <p>Correct header received. Here is your team flag:</p>
      <pre>{{flag}}</pre>
    """, flag=flag)

@app.route("/health")
def health():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
