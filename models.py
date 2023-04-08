from sqlalchemy import String, Integer, Date, Column, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(Integer)
    date = Column(Date)
    products = relationship('Product', secondary='order_products', back_populates='orders')


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    catalog_number = Column(Integer)
    oem_number = Column(String)
    description = Column(String)
    orders = relationship('Order', secondary='order_products', back_populates='products')


class OrderProduct(Base):
    __tablename__ = 'order_products'

    order_product_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

