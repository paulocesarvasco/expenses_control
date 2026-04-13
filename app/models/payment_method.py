from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.models import Base


class PaymentMethod(Base):
    __tablename__ = 'payment_methods'

    payment_method_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_method_name = Column(String(50), nullable=False, unique=True)

    shopping_trips = relationship("ShoppingTrip", back_populates="payment_method")

    def __repr__(self):
        return f"<PaymentMethod(payment_method_id={self.payment_method_id}, name='{self.payment_method_name}')>"
