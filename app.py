from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "inkora.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "inkora-dev-secret-change-me"
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        image_filename TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS post_reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        reaction TEXT NOT NULL CHECK(reaction IN ('like', 'dislike')),
        created_at TEXT NOT NULL,
        UNIQUE(post_id, user_id),
        FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS post_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        created_at TEXT NOT NULL,
        UNIQUE(post_id, user_id),
        FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        post_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    # Lightweight migration for databases created by an earlier version.
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(posts)").fetchall()]
    if "image_filename" not in columns:
        conn.execute("ALTER TABLE posts ADD COLUMN image_filename TEXT")
    conn.commit()
    conn.close()


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    user = conn.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped



def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_post_image(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        return False
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    safe_name = secure_filename(file.filename)
    stem = Path(safe_name).stem or "image"
    ext = Path(safe_name).suffix.lower()
    unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{stem}{ext}"
    file.save(UPLOAD_FOLDER / unique_name)
    return unique_name


def post_reaction_stats(conn, post_id, user_id=None):
    likes = conn.execute(
        "SELECT COUNT(*) FROM post_reactions WHERE post_id = ? AND reaction = 'like'", (post_id,)
    ).fetchone()[0]
    dislikes = conn.execute(
        "SELECT COUNT(*) FROM post_reactions WHERE post_id = ? AND reaction = 'dislike'", (post_id,)
    ).fetchone()[0]
    avg = conn.execute(
        "SELECT AVG(rating) FROM post_ratings WHERE post_id = ?", (post_id,)
    ).fetchone()[0]
    rating_count = conn.execute(
        "SELECT COUNT(*) FROM post_ratings WHERE post_id = ?", (post_id,)
    ).fetchone()[0]
    user_reaction = None
    user_rating = None
    if user_id:
        row = conn.execute(
            "SELECT reaction FROM post_reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id)
        ).fetchone()
        user_reaction = row["reaction"] if row else None
        row = conn.execute(
            "SELECT rating FROM post_ratings WHERE post_id = ? AND user_id = ?", (post_id, user_id)
        ).fetchone()
        user_rating = row["rating"] if row else None
    return {
        "likes": likes,
        "dislikes": dislikes,
        "average_rating": round(avg, 1) if avg is not None else 0,
        "rating_count": rating_count,
        "user_reaction": user_reaction,
        "user_rating": user_rating,
    }


def post_with_author(conn, post_id):

    return conn.execute("""
        SELECT p.*, u.name AS author_name, u.email AS author_email
        FROM posts p
        JOIN users u ON u.id = p.author_id
        WHERE p.id = ?
    """, (post_id,)).fetchone()


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/")
def home():
    conn = get_db()
    posts = conn.execute("""
        SELECT p.*, u.name AS author_name,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count,
               (SELECT COUNT(*) FROM post_reactions r WHERE r.post_id = p.id AND r.reaction = 'like') AS like_count,
               (SELECT COUNT(*) FROM post_reactions r WHERE r.post_id = p.id AND r.reaction = 'dislike') AS dislike_count,
               (SELECT AVG(pr.rating) FROM post_ratings pr WHERE pr.post_id = p.id) AS average_rating,
               (SELECT COUNT(*) FROM post_ratings pr WHERE pr.post_id = p.id) AS rating_count
        FROM posts p
        JOIN users u ON u.id = p.author_id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("index.html", posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
        elif len(name) < 2:
            flash("Name must contain at least 2 characters.", "error")
        elif len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
                    (name, email, generate_password_hash(password), datetime.now().isoformat(timespec="seconds"))
                )
                conn.commit()
                flash("Account created successfully. You can now log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists.", "error")
            finally:
                conn.close()

    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Welcome back to Inkora!", "success")
            next_url = request.args.get("next") or url_for("home")
            if not next_url.startswith("/"):
                next_url = url_for("home")
            return redirect(next_url)

        flash("Invalid email or password.", "error")

    return render_template("auth.html", mode="login")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        image = request.files.get("image")
        if not title or not content:
            flash("Title and content are required.", "error")
        elif len(title) > 150:
            flash("Title must be 150 characters or less.", "error")
        else:
            image_filename = save_post_image(image)
            if image_filename is False:
                flash("Image must be PNG, JPG, JPEG, GIF or WEBP.", "error")
                return render_template("editor.html", mode="create", post=None)
            now = datetime.now().isoformat(timespec="seconds")
            conn = get_db()
            cur = conn.execute(
                "INSERT INTO posts (title, content, author_id, image_filename, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (title, content, session["user_id"], image_filename, now, now)
            )
            conn.commit()
            post_id = cur.lastrowid
            conn.close()
            flash("Your post has been published.", "success")
            return redirect(url_for("post_detail", post_id=post_id))
    return render_template("editor.html", mode="create", post=None)


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    conn = get_db()
    post = post_with_author(conn, post_id)
    if not post:
        conn.close()
        return render_template("404.html"), 404
    comments = conn.execute("""
        SELECT c.*, u.name AS author_name
        FROM comments c
        JOIN users u ON u.id = c.author_id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    """, (post_id,)).fetchall()
    reaction_stats = post_reaction_stats(conn, post_id, session.get("user_id"))
    conn.close()
    return render_template("post.html", post=post, comments=comments, reaction_stats=reaction_stats)


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    conn = get_db()
    post = post_with_author(conn, post_id)
    if not post:
        conn.close()
        return render_template("404.html"), 404
    if post["author_id"] != session["user_id"]:
        conn.close()
        flash("You can only edit your own posts.", "error")
        return redirect(url_for("post_detail", post_id=post_id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        image = request.files.get("image")
        if not title or not content:
            flash("Title and content are required.", "error")
        else:
            image_filename = save_post_image(image)
            if image_filename is False:
                flash("Image must be PNG, JPG, JPEG, GIF or WEBP.", "error")
                conn.close()
                return render_template("editor.html", mode="edit", post=post)
            if image_filename:
                conn.execute(
                    "UPDATE posts SET title = ?, content = ?, image_filename = ?, updated_at = ? WHERE id = ?",
                    (title, content, image_filename, datetime.now().isoformat(timespec="seconds"), post_id)
                )
            else:
                conn.execute(
                    "UPDATE posts SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                    (title, content, datetime.now().isoformat(timespec="seconds"), post_id)
                )
            conn.commit()
            conn.close()
            flash("Post updated successfully.", "success")
            return redirect(url_for("post_detail", post_id=post_id))

    conn.close()
    return render_template("editor.html", mode="edit", post=post)


@app.post("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id):
    conn = get_db()
    post = conn.execute("SELECT author_id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return render_template("404.html"), 404
    if post["author_id"] != session["user_id"]:
        conn.close()
        flash("You can only delete your own posts.", "error")
        return redirect(url_for("post_detail", post_id=post_id))
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    flash("Post deleted.", "success")
    return redirect(url_for("home"))


@app.post("/post/<int:post_id>/comment")
@login_required
def add_comment(post_id):
    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("post_detail", post_id=post_id))

    conn = get_db()
    exists = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not exists:
        conn.close()
        return render_template("404.html"), 404

    conn.execute(
        "INSERT INTO comments (content, post_id, author_id, created_at) VALUES (?, ?, ?, ?)",
        (content, post_id, session["user_id"], datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    conn.close()
    flash("Comment added.", "success")
    return redirect(url_for("post_detail", post_id=post_id))


@app.post("/comment/<int:comment_id>/delete")
@login_required
def delete_comment(comment_id):
    conn = get_db()
    comment = conn.execute("SELECT author_id, post_id FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if not comment:
        conn.close()
        return render_template("404.html"), 404
    if comment["author_id"] != session["user_id"]:
        conn.close()
        flash("You can only delete your own comments.", "error")
        return redirect(url_for("post_detail", post_id=comment["post_id"]))
    post_id = comment["post_id"]
    conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()
    flash("Comment deleted.", "success")
    return redirect(url_for("post_detail", post_id=post_id))



@app.post("/post/<int:post_id>/reaction")
@login_required
def react_to_post(post_id):
    reaction = request.form.get("reaction", "")
    if reaction not in ("like", "dislike"):
        flash("Invalid reaction.", "error")
        return redirect(url_for("post_detail", post_id=post_id))

    conn = get_db()
    post = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return render_template("404.html"), 404

    existing = conn.execute(
        "SELECT id, reaction FROM post_reactions WHERE post_id = ? AND user_id = ?",
        (post_id, session["user_id"])
    ).fetchone()

    if existing and existing["reaction"] == reaction:
        conn.execute("DELETE FROM post_reactions WHERE id = ?", (existing["id"],))
    elif existing:
        conn.execute(
            "UPDATE post_reactions SET reaction = ?, created_at = ? WHERE id = ?",
            (reaction, datetime.now().isoformat(timespec="seconds"), existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO post_reactions (post_id, user_id, reaction, created_at) VALUES (?, ?, ?, ?)",
            (post_id, session["user_id"], reaction, datetime.now().isoformat(timespec="seconds"))
        )
    conn.commit()
    conn.close()
    return redirect(url_for("post_detail", post_id=post_id))


@app.post("/post/<int:post_id>/rating")
@login_required
def rate_post(post_id):
    try:
        rating = int(request.form.get("rating", "0"))
    except ValueError:
        rating = 0
    if rating not in range(1, 6):
        flash("Please select a rating from 1 to 5.", "error")
        return redirect(url_for("post_detail", post_id=post_id))

    conn = get_db()
    post = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return render_template("404.html"), 404

    existing = conn.execute(
        "SELECT id FROM post_ratings WHERE post_id = ? AND user_id = ?",
        (post_id, session["user_id"])
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE post_ratings SET rating = ?, created_at = ? WHERE id = ?",
            (rating, datetime.now().isoformat(timespec="seconds"), existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO post_ratings (post_id, user_id, rating, created_at) VALUES (?, ?, ?, ?)",
            (post_id, session["user_id"], rating, datetime.now().isoformat(timespec="seconds"))
        )
    conn.commit()
    conn.close()
    flash("Your rating has been saved.", "success")
    return redirect(url_for("post_detail", post_id=post_id))


# ---------------- REST API ----------------

@app.get("/api/posts")
def api_posts():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.id, p.title, p.content, p.author_id, u.name AS author_name,
               p.created_at, p.updated_at,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count
        FROM posts p
        JOIN users u ON u.id = p.author_id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()
    return jsonify({"posts": [dict(row) for row in rows]})


@app.get("/api/posts/<int:post_id>")
def api_post(post_id):
    conn = get_db()
    post = post_with_author(conn, post_id)
    if not post:
        conn.close()
        return jsonify({"error": "Post not found"}), 404
    comments = conn.execute("""
        SELECT c.id, c.content, c.author_id, u.name AS author_name, c.created_at
        FROM comments c
        JOIN users u ON u.id = c.author_id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    """, (post_id,)).fetchall()
    conn.close()
    result = dict(post)
    result["comments"] = [dict(c) for c in comments]
    return jsonify(result)


@app.post("/api/posts")
@login_required
def api_create_post():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO posts (title, content, author_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (title, content, session["user_id"], now, now)
    )
    conn.commit()
    post_id = cur.lastrowid
    conn.close()
    return jsonify({"message": "Post created", "post_id": post_id}), 201


@app.put("/api/posts/<int:post_id>")
@login_required
def api_update_post(post_id):
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    conn = get_db()
    post = conn.execute("SELECT author_id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return jsonify({"error": "Post not found"}), 404
    if post["author_id"] != session["user_id"]:
        conn.close()
        return jsonify({"error": "You can only edit your own posts"}), 403
    if not title or not content:
        conn.close()
        return jsonify({"error": "Title and content are required"}), 400

    conn.execute(
        "UPDATE posts SET title = ?, content = ?, updated_at = ? WHERE id = ?",
        (title, content, datetime.now().isoformat(timespec="seconds"), post_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Post updated"})


@app.delete("/api/posts/<int:post_id>")
@login_required
def api_delete_post(post_id):
    conn = get_db()
    post = conn.execute("SELECT author_id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return jsonify({"error": "Post not found"}), 404
    if post["author_id"] != session["user_id"]:
        conn.close()
        return jsonify({"error": "You can only delete your own posts"}), 403
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Post deleted"})


@app.post("/api/posts/<int:post_id>/comments")
@login_required
def api_create_comment(post_id):
    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content:
        return jsonify({"error": "Comment content is required"}), 400

    conn = get_db()
    post = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return jsonify({"error": "Post not found"}), 404

    cur = conn.execute(
        "INSERT INTO comments (content, post_id, author_id, created_at) VALUES (?, ?, ?, ?)",
        (content, post_id, session["user_id"], datetime.now().isoformat(timespec="seconds"))
    )
    conn.commit()
    comment_id = cur.lastrowid
    conn.close()
    return jsonify({"message": "Comment created", "comment_id": comment_id}), 201


@app.delete("/api/comments/<int:comment_id>")
@login_required
def api_delete_comment(comment_id):
    conn = get_db()
    comment = conn.execute("SELECT author_id FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if not comment:
        conn.close()
        return jsonify({"error": "Comment not found"}), 404
    if comment["author_id"] != session["user_id"]:
        conn.close()
        return jsonify({"error": "You can only delete your own comments"}), 403
    conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Comment deleted"})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "application": "Inkora"})


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Resource not found"}), 404
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
