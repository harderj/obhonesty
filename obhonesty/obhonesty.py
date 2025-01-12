"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from datetime import datetime
from typing import Callable, List, Optional
import uuid

import gspread
import reflex as rx

from obhonesty.state import State
from obhonesty.user import User
from obhonesty.item import Item
from obhonesty.aux import two_decimal_points 


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
    rx.dialog.root(
      rx.dialog.trigger(rx.button(
        rx.image(
          src=item.image_url,
          width="80px",
          height="auto",
          border_radius="15px",
          margin="10px"
        ),
        rx.text(item.name, size="5"),
        width="auto",
        height="auto",
        color_scheme='gray'
      )),
      rx.dialog.content(
        rx.dialog.title(f"{item.name} (€{two_decimal_points(item.price)})"),
        rx.dialog.description(item.description),
        rx.flex(
          rx.dialog.close(
            rx.button("Order", on_click=State.order_item(item))
          ),
          rx.dialog.close(rx.button(f"Cancel")),
          spacing="3",
          justify="end"
        )
      )
    )
  return rx.container(
    rx.vstack(
      rx.heading(f"Hello {State.current_user.name}"),
      rx.button("Log out", on_click=rx.redirect("/")),
      rx.text("Register an order:"),
      rx.foreach(State.items, item_button)
    )
  )


def admin() -> rx.Component:
  orders = order_sheet.get_all_records()
  n_o_dinner_signups = len([
    order for order in orders if order['item'] == "Sign-up for dinner" \
    and datetime.fromisoformat(order['time']).date() == datetime.today().date()
  ])
  users = user_sheet.get_all_records()
  n_o_volunteers = len([
    user for user in users if user['volunteer'] == "yes" \
    and user['away'] != "yes"
  ])
  return rx.container(
    rx.vstack(
      rx.heading(f"Admin"),
      rx.button("Return to index", on_click=rx.redirect("/")),
      rx.text(f"Signed up for dinner: {n_o_dinner_signups}"),
      rx.text(f"Volunteers: {n_o_volunteers}"),
      rx.text(f"Total eating dinner: {n_o_dinner_signups + n_o_volunteers}")
    )
  ) 


default_page_title: str = "OB Honesty system"

app = rx.App()
app.add_page(index, route="/", on_load=State.initialize)
app.add_page(user_page, route="/user", on_load=State.redirect_no_user)
app.add_page(admin, route="/admin")
