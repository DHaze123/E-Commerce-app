from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime

# -------------------
# APP SETUP
# -------------------
app = Flask(__name__)

# CHANGE THIS PASSWORD
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:PASSWD@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


# -------------------
# ASSOCIATION TABLE (Many-to-Many)
# -------------------
order_product = db.Table(
    'order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
)


# -------------------
# MODELS
# -------------------

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    email = db.Column(db.String(100), unique=True)

    orders = db.relationship('Order', backref='user', lazy=True)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    products = db.relationship(
        'Product',
        secondary=order_product,
        backref=db.backref('orders', lazy=True)
    )


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    price = db.Column(db.Float)


# -------------------
# SCHEMAS (MARSHMALLOW)
# -------------------

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


# -------------------
# CREATE TABLES
# -------------------
@app.before_first_request
def create_tables():
    db.create_all()


# -------------------
# USER ENDPOINTS
# -------------------

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return users_schema.jsonify(users)


@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return user_schema.jsonify(user)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    new_user = User(
        name=data['name'],
        address=data['address'],
        email=data['email']
    )
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user)


@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.json

    user.name = data.get('name', user.name)
    user.address = data.get('address', user.address)
    user.email = data.get('email', user.email)

    db.session.commit()
    return user_schema.jsonify(user)


@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


# -------------------
# PRODUCT ENDPOINTS
# -------------------

@app.route('/products', methods=['GET'])
def get_products():
    return products_schema.jsonify(Product.query.all())


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    return product_schema.jsonify(Product.query.get_or_404(id))


@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    product = Product(
        product_name=data['product_name'],
        price=data['price']
    )
    db.session.add(product)
    db.session.commit()
    return product_schema.jsonify(product)


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json

    product.product_name = data.get('product_name', product.product_name)
    product.price = data.get('price', product.price)

    db.session.commit()
    return product_schema.jsonify(product)


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"})


# -------------------
# ORDER ENDPOINTS
# -------------------

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json

    order = Order(
        user_id=data['user_id'],
        order_date=datetime.utcnow()
    )

    db.session.add(order)
    db.session.commit()
    return order_schema.jsonify(order)


@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    if product not in order.products:
        order.products.append(product)
        db.session.commit()

    return jsonify({"message": "Product added to order"})


@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    if product in order.products:
        order.products.remove(product)
        db.session.commit()

    return jsonify({"message": "Product removed from order"})


@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return orders_schema.jsonify(orders)


@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_products(order_id):
    order = Order.query.get_or_404(order_id)
    return products_schema.jsonify(order.products)


# -------------------
# RUN APP
# -------------------
if __name__ == '__main__':
    app.run(debug=True)