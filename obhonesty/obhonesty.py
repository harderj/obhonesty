"""Welcome to Reflex! This file outlines the steps to create a basic app."""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

import gspread
import reflex as rx

from obhonesty.order import Order, OrderRepr
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

# hard coding is underrated right

breakfast_items = [
  "Vegan",
  "Small",
  "Continental",
  "Full English",
  "Vegetarian",
  "Packed Lunch (Vegan)",
  "Packed Lunch (Vegetarian)",
  "Packed Lunch (Meat)"
]

tax_categories = [
  "Food and beverage non-alcoholic",
  "Beverage with alcohol",
  "Fitness",
  "Miscellaneous"
]

class State(rx.State):
  """The app state."""
  admin_data: Dict[str, Any]
  users: List[User]
  items: List[Item]
  current_user: Optional[User]
  new_nick_name: str
  custom_item_price: str
  orders: List[Order]

  @rx.event
  def initialize(self):
    user_data = user_sheet.get_all_records() 
    item_data = item_sheet.get_all_records()
    order_data = order_sheet.get_all_records()
    self.admin_data = admin_sheet.get_all_records()[0]
    self.users = [User.from_dict(x) for x in user_data]
    self.items = [Item.from_dict(x) for x in item_data]
    self.orders = [Order.from_dict(x) for x in order_data]

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
      item.price,
      "",
      "",
      "",
      "",
      item.tax_category,
      ""
    ])
    return rx.toast.info(
      f"'{item.name}' registered succesfully. Thank you!",
      position="bottom-center"
    )
  
  @rx.event
  def order_custom_item(self, form_data: dict):
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      form_data['custom_item_name'],
      float(form_data['custom_item_price']),
      "",
      "",
      "",
      "",
      form_data['tax_category'],
      form_data['custom_item_description']
    ])
    return rx.redirect("/user")
  
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
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ])

  @rx.event
  def order_breakfast(self, form_data: dict):
    menu_item = form_data['menu_item']
    key = f"{menu_item}_price"
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      "Breakfast sign-up",
      self.admin_data[key] if not self.current_user.volunteer else 0.0,
      form_data['full_name'],
      menu_item,
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ])
  
  @rx.event
  def submit_signup(self, form_data: dict):
    print(list(form_data.values()))
    print(self.users[0])
    user_sheet.append_row(list(form_data.values()))
    return rx.redirect("/")
  
  @rx.var(cache=True)
  def current_user_orders(self) -> List[OrderRepr]:
    filtered: List[OrderRepr] = []
    for order in self.orders:
      if order.user_nick_name == self.current_user.nick_name:
        filtered.append(OrderRepr.from_order(order))
    return filtered
 

  @rx.var(cache=True)
  def invalid_new_user_name(self) -> bool:
    return self.new_nick_name in [x.nick_name for x in self.users]
  
  @rx.var(cache=True)
  def invalid_custom_item_price(self) -> bool:
    try:
      # Convert to float and check decimals
      float_val = float(self.custom_item_price)
      # Optionally check decimal places
      if len(str(float_val).split('.')[-1]) <= 2:  # For 2 decimal places
        return False
      return True
    except ValueError:
      return True 
  
  @rx.var(cache=True)
  def dinner_signup_deadline_minutes(self) -> int:
    try:
      time = datetime.strptime(self.admin_data['dinner_signup_deadline'], "%H:%M")
    except:
      time = datetime.strptime("23:59", "%H:%M")
    return time.hour * 60 + time.minute
  
  @rx.var(cache=True)
  def breakfast_signup_deadline_minutes(self) -> int:
    try:
      time = datetime.strptime(self.admin_data['breakfast_signup_deadline'], "%H:%M")
    except:
      time = datetime.strptime("23:59", "%H:%M")
    return time.hour * 60 + time.minute
  
  @rx.var(cache=True)
  def tax_categories(self) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for order in self.orders:
      if not order.tax_category in result:
        result[order.tax_category] = 0.0
      result[order.tax_category] += order.price
    return result

  @rx.var(cache=True)
  def breakfast_signups(self) -> List[List[str]]:
    signups = []
    for order in self.orders:
      if order.item == "Breakfast sign-up" and \
        order.time.date() == datetime.today().date():
        signups.append([
          order.time.strftime("%H:%M:%S"),
          order.receiver,
          order.diet,
          order.allergies
        ])
    return signups
  
  @rx.var(cache=True)
  def dinner_signups(self) -> List[List[str]]:
    signups = []
    for order in self.orders:
      if order.item == "Dinner sign-up" and \
        order.time.date() == datetime.today().date():
        signups.append([order.receiver, order.diet, order.allergies, "no"])
    for user in self.users:
      if user.volunteer:
        signups.append([user.full_name, user.diet, user.allergies, "yes"])
    return signups
  
  @rx.var(cache=True)
  def dinner_count(self) -> int:
    return len(self.dinner_signups)
  
  @rx.var(cache=True)
  def dinner_count_vegan(self) -> int:
    count = 0 
    for order in self.dinner_signups:
      if order[1] == "Vegan":
        count += 1
    return count
  
  @rx.var(cache=True)
  def dinner_count_vegetarian(self) -> int:
    count = 0 
    for order in self.dinner_signups:
      if order[1] == "Vegetarian":
        count += 1
    return count
  
  @rx.var(cache=True)
  def dinner_count_meat(self) -> int:
    count = 0 
    for order in self.dinner_signups:
      if order[1] == "Meat":
        count += 1
    return count   

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
  def item_button(item: Item) -> rx.Component:
    title: str = f"{item.name} (€{two_decimal_points(item.price)})"
    return rx.dialog.root(
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
  now = datetime.now()
  return rx.container(rx.center(rx.vstack(
    rx.heading(f"Hello {State.current_user.nick_name}"),
    rx.button("Log out", on_click=rx.redirect("/")),
    rx.button("View orders", on_click=rx.redirect("/info")),
    rx.cond(
      State.breakfast_signup_deadline_minutes < now.hour * 60 + now.minute,
      rx.text(f"Breakfast sign-up closed (last sign-up at {State.admin_data['breakfast_signup_deadline']})"),
      rx.button("Sign up for breakfast / packed lunch", on_click=rx.redirect("/breakfast"))
    ), 
    rx.cond(
      State.dinner_signup_deadline_minutes < now.hour * 60 + now.minute,
      rx.text(f"Dinner sign-up closed (last sign-up at {State.admin_data['dinner_signup_deadline']})"),
      rx.button("Sign up for dinner", on_click=rx.redirect("/dinner"))
    ),
    rx.text("Register an item:"), 
    rx.button("Custom item", on_click=rx.redirect("/custom_item")),
    rx.foreach(State.items, item_button)
  )))


def custom_item_page() -> rx.Component:
  return rx.container(rx.center(rx.vstack(
    rx.heading("Register custom item"),
    rx.form(
      rx.vstack(
        rx.text("Name"),
        rx.input(placeholder="What did you get?", name="custom_item_name"),
        rx.text("Price"),
        rx.form.field(
          rx.form.control(
            rx.input(
              placeholder="E.g. 2.50 for (2.50€)",
              name="custom_item_price",
              on_change=State.set_custom_item_price
            ),
            as_child=True
          ),
          rx.form.message(
            "Please enter a valid price",
            match="valueMissing",
            force_match=State.invalid_custom_item_price,
            color="var(--red-11)"
          )
        ),
        rx.text("Category"),
        rx.select(
          tax_categories,
          default_value=tax_categories[0],
          name="tax_category"
        ),
        rx.text("Comment"),
        rx.input(placeholder="optional", name="custom_item_description"),
        rx.button("Register", type="submit")
      ),
      on_submit=State.order_custom_item
    ),
    rx.button("Cancel", on_click=rx.redirect("/user"))
  )))


def admin() -> rx.Component:
  return rx.container(rx.center(
    rx.vstack(
      rx.heading(f"Admin"),
      rx.button("Dinner", on_click=rx.redirect("/admin/dinner")),
      rx.button("Breakfast", on_click=rx.redirect("/admin/breakfast")),
      rx.button("Tax", on_click=rx.redirect("/admin/tax"))
    ) 
  ))


def admin_tax() -> rx.Component:
  return rx.container(rx.center(rx.vstack(
    rx.heading("Tax categories"),
    rx.button("Go back", on_click=rx.redirect("/admin")),
    rx.foreach(
      State.tax_categories.items(),
      lambda x: rx.text(f"{x[0]}: {x[1]}")
    )
  )))

def admin_dinner() -> rx.Component:
  return rx.container(rx.center(
    rx.vstack(
      rx.heading("Dinner"),
      rx.button("Go back", on_click=rx.redirect("/admin")),
      rx.text(f"Total eating dinner: {State.dinner_count}"),
      rx.text(f"Vegan: {State.dinner_count_vegan}"),
      rx.text(f"Vegatarian: {State.dinner_count_vegetarian}"),
      rx.text(f"Meat: {State.dinner_count_meat}"),
      rx.data_table(data=State.dinner_signups, columns=["Name", "Diet", "Allergies", "Volunteer"])
    )
  ))

def admin_breakfast() -> rx.Component:
  return rx.container(rx.center(
    rx.vstack(
      rx.heading("Breakfast"),
      rx.button("Go back", on_click=rx.redirect("/admin")),
      # rx.text(f"Total eating breakfast: {len(signups)}"),
      rx.data_table(data=State.breakfast_signups, columns=["Time", "Name", "Diet", "Allergies"])   
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
              required=True,
              type="email"
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
          rx.button("Register", type="submit", on_click=rx.redirect("/user"))
        ),
        on_submit=State.order_dinner
      ),
      rx.button("Cancel", on_click=rx.redirect("/user"))
    )
  ))

