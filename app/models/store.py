from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.models import Base


class ShoppingTrip(Base):
    __tablename__ = 'shopping_trips'

    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    store_name = Column(String(100), nullable=False)
    purchase_date = Column(Date, nullable=False)
    total_amount = Column(Float(precision=2))
    payment_method_id = Column(Integer, ForeignKey('payment_methods.payment_method_id'))
    notes = Column(String(150))

    items = relationship("PurchasedItem", back_populates="trip")
    payment_method = relationship("PaymentMethod", back_populates="shopping_trips")

    def __repr__(self):
        return f"<ShoppingTrip(trip_id={self.trip_id}, store='{self.store_name}', date={self.purchase_date})>"
