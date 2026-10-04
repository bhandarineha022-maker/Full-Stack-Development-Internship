from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "neha-portfolio-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(INSTANCE_DIR / "portfolio.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech = db.Column(db.String(300), default="")
    github = db.Column(db.String(500), default="#")
    live = db.Column(db.String(500), default="#")
    featured = db.Column(db.Boolean, default=False)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)


def seed_projects():
    if Project.query.count():
        return
    projects = [
        Project(
            title="AI Goa Tourism Blog Generator",
            description="An AI-assisted content workflow that turns tourism topics into structured, SEO-friendly blog documents with retrieval and export steps.",
            tech="Python · Flask · Gemini · Jinja2 · DOCX",
            featured=True,
        ),
        Project(
            title="TaskFlow",
            description="A practical task-management web app with CRUD operations, task status, priorities and a clean responsive dashboard.",
            tech="Python · Flask · SQLite · JavaScript",
            featured=True,
        ),
        Project(
            title="BlogSpace",
            description="A full-stack blogging platform for creating posts, reactions, ratings and image-supported content in one place.",
            tech="Flask · SQLite · HTML · CSS · JavaScript",
            featured=True,
        ),
    ]
    db.session.add_all(projects)
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_projects()


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/projects")
def projects_api():
    projects = Project.query.order_by(Project.featured.desc(), Project.id.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "tech": p.tech,
            "github": p.github,
            "live": p.live,
            "featured": p.featured,
        }
        for p in projects
    ])


@app.post("/api/projects")
def add_project():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    if not title or not description:
        return jsonify({"error": "Title and description are required."}), 400

    project = Project(
        title=title,
        description=description,
        tech=str(data.get("tech", "")).strip(),
        github=str(data.get("github", "#")).strip() or "#",
        live=str(data.get("live", "#")).strip() or "#",
        featured=bool(data.get("featured", False)),
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({"message": "Project added successfully", "id": project.id}), 201


@app.delete("/api/projects/<int:project_id>")
def delete_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted"})


@app.post("/api/contact")
def contact():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    message = str(data.get("message", "")).strip()

    if not name or not email or not message:
        return jsonify({"error": "Please fill in all fields."}), 400

    db.session.add(ContactMessage(name=name, email=email, message=message))
    db.session.commit()
    return jsonify({"message": "Your message has been sent successfully."}), 201


@app.get("/resume")
def resume():
    resume_dir = BASE_DIR / "static" / "files"
    resume_dir.mkdir(exist_ok=True)
    resume_file = resume_dir / "Neha_Bhandari_Resume.pdf"
    if not resume_file.exists():
        return jsonify({"error": "Resume not added yet. Put Neha_Bhandari_Resume.pdf inside static/files/."}), 404
    return send_from_directory(resume_dir, resume_file.name, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
