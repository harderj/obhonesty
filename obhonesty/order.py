from datetime import datetime
from typing import Dict, Optional
import reflex as rx


class Order(rx.Base):
  order_id: str
  user_nick_name: str
  time: datetime
  item: str
  price: float
  receiver: str
  diet: str
  allergies: str
  served: bool
  tax_category: str

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Order(
      order_id=x['order_id'],
      user_nick_name=x['user'],
      time=datetime.fromisoformat(x['time']),
      item=x['item'],
      price=x['price'],
      receiver=x['receiver'],
      diet=x['diet'],
      allergies=x['allergies'],
      served=x['served']=="yes",
      tax_category=x['tax_category'],
      description=x['comment']
    )
  

class OrderRepr(rx.Base):
  time: str
  item: str
  price: str

  @staticmethod
  def from_order(order: Order):
    return OrderRepr(
      time=order.time.strftime("%Y-%m-%d, %H:%M:%S"),
      item=order.item,
      price=f"{order.price:.2f}€"
    )
