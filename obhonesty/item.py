from datetime import datetime
from typing import Dict, Optional
import reflex as rx

class Item(rx.Base):
  name: str
  price: float
  image_url: str
  description: str
  deadline: Optional[datetime]


  @staticmethod
  def from_dict(x: Dict[str, str]):
    deadline_str: str = x['deadline']
    deadline = None if deadline_str=="" \
      else datetime.strptime(deadline_str, '%H:%M')
    return Item(
      name=x['name'],
      price=x['price'],
      image_url=x['image_url'],
      description=x['description'],
      deadline=deadline
    )
