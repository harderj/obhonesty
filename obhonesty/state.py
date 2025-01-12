from datetime import datetime
import uuid
import reflex as rx
from typing import List, Optional
import gspread

from obhonesty.item import Item
from obhonesty.user import User

gclient = gspread.service_account()
spreadsheet = gclient.open("test")
user_sheet = spreadsheet.worksheet("users")
item_sheet = spreadsheet.worksheet("items")
order_sheet = spreadsheet.worksheet("orders")



class State(rx.State):
  """The app state."""
  users: List[User]
  items: List[Item]
  current_user: Optional[User]

  @rx.event
  def initialize(self): # -> List[Dict[str, str]]:
    user_data = user_sheet.get_all_records() 
    item_data = item_sheet.get_all_records()
    self.users = [User.from_dict(x) for x in user_data]
    self.items = [Item.from_dict(x) for x in item_data]

  @rx.event
  def redirect_to_user_page(self, user: User):
    self.current_user = user
    return rx.redirect("/user")
  
  @rx.event
  def redirect_no_user(self):
    if self.current_user is None:
      return rx.redirect("/")
    
  @rx.event
  def order_item(self, item: Item, quantity: float = 1.0):
    print(f"{self.current_user.name} ordered {item.name}")
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.name,
      str(datetime.now()),
      item.name,
      quantity,
      item.price,
      quantity * item.price
    ])
    
 