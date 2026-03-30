import os, sqlite3
from flask import Flask, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin-is-back-2026'
DB_PATH = os.path.join(os.path.dirname(__file__), 'notes_pro.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- API РЕГІСТРАЦІЯ/ВХІД ---
@app.route("/api/user_info")
def user_info():
    if 'user_id' not in session: return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "username": session['username'], "role": session.get('role', 'user')})

@app.route("/login", methods=["POST"])
def login():
    d = request.get_json(); conn = get_db()
    u = conn.execute('SELECT * FROM user WHERE username = ?', (d['username'],)).fetchone()
    if u and check_password_hash(u['password_hash'], d['password']):
        session['user_id'], session['username'], session['role'] = u['id'], u['username'], u['role']
        return jsonify({"success": True})
    return jsonify({"error": "Невірно"}), 401

@app.route("/register", methods=["POST"])
def register():
    d = request.get_json()
    try:
        with get_db() as conn:
            conn.execute('INSERT INTO user (username, password_hash) VALUES (?, ?)', (d['username'], generate_password_hash(d['password'])))
            conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"error": "Зайнято"}), 400

@app.route("/logout")
def logout(): session.clear(); return redirect('/')

# --- НОТАТКИ ---
@app.route("/all_notes")
def fetch_notes():
    if 'user_id' not in session: return jsonify([])
    conn = get_db()
    rows = conn.execute('SELECT * FROM note WHERE user_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    return jsonify([{"id": r['id'], "text": r['text']} for r in rows])

@app.route("/add_note", methods=["POST"])
def add_note():
    txt = request.args.get("content")
    with get_db() as conn:
        conn.execute('INSERT INTO note (text, user_id) VALUES (?, ?)', (txt, session['user_id']))
        conn.commit()
    return jsonify({"success": True})

@app.route("/edit_note/<int:nid>", methods=["POST"])
def edit_note(nid):
    txt = request.args.get("content")
    with get_db() as conn:
        conn.execute('UPDATE note SET text = ? WHERE id = ? AND user_id = ?', (txt, nid, session['user_id']))
        conn.commit()
    return jsonify({"success": True})

@app.route("/delete_note/<int:nid>", methods=["DELETE"])
def delete_note(nid):
    with get_db() as conn:
        if session.get('role') == 'admin':
            conn.execute('DELETE FROM note WHERE id = ?', (nid,))
        else:
            conn.execute('DELETE FROM note WHERE id = ? AND user_id = ?', (nid, session['user_id']))
        conn.commit()
    return jsonify({"success": True})

# --- АДМІН-ФУНКЦІЇ ---
@app.route("/api/admin/users")
def admin_users():
    if session.get('role') != 'admin': return jsonify([]), 403
    conn = get_db()
    res = conn.execute('SELECT u.id, u.username, COUNT(n.id) as count FROM user u LEFT JOIN note n ON u.id = n.user_id GROUP BY u.id').fetchall()
    return jsonify([{"id": r['id'], "username": r['username'], "count": r['count']} for r in res])

@app.route("/")
def index(): return HTML_BODY

HTML_BODY = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Notes UX</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"><style>
:root{--p:#4a90e2;--bg:#f0f4f8;--txt:#2d3748;--c:#fff;--b:#e2e8f0}
[data-theme="dark"]{--bg:#1a202c;--txt:#f7fafc;--c:#2d3748;--b:#4a5568}
body{font-family:sans-serif;background:var(--bg);color:var(--txt);margin:0;padding:20px;display:flex;flex-direction:column;align-items:center;transition:.3s}
.h{width:100%;max-width:900px;display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}
.cnt{width:100%;max-width:900px}
.ib{background:var(--c);padding:5px 15px;border-radius:15px;border:2px solid var(--p);display:flex;gap:10px;margin-bottom:30px}
#nt, .ed-in{flex:1;border:none;outline:0;background:0 0;color:var(--txt);font-size:18px;padding:12px;width:100%}
.abtn{background:var(--p);color:#fff;border:none;padding:0 25px;border-radius:12px;cursor:pointer;font-weight:700;font-size:24px}
#l{display:grid;grid-template-columns:repeat(auto-fill, minmax(280px, 1fr));gap:20px;width:100%}
.cd{background:var(--c);border:1px solid var(--b);padding:20px;border-radius:20px;display:flex;flex-direction:column;transition:.2s}
.f{display:flex;justify-content:flex-end;gap:15px;margin-top:15px;border-top:1px solid var(--b);padding-top:10px}
.icn{background:none;border:none;cursor:pointer;font-size:16px;color:#94a3b8}
.auth{background:#fff;padding:40px;border-radius:25px;box-shadow:0 15px 30px rgba(0,0,0,.1);width:320px;text-align:center;margin-top:80px}
.auth input{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:10px;box-sizing:border-box}
.auth button{width:100%;padding:12px;background:var(--p);color:#fff;border:none;border-radius:10px;cursor:pointer;font-weight:700;margin-top:10px}
</style></head><body><div id="app" style="width:100%;display:flex;flex-direction:column;align-items:center"></div>
<script>
let u = null;
async function init(){
    const r = await fetch('/api/user_info'); u = await r.json();
    u.logged_in ? drawMain() : drawAuth();
}
function th(){const d=document.documentElement; const n=d.getAttribute('data-theme')==='dark'?'light':'dark'; d.setAttribute('data-theme',n); localStorage.setItem('t',n);}
if(localStorage.getItem('t')==='dark')document.documentElement.setAttribute('data-theme','dark');

function drawAuth(){
    let isL = true; const app = document.getElementById('app');
    app.innerHTML = '<div class="auth"><h2 id="at">Вхід</h2><input id="au" placeholder="Логін"><input type="password" id="ap" placeholder="Пароль"><button id="ab">Увійти</button><p id="as" style="cursor:pointer;margin-top:15px;color:#64748b;font-size:14px">Реєстрація</p></div>';
    as.onclick = () => { isL=!isL; at.innerText=isL?'Вхід':'Реєстрація'; ab.innerText=isL?'Увійти':'Створити'; as.innerText=isL?'Реєстрація':'Вхід'; };
    ab.onclick = async () => {
        const res = await fetch(isL?'/login':'/register', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:au.value, password:ap.value})});
        const d = await res.json(); if(d.success) init(); else alert(d.error);
    };
}
function drawMain(){
    const app = document.getElementById('app');
    let h = '<div class="h"><div>Привіт, <b>'+u.username+'</b>!</div><div style="display:flex;gap:15px;align-items:center">';
    if(u.role === 'admin') h += '<button onclick="admPanel()" style="background:#f59e0b;color:#fff;border:none;padding:5px 10px;border-radius:8px;cursor:pointer;font-weight:700">Адмін</button>';
    h += '<i class="fa-solid fa-moon" onclick="th()" style="cursor:pointer;font-size:18px"></i><a href="/logout" style="color:red;text-decoration:none;font-weight:700">Вийти</a></div></div>';
    h += '<div class="cnt"><h1>📝 Нотатки</h1><div class="ib"><input id="nt" placeholder="Що нового?"><button class="abtn" onclick="addN()">+</button></div><div id="l"></div></div>';
    app.innerHTML = h; loadN();
    nt.onkeyup = (e) => { if(e.key==='Enter') addN(); };
}
async function loadN(){
    const r = await fetch('/all_notes'); const d = await r.json(); const list = document.getElementById('l');
    list.innerHTML = d.length ? '' : '<div style="grid-column:1/-1;text-align:center;opacity:.5;padding:40px">Немає записів</div>';
    d.forEach(n => {
        let card = document.createElement('div'); card.className = 'cd'; card.id = 'n'+n.id;
        card.innerHTML = '<div class="tx">'+n.text+'</div><div class="f"><button class="icn" onclick="stEd('+n.id+')"><i class="fa-solid fa-pen"></i></button><button class="icn" onclick="delN('+n.id+')"><i class="fa-solid fa-trash"></i></button></div>';
        list.appendChild(card);
    });
}
async function admPanel(){
    const r = await fetch('/api/admin/users'); const users = await r.json(); const list = document.getElementById('l');
    list.innerHTML = '<div style="grid-column:1/-1;background:var(--c);padding:20px;border-radius:15px;border:1px solid var(--p)"><h3>Студенти коледжу:</h3>';
    users.forEach(us => {
        list.innerHTML += '<div style="display:flex;justify-content:space-between;padding:10px;border-bottom:1px solid var(--b)"><span>' + us.username + ' (' + us.count + ')</span><button onclick="drawMain()" style="background:var(--p);color:#fff;border:none;padding:4px 8px;border-radius:5px;cursor:pointer">Ок</button></div>';
    });
    list.innerHTML += '<button onclick="drawMain()" style="width:100%;margin-top:15px;background:#94a3b8;color:#fff;border:none;padding:10px;border-radius:10px;cursor:pointer">Назад</button></div>';
}
function stEd(id){
    const c = document.getElementById('n'+id); const t = c.querySelector('.tx'); const old = t.innerText;
    c.querySelector('.f').style.display = 'none';
    t.innerHTML = '<input class="ed-in" id="e'+id+'" value="'+old+'"><button onclick="svEd('+id+')" style="background:var(--p);color:#fff;border:none;padding:5px;border-radius:5px;cursor:pointer">Ок</button>';
    const i = document.getElementById('e'+id); i.focus();
    i.onkeyup = (e) => { if(e.key==='Enter') svEd(id); };
}
async function svEd(id){
    const v = document.getElementById('e'+id).value.trim();
    if(v){ await fetch('/edit_note/'+id+'?content='+encodeURIComponent(v), {method:'POST'}); loadN(); }
}
async function delN(id){
    const c = document.getElementById('n'+id); c.style.opacity = '0.3';
    await fetch('/delete_note/'+id, {method:'DELETE'}); c.remove();
}
async function addN(){ const v = nt.value.trim(); if(!v) return; await fetch('/add_note?content='+encodeURIComponent(v), {method:'POST'}); nt.value=''; loadN(); }
init();
</script></body></html>
"""