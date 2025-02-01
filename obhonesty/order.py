from datetime import datetime
from typing import Dict
import reflex as rx


class Order(rx.Base):
  order_id: str
  user_nick_name: str
  time: datetime
  item: str
  quantity: float
  price: float
  total: float
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
      quantity=float(x['quantity']),
      price=float(x['price']),
      total=float(x['total']),
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
  quantity: float
  price: float
  total: float

  @staticmethod
  def from_order(order: Order):
    return OrderRepr(
      time=order.time.strftime("%Y-%m-%d, %H:%M:%S"),
      item=order.item,
      quantity=order.quantity,
      price=order.price,
      total=order.total
    )
