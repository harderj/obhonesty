from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import reflex as rx

class Item(rx.Base):
  name: str
  price: float
  description: str
  deadline: int

  @staticmethod
  def from_dict(x: Dict[str, str]):
    deadline_str: str = x['deadline']
    deadline = 24 * 60
    try:
      strip = datetime.strptime(deadline_str, '%H:%M')
      deadline = strip.hour * 60 + strip.minute
    except: pass
    return Item(
      name=x['name'],
      price=x['price'],
      description=x['description'],
      deadline=deadline
    )
