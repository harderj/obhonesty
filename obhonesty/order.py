from datetime import datetime
from typing import Dict, Optional
import reflex as rx


class Order(rx.Base):
  order_id: str
  user: str
  time: datetime
  item: str
  price: float
  receiver: str
  diet: str
  allergies: str
  served: bool


  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Order(
      order_id=x['order_id'],
      user=x['user'],
      time=datetime.fromisoformat(x['time']),
      item=x['item'],
      price=x['price'],
      receiver=x['receiver'],
      diet=x['diet'],
      allergies=x['allergies'],
      served=x['served']=="yes"
    )
