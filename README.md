# Neha Bhandari — Personal Portfolio

A modern dark-purple personal portfolio inspired by the supplied reference design. It uses Flask, SQLite, HTML, CSS and JavaScript.

## Features

- Dark purple / violet visual identity
- Minimal rounded N logo and name header
- About, Projects, Core Skills, Curiosity and Contact sections
- Smooth scrolling and subtle reveal animations
- Responsive desktop, tablet and mobile layout
- Projects loaded from SQLite through a Flask API
- Contact form saved to SQLite
- Resume download endpoint
- Ready for GitHub and deployment

## Run on Windows

Open PowerShell in this folder:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Personalize

1. Replace `static/images/profile.jpg` with your photo.
2. Put your resume at `static/files/Neha_Bhandari_Resume.pdf`.
3. Edit the email, GitHub and LinkedIn placeholders in `templates/index.html`.
4. Update project links in the `Project` seed data inside `app.py` or through the API.

## Stop the server

Press `Ctrl + C` in PowerShell.
