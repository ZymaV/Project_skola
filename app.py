# Import potřebných knihoven
import matplotlib
matplotlib.use("Agg")
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os  # Pro kontrolu existence databáze
import matplotlib.pyplot as plt
import io
import base64

# Inicializace Flask aplikace
app = Flask(__name__)
app.secret_key = "tajny_klic"  # Nastavení tajného klíče pro session

# 🟢 Funkce pro připojení k databázi herních výsledků
def get_scores_db_connection():
    """
    Pokusí se připojit k databázi "database.db".
    Pokud soubor databáze neexistuje, vrátí None.
    """
    if not os.path.exists("database.db"):
        return None  # Pokud databáze neexistuje, vracíme None
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row  # Umožní přístup k datům jako ke slovníku
    return conn

# 🟢 Funkce pro připojení k databázi přihlášení (loginInfo.db)
def get_login_db_connection():
    """
    Připojí se k databázi "loginInfo.db".
    """
    conn = sqlite3.connect("loginInfo.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_color_mapping(user_list):
    """
    Given a list (or set) of usernames, return a mapping from username to a color.
    Uses a fixed list of colors.
    """
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    mapping = {}
    for i, user in enumerate(sorted(user_list)):
        mapping[user] = colors[i % len(colors)]
    return mapping

def generate_bar_chart_score(color_mapping):
    conn = get_scores_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, points FROM scores ORDER BY points DESC LIMIT 5")
    data = cursor.fetchall()
    conn.close()
    names = [row['username'] for row in data]
    scores = [row['points'] for row in data]
    # Use the provided mapping to get consistent colors.
    colors_list = [color_mapping[name] for name in names]
    
    plt.figure(figsize=(6,4))
    plt.bar(names, scores, color=colors_list)
    plt.xlabel('Uživatel')
    plt.ylabel('Skóre')
    plt.title('Nejvyšší skóre')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return chart_base64

def generate_bar_chart_turns(color_mapping):
    conn = get_scores_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, turns FROM scores ORDER BY turns ASC LIMIT 5")
    data = cursor.fetchall()
    conn.close()
    names = [row['username'] for row in data]
    turns = [row['turns'] for row in data]
    colors_list = [color_mapping[name] for name in names]
    
    plt.figure(figsize=(6,4))
    plt.bar(names, turns, color=colors_list)
    plt.xlabel('Uživatel')
    plt.ylabel('Tahů')
    plt.title('Nejnižší počet tahů')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return chart_base64

def generate_bar_chart_time(color_mapping):
    conn = get_scores_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, time FROM scores ORDER BY time ASC LIMIT 5")
    data = cursor.fetchall()
    conn.close()
    names = [row['username'] for row in data]
    times = [row['time'] for row in data]
    colors_list = [color_mapping[name] for name in names]
    
    plt.figure(figsize=(6,4))
    plt.bar(names, times, color=colors_list)
    plt.xlabel('Uživatel')
    plt.ylabel('Čas (s)')
    plt.title('Nejnižší herní čas')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return chart_base64

def generate_pie_chart(color_mapping):
    # Vybereme top 20 hráčů podle skóre.
    conn = get_scores_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, points FROM scores ORDER BY points DESC LIMIT 20")
    data = cursor.fetchall()
    conn.close()
    
    names = [row['username'] for row in data]
    scores = [row['points'] for row in data]
    colors_list = [color_mapping[name] for name in names]

    # Sloučíme záznamy se stejnou barvou:
    # sečteme skóre a přidáme jména pouze jednou.
    combined = {}
    for name, score, color in zip(names, scores, colors_list):
        if color not in combined:
            combined[color] = {"names": [name], "score": score}
        else:
            if name not in combined[color]["names"]:
                combined[color]["names"].append(name)
            combined[color]["score"] += score

    new_colors = []
    new_names = []
    new_scores = []
    for color, values in combined.items():
        new_colors.append(color)
        new_names.append(", ".join(values["names"]))
        new_scores.append(values["score"])

    plt.figure(figsize=(6,6))
    plt.pie(new_scores, labels=new_names, autopct='%1.1f%%', startangle=140, colors=new_colors)
    plt.title('Rozložení skóre')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return chart_base64


# 🟢 Domovská stránka
@app.route("/")
def home():
    """
    Hlavní stránka aplikace. Zobrazuje přihlašovací formulář.
    """
    return render_template("home.html", logged_in="username" in session, error=None)

# 🟢 Přihlášení uživatele
@app.route("/login", methods=["POST"])
def login():
    """
    Zpracuje přihlášení uživatele.
    Pokud databáze loginInfo.db neexistuje, zobrazí chybu.
    """
    username = request.form["username"]
    password = request.form["password"]

    if not os.path.exists("loginInfo.db"):
        return render_template("home.html", error="Chyba: Databáze přihlášení neexistuje!", logged_in=False)

    conn = get_login_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["username"] = username
        return redirect(url_for("game"))
    else:
        return render_template("home.html", error="Chybné přihlašovací údaje", logged_in=False)

# 🟢 Registrace uživatele (PŘIDÁNO!)
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Zpracuje registraci nového uživatele.
    Pokud databáze loginInfo.db neexistuje, zobrazí chybu.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not os.path.exists("loginInfo.db"):
            return render_template("register.html", error="Chyba: Databáze přihlášení neexistuje!")

        conn = get_login_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Uživatel již existuje!")

    return render_template("register.html", error=None)

# 🟢 Statistiky – zobrazí top 5 hráčů, pokud databáze existuje
@app.route('/stats', endpoint='stats')
def stats_route():
    conn = get_scores_db_connection()
    if conn is None:
        return "Database not found", 404
    cursor = conn.cursor()

    # Získáme top 5 podle skóre
    cursor.execute("SELECT username, points, turns, time FROM scores ORDER BY points DESC LIMIT 5")
    score_board = cursor.fetchall()

    # Získáme top 5 podle nejnižšího počtu tahů
    cursor.execute("SELECT username, points, turns, time FROM scores ORDER BY turns ASC LIMIT 5")
    turns_board = cursor.fetchall()

    # Získáme top 5 podle nejkratšího času
    cursor.execute("SELECT username, points, turns, time FROM scores ORDER BY time ASC LIMIT 5")
    time_board = cursor.fetchall()

    # Získáme 20 nejnovějších záznamů
    cursor.execute("SELECT username, points, turns, time FROM scores ORDER BY id DESC LIMIT 20")
    recent_board = cursor.fetchall()

    conn.close()
    return render_template('stats.html',
                           score_board=score_board,
                           turns_board=turns_board,
                           time_board=time_board,
                           recent_board=recent_board)


# 🟢 Generování grafů
@app.route('/graphs')
def graphs():
    # Get union of usernames from all queries to build a consistent color mapping.
    conn = get_scores_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM scores ORDER BY points DESC LIMIT 5")
    score_users = [row['username'] for row in cursor.fetchall()]
    cursor.execute("SELECT username FROM scores ORDER BY turns ASC LIMIT 5")
    turns_users = [row['username'] for row in cursor.fetchall()]
    cursor.execute("SELECT username FROM scores ORDER BY time ASC LIMIT 5")
    time_users = [row['username'] for row in cursor.fetchall()]
    cursor.execute("SELECT username FROM scores ORDER BY id DESC LIMIT 5")
    recent_users = [row['username'] for row in cursor.fetchall()]
    conn.close()
    
    all_users = set(score_users + turns_users + time_users + recent_users)
    color_mapping = create_color_mapping(all_users)
    
    # Generate charts using the same color mapping.
    bar_chart_score = generate_bar_chart_score(color_mapping)
    bar_chart_turns = generate_bar_chart_turns(color_mapping)
    bar_chart_time = generate_bar_chart_time(color_mapping)
    pie_chart = generate_pie_chart(color_mapping)
    
    return render_template('graphs.html',
                           bar_chart_score=bar_chart_score,
                           bar_chart_turns=bar_chart_turns,
                           bar_chart_time=bar_chart_time,
                           pie_chart=pie_chart,
                           logged_in=True)


# 🟢 Odhlášení uživatele
@app.route("/logout")
def logout():
    """
    Odhlásí uživatele a přesměruje ho zpět na přihlašovací stránku.
    """
    session.pop("username", None)
    return redirect(url_for("home"))

# 🟢 Hra Snake
@app.route("/game")
def game():
    """
    Zobrazí stránku s hrou Snake, pokud je uživatel přihlášen.
    """
    if "username" not in session:
        return redirect(url_for("home"))
    return render_template("game.html", username=session["username"], logged_in=True)

# 🟢 Spuštění aplikace
if __name__ == "__main__":
    app.run(debug=True)
