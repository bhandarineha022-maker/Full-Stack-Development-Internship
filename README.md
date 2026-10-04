# Blog Space – Blogging & Comments Platform

Blog Space is a full-stack blogging platform built with Flask, SQLite, HTML, CSS and JavaScript.

## Features

- User registration and login
- Password hashing
- Session-based authentication
- Create, read, edit and delete blog posts
- Users can edit/delete only their own posts
- Comments on blog posts
- Like and dislike reactions (one reaction per user per post)
- 1–5 star post ratings (one rating per user per post)
- Optional post image upload (PNG/JPG/JPEG/GIF/WEBP, up to 5 MB)
- Users can delete only their own comments
- RESTful API endpoints for posts and comments
- SQLite database integration
- Responsive modern UI
- Search/filter posts on the home page
- Flash messages for actions and validation
- No external database or API key is required

## Technology

- Frontend: HTML5, CSS3, JavaScript
- Backend: Python + Flask
- Database: SQLite
- Authentication: Flask sessions + Werkzeug password hashing
- API: REST-style JSON endpoints

## Windows Setup

### 1. Open PowerShell in this folder

Example:

```powershell
cd "C:\Users\YOUR_NAME\Downloads\Inkora_Blogging_Platform"
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

If `py` does not work:

```powershell
python -m venv .venv
```

### 3. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4. Install packages

```powershell
python -m pip install -r requirements.txt
```

### 5. Start the website

```powershell
python app.py
```

You should see Flask running on:

`http://127.0.0.1:5000`

Open that address in Chrome or Edge.

The SQLite database is automatically created at:

`instance/inkora.db`

## How to test

1. Open the website.
2. Click Register.
3. Create a user account.
4. Log in.
5. Click Write a Post.
6. Create a blog post.
7. Open the post.
8. Add a comment.
9. Edit or delete your own post.
10. Log out and register another account to test ownership restrictions.

## REST API

### Public

- `GET /api/health`
- `GET /api/posts`
- `GET /api/posts/<id>`

### Authentication required

- `POST /api/posts`
- `PUT /api/posts/<id>`
- `DELETE /api/posts/<id>`
- `POST /api/posts/<id>/comments`
- `DELETE /api/comments/<id>`

The API uses JSON for request/response data.

Example create-post JSON:

```json
{
  "title": "My First Inkora Post",
  "content": "This is my first post."
}
```

## Project structure

```text
Inkora_Blogging_Platform/
│
├── app.py
├── requirements.txt
├── README.md
├── instance/
│   └── inkora.db          # created automatically
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── auth.html
│   ├── editor.html
│   ├── post.html
│   └── 404.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## Presentation explanation

**Frontend:** The templates create the pages and CSS gives the website its cream, peach and coral visual theme.

**Backend:** Flask handles routes, authentication, blog CRUD operations, comments and REST API requests.

**Database:** SQLite stores users, posts and comments. Foreign keys connect posts to their authors and comments to both posts and authors.

**Authentication:** A user registers with an email/password. The password is stored as a secure hash. After login, Flask stores the user's ID in a session.

**REST API:** JSON endpoints allow a frontend or API client to read and modify posts/comments without directly accessing the database.

**Security/ownership:** A logged-in user can edit or delete only content they created.


## New interaction features

### Like / Dislike
A logged-in user can like or dislike a post. Clicking the same reaction again removes it. Switching from Like to Dislike changes the reaction instead of creating duplicates.

### Rating
A logged-in user can rate a post from 1 to 5 stars. The current average rating and number of ratings are shown on the post.

### Optional image
When creating or editing a post, an image can optionally be selected from the computer. Supported formats are PNG, JPG, JPEG, GIF and WEBP, with a 5 MB limit.

Uploaded images are stored in `static/uploads/`.

### Important
If you used an older copy of this project before these features were added, the application automatically adds the new `image_filename` column to the existing posts table. The new reaction and rating tables are created automatically.

## Visual design

The **Blog Space** interface uses the requested cream, peach/coral, green and dark-brown colour family while using an independently designed editorial layout. The navigation, hero composition, organic paper-like cards, post grid, typography hierarchy and engagement sections are intentionally different from the reference design.
