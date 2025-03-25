from sqlalchemy import Column, Integer, String, Date, Float
from sqlalchemy.orm import relationship
from app.utils.models import Base


class ShoppingTrip(Base):
    __tablename__ = 'shopping_trips'

    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    store_name = Column(String(100), nullable=False)
    purchase_date = Column(Date, nullable=False)
    total_amount = Column(Float(precision=2))
    payment_method = Column(String(50))
    notes = Column(String)  # Changed from TEXT to String for compatibility

    # Relationship to purchased items
    items = relationship("PurchasedItem", back_populates="trip")

    def __repr__(self):
        return f"<ShoppingTrip(trip_id={self.trip_id}, store='{self.store_name}', date={self.purchase_date})>"
