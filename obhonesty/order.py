from typing import Dict
import reflex as rx


class Order(rx.Base):
  order_id: str
  user_nick_name: str
  time: str
  item: str
  quantity: float
  price: float
  total: float
  receiver: str
  diet: str
  allergies: str
  served: str
  tax_category: str

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Order(
      order_id=x['order_id'],
      user_nick_name=x['user'],
      time=x['time'],
      item=x['item'],
      quantity=float(x['quantity']),
      price=float(x['price']),
      total=float(x['total']),
      receiver=x['receiver'],
      diet=x['diet'],
      allergies=x['allergies'],
      served=x['served'],
      tax_category=x['tax_category'],
      description=x['comment']
    )
  