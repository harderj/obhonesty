"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
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
admin_sheet = spreadsheet.worksheet("admin")


# class AdminData(rx.Base):
#   dinner_price: float
#   desert_price: float
# 
#   @staticmethod
#   def from_dict(x: Dict[str, Any]):
#     return AdminData(
#       dinner_price=x['dinner_price'],
#       desert_price=x['desert_price']
#     )
# 

class State(rx.State):
  """The app state."""
  admin_data: dict
  users: List[User]
  items: List[Item]
  current_user: Optional[User]
  new_nick_name: str

  @rx.event
  def initialize(self): # -> List[Dict[str, str]]:
    print("State.initize() called")
    user_data = user_sheet.get_all_records() 
    item_data = item_sheet.get_all_records()
    self.admin_data = admin_sheet.get_all_records()[0]
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
  def order_item(self, item: Item):
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      item.name,
      item.price
    ])
  
  @rx.event
  def order_dinner(self, form_data: dict):
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      "Dinner sign-up",
      self.admin_data['dinner_price'],
      form_data['diner'],
      form_data['diet'],
      form_data['allergies']
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
  user_data = user_sheet.get_all_records()
  signups = []
  vegan_count: int = 0
  vegetarian_count: int = 0
  meat_count: int = 0
  for user_dict in user_data:
    user = User.from_dict(user_dict)
    if user.volunteer:
      signups.append([user.full_name, user.diet, user.allergies])
      match user_dict["diet"]:
        case "Vegetarian": vegetarian_count += 1
        case "Meat": meat_count += 1
        case _: vegan_count += 1
  for order in orders:
    if order["item"] == "Dinner sign-up" and \
      datetime.fromisoformat(order['time']).date() == datetime.today().date():
      signups.append([order['receiver'], order['diet'], order['allergies']])
      match order["diet"]:
        case "Vegetarian": vegetarian_count += 1
        case "Meat": meat_count += 1
        case _: vegan_count += 1

  return rx.container(rx.center(
    rx.vstack(
      rx.heading(f"Admin"),
      rx.button("Return to index", on_click=rx.redirect("/")),
      rx.text(f"Total eating dinner: {len(signups)}"),
      rx.text(f"Vegan: {vegan_count}"),
      rx.text(f"Vegatarian: {vegetarian_count}"),
      rx.text(f"Meat: {meat_count}"),
      rx.data_table(data=signups, columns=["Name", "Diet", "Allergies"])   
    )
  ))

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

def dinner_signup_page() -> rx.Component:
  return rx.container(rx.center(
    rx.vstack(
      rx.form(
        rx.vstack(
          rx.heading("Sign up for dinner"),
          rx.text("Name of dinner guest"),
          rx.input(
            placeholder="Name of diner",
            default_value=State.current_user.full_name,
            name="diner"
          ),
          rx.text("Dietary preferences"),
          rx.select(
            ["Vegan", "Vegetarian", "Meat"],
            default_value="Vegan",
            name="diet"
          ),
          rx.text("Allergies"),
          rx.input(
            name="allergies"
          ),
          rx.button("Register", type="submit")
        ),
        on_submit=State.order_dinner
      ),
      rx.button("Cancel", on_click=rx.redirect("/user"))
    )
  ))

app = rx.App()
app.add_page(index, route="/", on_load=State.initialize)
app.add_page(user_page, route="/user", on_load=State.redirect_no_user)
app.add_page(user_signup_page, route="/signup")
app.add_page(admin, route="/admin")
app.add_page(dinner_signup_page, route="/dinner")