def breakfast_signup_page() -> rx.Component:
  return rx.container(rx.center(
    rx.vstack(
      rx.form(
        rx.vstack(
          rx.heading("Sign up for breakfast"),
          rx.text("Name of breakfast guest"),
          rx.input(
            placeholder="Name",
            default_value=State.current_user.full_name,
            name="full_name"
          ),
          rx.text("Menu"),
          rx.select.root(
            rx.select.trigger(),
            rx.select.content(
              rx.foreach(
                breakfast_items,
                lambda item: rx.select.item(f"{item} ({State.admin_data[item + "_price"]}€)", value=item)
              )
            ),
            default_value=breakfast_items[0],
            name="menu_item"
          ),
          rx.text("Allergies"),
          rx.input(
            name="allergies"
          ),
          rx.button("Register", type="submit", on_click=rx.redirect("/user"))
        ),
        on_submit=State.order_breakfast
      ),
      rx.button("Cancel", on_click=rx.redirect("/user"))
    )
  ))


def user_info_page() -> rx.Component:
  def show_row(order: OrderRepr):
    return rx.table.row(
      rx.table.cell(order.time),
      rx.table.cell(order.item),
      rx.table.cell(order.price)
    )
  
  return rx.container(rx.center(rx.vstack(
    rx.heading(f"Hello {State.current_user.nick_name}"),
    rx.button(f"Back to orders and items", on_click=rx.redirect("/user")),
    rx.table.root(
      rx.table.header(
        rx.table.row(
          rx.table.column_header_cell("Time"),
          rx.table.column_header_cell("Item"),
          rx.table.column_header_cell("Price")
        )
      ),
      rx.table.body(
        rx.foreach(
          State.current_user_orders, show_row
        )
      )
    )
  )))

app = rx.App()
app.add_page(index, route="/", on_load=State.initialize)
app.add_page(user_page, route="/user", on_load=State.redirect_no_user)
app.add_page(user_signup_page, route="/signup")
app.add_page(admin, route="/admin")
app.add_page(admin_dinner, route="/admin/dinner", on_load=State.initialize)
app.add_page(admin_breakfast, route="/admin/breakfast", on_load=State.initialize)
app.add_page(admin_tax, route="/admin/tax", on_load=State.initialize)
app.add_page(dinner_signup_page, route="/dinner")
app.add_page(breakfast_signup_page, route="/breakfast")
app.add_page(custom_item_page, route="/custom_item")
app.add_page(user_info_page, route="/info", on_load=State.initialize)