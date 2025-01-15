"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from datetime import datetime, timedelta
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
  new_nick_name: str

  @rx.event
  def initialize(self): # -> List[Dict[str, str]]:
    print("State.initize() called")
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
    print(f"{self.current_user.nick_name} ordered {quantity} of {item.name}")
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      item.name,
      quantity,
      item.price,
      quantity * item.price
    ])

  @rx.var
  def invalid_new_user_name(self) -> bool:
    return self.new_nick_name in [x.nick_name for x in self.users]
  
  @rx.event
  def submit_signup(self, form_data: dict):
    print(list(form_data.values()))
    print(self.users[0])
    user_sheet.append_row(list(form_data.values()))
    return rx.redirect("/")
    

def index() -> rx.Component:
  # Welcome Page (Index)
  user_button: Callable[[User], rx.Component] = lambda user: \
    rx.button(user.nick_name, on_click=State.redirect_to_user_page(user))
  return rx.container(
    rx.center(
      rx.vstack(
        rx.heading("Welcome to the Olive Branch honest self-service", size="7"),
        rx.hstack(
          rx.text("New here?", size="5"),
          rx.button("Sign up for self-service", on_click=rx.redirect("/signup"))
        ),
        rx.text(f"Find yourself and place an order", size="5"),
        rx.foreach(State.users, user_button),
      )
    )
  )


def user_page() -> rx.Component:
  now = datetime.now()
  def item_button(item: Item) -> rx.Component:
    title: str = f"{item.name} (€{two_decimal_points(item.price)})"
    return rx.cond(
      item.deadline < now.hour * 60 + now.minute,
      rx.text(f"{title}: (too late to order)"),
      rx.dialog.root(
        rx.dialog.trigger(rx.button(
          title,
          color_scheme='gray'
        )),
        rx.dialog.content(
          rx.dialog.title(title),
          rx.dialog.description(item.description),
          rx.vstack(
            rx.flex(
              rx.dialog.close(
                rx.button("Register", on_click=State.order_item(item))
              ), 
              rx.dialog.close(rx.button(f"Cancel")),
              spacing="3",
              justify="end" 
            ),
            spacing="3"
          ),
        )
      )
    )
  
  return rx.container(
    rx.center(
      rx.vstack(
        rx.heading(f"Hello {State.current_user.nick_name}"),
        rx.button("Log out", on_click=rx.redirect("/")),
        rx.button("Sign up for dinner", on_click=rx.redirect("/dinner")),
        rx.text("Register an item:"),
        rx.foreach(State.items, item_button)
      )
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

message_name_already_taken: str = "Already taken"

def user_signup_page() -> rx.Component:
  return rx.container(
    rx.center(
      rx.vstack(
        rx.heading("Welcome to the Olive Branch"),
        rx.text("Please fill in your details to get started with self-service"),
        rx.form(
          rx.vstack(
            rx.form.field(
              rx.form.control(
                rx.input(
                  placeholder="Nick name (required)",
                  on_change=State.set_new_nick_name,
                  name="nick_name",
                  required=True
                ),
                as_child=True
              ),
              rx.form.message(
                message_name_already_taken,
                match="valueMissing",
                force_match=State.invalid_new_user_name,
                color="var(--red-11)"
              ),
            ),
            rx.input(
              placeholder="Full name (required)",
              name="full_name",
              required=True
            ),
            rx.input(
              placeholder="Phone number (required)",
              name="phone_number",
              required=True
            ),
            rx.input(
              placeholder="Email (required)",
              name="email",
              required=True
            ),
            rx.input(
              placeholder="Address (optional)",
              name="address"
            ),
            rx.button("Submit", type="submit")
          ),
          on_submit=State.submit_signup,
          reset_on_submit=True
        ),
        rx.button("Go back", on_click=rx.redirect("/")),
      ),
    ),
  )

app = rx.App()
app.add_page(index, route="/", on_load=State.initialize)
app.add_page(user_page, route="/user", on_load=State.redirect_no_user)
app.add_page(user_signup_page, route="/signup")
app.add_page(admin, route="/admin")
