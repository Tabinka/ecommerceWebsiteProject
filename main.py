from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreateProductForm, RegisterForm, LoginForm

import stripe

# This is a sample test API key. Sign in to see examples pre-filled with your key.

stripe.api_key = 'sk_test_RXHltS2OKzISvxWQ7NmRN57i001oa6x7o4'

YOUR_DOMAIN = 'http://127.0.0.1:5000'

app = Flask(__name__)
app.config['SECRET_KEY'] = "dadadadnad22393DNdnsandas"
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///products.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
Base = declarative_base()


##CONFIGURE TABLES
class User(UserMixin, db.Model, Base):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)


class Product(db.Model, Base):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    alias = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(250), nullable=False)
    category_id = db.Column(db.Integer, ForeignKey('category.id'))
    category = relationship("Category", back_populates="products")


class Category(db.Model, Base):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    alias = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=False)
    products = relationship("Product", back_populates="category")


db.create_all()


@app.context_processor
def inject_category():
    categories = Category.query.all()
    name = []
    alias = []
    for cat in categories:
        name.append(cat.name)
        alias.append(cat.alias)
    return dict({"name": name, "alias": alias})


@app.context_processor
def logged_in():
    user_name = User.query.get(current_user.get_id())
    return dict({"user": user_name, "admin": current_user.is_authenticated})


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.get_id() != '1':
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def get_all_products():
    products = Product.query.all()
    return render_template("index.html", all_products=products, logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        if form.validate_on_submit():
            if User.query.filter_by(email=request.form["email"]).first():
                flash("User already exists.")
                return redirect(url_for('login'))
            else:
                new_user = User(email=request.form["email"],
                                password=generate_password_hash(password=request.form["password"],
                                                                method='pbkdf2:sha256',
                                                                salt_length=8), name=request.form["name"])
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('get_all_products'))
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        if User.query.filter_by(email=request.form["email"]).first():
            user = User.query.filter_by(email=request.form["email"]).first()
            if check_password_hash(user.password, request.form["password"]):
                login_user(user)
                return redirect(url_for('get_all_products'))
            else:
                flash('Wrong password.')
        else:
            flash('User does not exist.')
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_products'))


@app.route("/product/<string:alias>")
def show_product(alias):
    requested_product = Product.query.filter_by(alias=alias).first()
    category_id = requested_product.category.id
    category = Category.query.filter_by(id=category_id).first()
    category_name = category.name
    category_alias = category.alias
    return render_template("product-details.html", prod=requested_product, category_name=category_name,
                           category_alias=category_alias)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)


@app.route("/admin")
@admin_only
def admin_area():
    products = Product.query.all()
    return render_template("admin.html", logged_in=current_user.is_authenticated, list_products=products)


@app.route("/add-product", methods=["GET", "POST"])
@admin_only
def add_new_product():
    form = CreateProductForm()
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            alias=form.name.data,
            price=form.price.data,
            description=form.description.data,
            stock=form.stock.data,
            image=form.image.data
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("get_all_products"))
    return render_template("admin_forms.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/edit-product/<int:product_id>")
@admin_only
def edit_product(product_id):
    product = Product.query.get(product_id)
    edit_form = CreateProductForm(
        name=product.name,
        alias=product.alias,
        image=product.image,
        price=product.price,
        stock=product.stock,
        description=product.description
    )
    if edit_form.validate_on_submit():
        product.name = edit_form.name.data
        product.alias = edit_form.name.data
        product.image = edit_form.image.data
        product.price = edit_form.price.data
        product.stock = edit_form.stock.data
        product.description = edit_form.description.data
        db.session.commit()
        return redirect(url_for("show_product", alias=product.alias))
    return render_template("admin_forms.html", form=edit_form, logged_in=current_user.is_authenticated)


@app.route("/delete/<int:product_id>")
@admin_only
def delete_product(product_id):
    product_to_delete = Product.query.get(product_id)
    db.session.delete(product_to_delete)
    db.session.commit()
    return redirect(url_for('admin_area'))


# Stripe Checkout

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:

        checkout_session = stripe.checkout.Session.create(

            line_items=[

                {

                    # Provide the exact Price ID (e.g. pr_1234) of the product you want to sell

                    'price': '{{PRICE_ID}}',

                    'quantity': 1,

                },

            ],

            payment_method_types=[

                'card',

            ],

            mode='payment',

            success_url=YOUR_DOMAIN + '/success.html',

            cancel_url=YOUR_DOMAIN + '/cancel.html',

        )

    except Exception as e:

        return str(e)

    return redirect(checkout_session.url, code=303)


if __name__ == "__main__":
    app.run(debug=True)
