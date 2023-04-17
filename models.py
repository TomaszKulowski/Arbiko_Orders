"""The collections of the models to use in sqlachemy ORM."""
from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column, relationship

Base = declarative_base()


class Product(Base):
    """Model to manage products table."""
    __tablename__ = 'products'

    id = mapped_column(Integer, primary_key=True)
    catalog_number = mapped_column(String)
    oem_number = mapped_column(String)
    description = mapped_column(String)
    orders = relationship('OrderProduct', back_populates='product', viewonly=True)


class Order(Base):
    """Model to manage orders table."""
    __tablename__ = 'orders'

    id = mapped_column(Integer, primary_key=True)
    order_number = mapped_column(Integer)
    date = mapped_column(Date)
    products = relationship('OrderProduct', back_populates='order', viewonly=True)


class OrderProduct(Base):
    """Model to associate table orders and products."""
    __tablename__ = 'orders_products'

    id = mapped_column(Integer, primary_key=True)
    order_id = mapped_column(Integer, ForeignKey('orders.id'))
    product_id = mapped_column(Integer, ForeignKey('products.id'))
    quantity = mapped_column(Integer)
    product = relationship('Product', back_populates='orders')
    order = relationship('Order', back_populates='products')
