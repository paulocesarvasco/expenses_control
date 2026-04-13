from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models import Base


class ProductCategory(Base):
    __tablename__ = 'product_categories'

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(50), nullable=False, unique=True)

    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<ProductCategory(category_id={self.category_id}, name='{self.category_name}')>"


class Product(Base):
    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(100), nullable=False, unique=True)
    category_id = Column(Integer, ForeignKey('product_categories.category_id'))

    category = relationship("ProductCategory", back_populates="products")
    purchases = relationship("PurchasedItem", back_populates="product")

    def __repr__(self):
        return f"<Product(product_id={self.product_id}, name='{self.product_name}')>"
