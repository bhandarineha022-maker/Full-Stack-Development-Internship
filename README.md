# AuroraCart — Full-Stack E-Commerce Web Application

AuroraCart is a complete Flask e-commerce project built around the requirements in the supplied reference:
- Product catalog, add-to-cart and checkout
- User login and role-based access (Admin/User)
- Backend REST APIs for product and order management
- SQL database integration through SQLAlchemy
- Order tracking with status updates
- Responsive, animated and unique visual design

## 1. Requirements
- Python 3.10 or newer
- VS Code or another editor
- Internet only during package installation if packages are not already cached
- Optional: MySQL 8+ if you want to switch from the included SQLite development database

## 2. Windows setup

Open PowerShell inside this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

Then open:
http://127.0.0.1:5000

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Demo accounts
User:
- Email: user@auroracart.local
- Password: user123

Admin:
- Email: admin@auroracart.local
- Password: admin123

## 4. MySQL option
The project works immediately with SQLite so you can test it without installing MySQL. It also supports MySQL.

1. Create a database:
```sql
CREATE DATABASE auroracart;
```

2. Copy `.env.example` to `.env`.

3. Change:
```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost/auroracart
```

4. Restart:
```powershell
python run.py
```

SQLAlchemy will create the required tables automatically.

## 5. Main pages
- `/` — storefront/product catalog
- `/shop/cart` — shopping cart
- `/shop/checkout` — checkout
- `/shop/orders` — customer order history
- `/admin/` — admin dashboard
- `/login` and `/register` — authentication
- `/api/products` — product JSON API
- `/api/orders` — order JSON API (login required)
- `/api/search?q=keyboard` — product search API

## 6. What the admin can do
- Add products
- View products and stock
- View all orders
- Change order status: Placed → Packed → Shipped → Out for Delivery → Delivered
- Cancel orders
- Protect admin features using role-based access

## 7. Notes for your college demonstration
The seeded products and accounts are already included. You can demonstrate:
1. Register a new user.
2. Browse products and filter by category.
3. Add multiple products to cart.
4. Checkout with a shipping address.
5. Open My Orders and show the tracking timeline.
6. Log out and sign in as admin.
7. Add a product from Admin.
8. Change an order's status.
9. Open `/api/products` to demonstrate the backend API.

The design intentionally uses a warm off-white background, deep ink navy, coral-pink and saffron yellow rather than a common blue/purple e-commerce template.
