from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "notes_db.json")

def load_data():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route("/all_notes")
def get_all_notes():
    return jsonify(load_data())

@app.route("/add_note", methods=["POST"])
def add_new_note():
    content = request.args.get("content")
    if not content: return jsonify({"error": "No content"}), 400
    notes = load_data()
    new_obj = {"id": max([n["id"] for n in notes], default=0) + 1, "text": content}
    notes.append(new_obj)
    save_data(notes)
    return jsonify(new_obj)

@app.route("/delete_note/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    notes = load_data()
    updated = [n for n in notes if n["id"] != note_id]
    save_data(updated)
    return jsonify({"status": "deleted"})

@app.route("/edit_note/<int:note_id>", methods=["PUT"])
def edit_note(note_id):
    new_content = request.args.get("new_content")
    if not new_content: return jsonify({"error": "No content"}), 400
    notes = load_data()
    for note in notes:
        if note["id"] == note_id:
            note["text"] = new_content
            save_data(notes)
            return jsonify(note)
    return jsonify({"error": "not found"}), 404

# Змінна з HTML кодом (важливо закрити лапки в кінці)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ЧХТК | Notes Manager</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --primary: #4a90e2; --bg: #f8fafc; --text: #1e293b; --card-bg: #ffffff; --border: #e2e8f0; }
        [data-theme="dark"] { --bg: #0f172a; --text: #f1f5f9; --card-bg: #1e293b; --border: #334155; }
        body { font-family: 'Segoe UI', sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; transition: 0.3s; }
        .header-nav { width: 100%; max-width: 800px; display: flex; justify-content: flex-end; margin-bottom: 20px; }
        #theme-toggle { background: var(--card-bg); border: 1px solid var(--border); color: var(--text); padding: 10px; border-radius: 12px; cursor: pointer; }
        .container { width: 100%; max-width: 800px; }
        .input-section { background: var(--card-bg); padding: 12px; border-radius: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid var(--border); display: flex; gap: 10px; margin-bottom: 40px; }
        input[type="text"] { flex: 1; border: none; padding: 10px; font-size: 1rem; outline: none; background: transparent; color: var(--text); }
        .btn-add { background: var(--primary); border-radius: 15px; padding: 10px 25px; color: white; border: none; cursor: pointer; }
        #notesList { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; width: 100%; }
        @media (max-width: 600px) { #notesList { grid-template-columns: 1fr; } }
        .note-card { background: var(--card-bg); border-radius: 20px; padding: 20px; border: 1px solid var(--border); display: flex; flex-direction: column; min-height: 150px; transition: 0.3s; }
        .note-text { font-size: 1rem; line-height: 1.5; word-break: break-word; flex-grow: 1; }
        .note-footer { display: flex; justify-content: flex-end; padding-top: 15px; border-top: 1px solid var(--border); margin-top: 15px; }
        .btn-action { background: var(--bg); color: #64748b; width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-left: 8px; border: 1px solid var(--border); cursor: pointer; }
        textarea { width: 100%; background: var(--bg); color: var(--text); border: 1px solid var(--primary); border-radius: 12px; padding: 10px; resize: none; box-sizing: border-box; }
        footer { margin-top: 50px; color: #94a3b8; font-size: 0.75rem; letter-spacing: 2px; text-align: center; }
    </style>
</head>
<body>
    <div class="header-nav"><button id="theme-toggle" onclick="toggleTheme()"><i id="theme-icon" class="fa-solid fa-moon"></i></button></div>
    <div class="container">
        <h1>📝 Нотатки</h1>
        <div class="input-section">
            <input type="text" id="noteText" placeholder="Додати запис...">
            <button class="btn-add" onclick="addNote()"><i class="fa-solid fa-plus"></i></button>
        </div>
        <div id="notesList"></div>
    </div>
    <footer>ЧХТК • notes manager • 2026</footer>
    <script>
        function toggleTheme() {
            const cur = document.documentElement.getAttribute('data-theme');
            const next = cur === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            document.getElementById('theme-icon').className = next === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
        const saved = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', saved);
        document.getElementById('theme-icon').className = saved === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';

        async function loadNotes() {
            const res = await fetch('/all_notes');
            const notes = await res.json();
            const list = document.getElementById('notesList');
            list.innerHTML = '';
            notes.forEach(n => {
                list.innerHTML += `
                    <div class="note-card" id="note-${n.id}">
                        <div class="note-text">${n.text}</div>
                        <div class="note-footer">
                            <button class="btn-action" onclick="enterEdit(${n.id}, '${n.text.replace(/'/g, "\\'")}')"><i class="fa-solid fa-pen"></i></button>
                            <button class="btn-action" onclick="deleteNote(${n.id})"><i class="fa-solid fa-trash"></i></button>
                        </div>
                    </div>`;
            });
        }
        async function addNote() {
            const input = document.getElementById('noteText');
            if (!input.value.trim()) return;
            await fetch('/add_note?content=' + encodeURIComponent(input.value), { method: 'POST' });
            input.value = '';
            loadNotes();
        }
        async function deleteNote(id) {
            if(confirm('Видалити?')) { await fetch('/delete_note/' + id, { method: 'DELETE' }); loadNotes(); }
        }
        function enterEdit(id, old) {
            const card = document.getElementById('note-' + id);
            card.innerHTML = `<textarea id="edit-${id}" rows="4">${old}</textarea>
                <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px;">
                    <button style="background:#94a3b8;color:white;border:none;padding:5px 10px;border-radius:8px;" onclick="loadNotes()">Скасувати</button>
                    <button style="background:#22c55e;color:white;border:none;padding:5px 10px;border-radius:8px;" onclick="saveEdit(${id})">Зберегти</button>
                </div>`;
        }
        async function saveEdit(id) {
            const val = document.getElementById('edit-' + id).value;
            await fetch('/edit_note/' + id + '?new_content=' + encodeURIComponent(val), { method: 'PUT' });
            loadNotes();
        }
        loadNotes();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)