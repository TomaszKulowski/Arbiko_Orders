from sqlalchemy import Integer, String, Date, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column, relationship

Base = declarative_base()
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)


class Product(Base):
    __tablename__ = 'products'

    id = mapped_column(Integer, primary_key=True)
    catalog_number = mapped_column(String)
    oem_number = mapped_column(String)
    description = mapped_column(String)
    orders = relationship('Order', secondary='products_orders', back_populates='products')


class Order(Base):
    __tablename__ = 'orders'

    id = mapped_column(Integer, primary_key=True)
    order_number = mapped_column(Integer)
    date = mapped_column(Date)
    products = relationship('Product', secondary='products_orders', back_populates='orders')


class ProductOrder(Base):
    __tablename__ = 'products_orders'

    id = mapped_column(Integer, primary_key=True)
    product_id = mapped_column(Integer, ForeignKey('products.id'))
    order_id = mapped_column(Integer, ForeignKey('orders.id'))
