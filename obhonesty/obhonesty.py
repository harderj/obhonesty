"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from datetime import datetime
from typing import Callable, Dict, List, Optional
import uuid

import reflex as rx
import gspread


gclient = gspread.service_account(filename="service_account.json")
spreadsheet = gclient.open("test")
user_sheet = spreadsheet.worksheet("users")
item_sheet = spreadsheet.worksheet("items")
order_sheet = spreadsheet.worksheet("orders")



class User(rx.Base):
  name: str
  password: str

  def __str__(self):
    return f"User(name={self.name}, password={self.password})"

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return User(name=x['name'], password=x['password'])


class Item(rx.Base):
  name: str
  price: float
  image_url: str

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return Item(name=x['name'], price=x['price'], image_url=x['image_url'])


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
    
  

def index() -> rx.Component:
  # Welcome Page (Index)
  user_button: Callable[[User], rx.Component] = lambda user: \
    rx.button(user.name, on_click=State.redirect_to_user_page(user))
  return rx.container(
    rx.vstack(
      rx.heading("Welcome to the Olive Branch honest self-service", size="7"),
      rx.text(f"Find yourself and place an order", size="5"),
      rx.foreach(State.users, user_button),
    )
  )


def user_page() -> rx.Component:
  item_button: Callable[[Item], rx.Component] = lambda item: \
    rx.button(
      item.name,
      rx.image(
        src=item.image_url,
        width="80px",
        height="auto",
        border_radius="15px",
        margin="10px"
      ),
      width="auto",
      height="auto",
      on_click=State.order_item(item),
      color_scheme='gray'
    )
  return rx.container(
    rx.vstack(
      rx.heading(f"Hello {State.current_user.name}"),
      rx.button("Log out", on_click=rx.redirect("/")),
      rx.text("Register an order:"),
      rx.foreach(State.items, item_button)
    )
  )


app = rx.App()
app.add_page(index, route="/", on_load=State.initialize, title="Welcome")
app.add_page(user_page, route="/user", on_load=State.redirect_no_user)

