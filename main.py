import os
import json
import uuid
import sqlite3

from flask import Flask, render_template, redirect, request, url_for, flash, g


app = Flask(__name__)
app.secret_key = "supersecretkeyishere"
DATABASE = 'urls.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS urls (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       short_url TEXT UNIQUE,
                       long_url TEXT,
                       visits INTEGER DEFAULT 0
                       )""")
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_short_url():
    return uuid.uuid4().hex[:8]


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        long_url = request.form.get("long_url", "").strip()
        custom_alias = request.form.get("custom_alias", "").strip()
        
        if not long_url:
            flash("Please provide a valid URL.")
            return redirect(url_for('index'))

        db = get_db()
        cursor = db.cursor()

        if custom_alias:
            cursor.execute("SELECT * FROM urls WHERE short_url = ?", (custom_alias,))
            if cursor.fetchone():
                flash("Custom alias already taken. Please choose another.")
                return redirect(url_for("index"))
            short_url = custom_alias
        else:
            short_url = generate_short_url()

        cursor.execute("INSERT INTO urls (short_url, long_url) VALUES (?, ?)", (short_url, long_url))
        db.commit()

        full_short_url = request.url_root + short_url
        return render_template("index.html", short_url=full_short_url)
    
    return render_template("index.html")


@app.route("/<short_url>")
def redirect_url(short_url):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT long_url, visits FROM urls WHERE short_url = ?", (short_url,))
    result = cursor.fetchone()
    
    if result:
        long_url, visits = result
        cursor.execute("UPDATE urls SET visits = visits + 1 WHERE short_url = ?", (short_url,))
        db.commit()
        return redirect(long_url)
    return "URL not found", 404
    

@app.route("/analytics")
def analytics():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT short_url, long_url, visits FROM urls ORDER BY visits DESC")
    data = cursor.fetchall()
    return render_template("analytics.html", data=data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)