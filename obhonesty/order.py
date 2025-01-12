from datetime import datetime
from typing import Dict, Optional
import reflex as rx


class Order(rx.Base):
  order_id: str
  user: str
  time: datetime
  item: str
  quantity: float
  price_at_order_time: float
  total_price: float
  tags: str


  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Order(
      order_id=x['order_id'],
      user=x['user'],
      time=datetime.fromisoformat(x['time']),
      item=x['item'],
      quantity=x['quantity'],
      price_at_order_time=x['price_at_order_time'],
      total_price=x['total_price'],
      tags=x['tags']
    )
