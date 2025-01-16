from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import reflex as rx

class Item(rx.Base):
  name: str
  price: float
  description: str

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Item(
      name=x['name'],
      price=x['price'],
      description=x['description']
    )
