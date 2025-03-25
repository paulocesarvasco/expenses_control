from sqlalchemy import Column, Computed, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.models import Base


class PurchasedItem(Base):
    __tablename__ = 'purchased_items'

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey('shopping_trips.trip_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Float(precision=3), nullable=False, default=1)
    unit_price = Column(Float(precision=2), nullable=False)
    total_price = Column(Float(precision=2), Computed(quantity * unit_price))
    brand = Column(String(100))

    # Relationships
    trip = relationship("ShoppingTrip", back_populates="items")
    product = relationship("Product", back_populates="purchases")

    def __repr__(self):
        return f"<PurchasedItem(item_id={self.item_id}, product='{self.product.product_name}', qty={self.quantity})>"
