
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

import reflex as rx

from obhonesty.user import User
from obhonesty.item import Item
from obhonesty.order import Order
from obhonesty.sheet import user_sheet, item_sheet, order_sheet, admin_sheet, dinner_sheet, breakfast_sheet

class State(rx.State):
  """The app state."""
  admin_data: Dict[str, Any]
  users: List[User]
  items: Dict[str, Item]
  current_user: Optional[User]
  new_nick_name: str
  custom_item_price: str
  orders: List[Order]

  @rx.event
  def reload_sheet_data(self):
    user_data = user_sheet.get_all_records() 
    item_data = item_sheet.get_all_records()
    order_data = order_sheet.get_all_records()
    self.admin_data = admin_sheet.get_all_records()[-1]
    self.users = [User.from_dict(x) for x in user_data]
    self.items = {x['name'] : Item.from_dict(x) for x in item_data}
    self.orders = [Order.from_dict(x) for x in order_data]

    self.users.sort(key=lambda x: x.nick_name)

  @rx.event
  def redirect_to_user_page(self, user: User):
    self.current_user = user
    return rx.redirect("/user")
  
  @rx.event
  def redirect_to_admin_user_page(self, user: User):
    self.current_user = user
    return rx.redirect("/admin/user")

  @rx.event
  def redirect_no_user(self):
    if self.current_user is None:
      return rx.redirect("/")
    
  @rx.event
  def order_item(self, form_data: dict):
    item = self.items[form_data['item_name']]
    try:
      quantity = float(form_data['quantity'])
    except:
      return rx.toast.error("Failed to register. Quantity must be a number")
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      item.name,
      quantity,
      item.price,
      quantity * item.price,
      "", "", "", "",
      item.tax_category,
      ""
    ])
    return rx.toast.info(
      f"'{item.name}' registered succesfully. Thank you!",
      position="bottom-center"
    )
  
  @rx.event
  def order_custom_item(self, form_data: dict):
    item_name = form_data['custom_item_name']
    order_sheet.append_row([
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      item_name,
      1.0,
      float(form_data['custom_item_price']),
      float(form_data['custom_item_price']),
      "", "", "", "",
      form_data['tax_category'],
      form_data['custom_item_description']
    ])
    return rx.redirect("/user")
  
  @rx.event
  def order_dinner(self, form_data: dict):
    row = [
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      "Dinner sign-up",
      1.0,
      self.admin_data['dinner_price'],
      self.admin_data['dinner_price'],
      form_data['diner'],
      form_data['diet'],
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ]
    order_sheet.append_row(row)

    # Clear dinner sheet if there are still rows from yesterday
    potential_time_yesterday = dinner_sheet.cell(2, 3).value
    if potential_time_yesterday != None:
      if datetime.fromisoformat(potential_time_yesterday).date() != datetime.now().date():
        dinner_sheet.delete_rows(2, 200)
    
    dinner_sheet.append_row(row) 
    rx.toast.info("Dinner sign-up successful")
    return rx.redirect("/user")

  @rx.event
  def order_breakfast(self, form_data: dict):
    menu_item = form_data['menu_item']
    key = f"{menu_item}_price"
    price = self.admin_data[key] if not self.current_user.volunteer else 0.0
    row = [
      str(uuid.uuid4()), 
      self.current_user.nick_name,
      str(datetime.now()),
      "Breakfast sign-up",
      1.0,
      price,
      price,
      form_data['full_name'],
      menu_item,
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ]
    order_sheet.append_row(row)

    # Clear breakfast sheet if there are still rows from yesterday
    potential_time_yesterday = breakfast_sheet.cell(2, 3).value
    if potential_time_yesterday != None:
      if datetime.fromisoformat(potential_time_yesterday).date() != datetime.now().date():
        breakfast_sheet.delete_rows(2, 200)

    breakfast_sheet.append_row(row)
    return rx.toast.info("Breakfast/pack-lunch sign-up successful")
  
  @rx.event
  def submit_signup(self, form_data: dict):
    user_sheet.append_row(list(form_data.values()))
    return rx.redirect("/")
  
  @rx.var(cache=False)
  def current_user_orders(self) -> List[Order]:
    filtered: List[Order] = []
    for order in self.orders:
      if order.user_nick_name == self.current_user.nick_name:
        filtered.append(order)
    return filtered

  @rx.var(cache=False)
  def invalid_new_user_name(self) -> bool:
    return self.new_nick_name in [x.nick_name for x in self.users]
  
  @rx.var(cache=False)
  def invalid_custom_item_price(self) -> bool:
    try:
      # Convert to float and check decimals
      float_val = float(self.custom_item_price)
      # Optionally check decimal places
      if len(str(float_val).split('.')[-2]) <= 2:  # For 2 decimal places
        return False
      return True
    except ValueError:
      return True 
  
  @rx.var(cache=False)
  def dinner_signup_available(self) -> int:
    try:
      deadline = datetime.strptime(self.admin_data['dinner_signup_deadline'], "%H:%M")
    except:
      deadline = datetime.strptime("22:59", "%H:%M")
    now = datetime.now()
    deadline_minutes = deadline.hour * 60 + deadline.minute
    now_minutes = now.hour * 60 + now.minute
    return now_minutes < deadline_minutes
  
  @rx.var(cache=False)
  def breakfast_signup_available(self) -> int:
    try:
      deadline = datetime.strptime(self.admin_data['breakfast_signup_deadline'], "%H:%M")
    except:
      deadline = datetime.strptime("22:59", "%H:%M")
    now = datetime.now()
    deadline_minutes = deadline.hour * 60 + deadline.minute
    now_minutes = now.hour * 60 + now.minute
    return now_minutes < deadline_minutes
  
  @rx.var(cache=False)
  def tax_categories(self) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for order in self.orders:
      if not order.tax_category in result:
        result[order.tax_category] = 0.0
      result[order.tax_category] += order.price
    return result

  @rx.var(cache=False)
  def breakfast_signups(self) -> List[Order]:
    signups = []
    for order in self.orders:
      try:
        order_date = datetime.fromisoformat(order.time).date()
      except:
        pass
      if order.item == "Breakfast sign-up" and \
          order_date == datetime.today().date():
        signups.append(order)
    return signups
  
  @rx.var(cache=False)
  def dinner_signups(self) -> List[Order]:
    signups: List[Order] = []
    for order in self.orders:
      try:
        order_date = datetime.fromisoformat(order.time).date()
      except:
        pass
      if order.item == "Dinner sign-up" and \
          order_date == datetime.today().date():
        signups.append(order)
    for user in self.users:
      if user.volunteer:
        signups.append(Order(order_id="",
          user_nick_name=user.nick_name, time="",
          item="Dinner sign-up (volunteer)",
          quantity=1.0, price=0.0, total=0.0,
          receiver=user.full_name, diet=user.diet,
          allergies=user.allergies, served="", tax_category=""
        ))
    return signups
  
  @rx.var(cache=False)
  def dinner_count(self) -> int:
    return len(self.dinner_signups)
  
  @rx.var(cache=False)
  def dinner_count_vegan(self) -> int:
    count = 0
    for order in self.dinner_signups:
      if order.diet == "Vegan":
        count += 1
    return count
  
  @rx.var(cache=False)
  def dinner_count_vegetarian(self) -> int:
    count = 0
    for order in self.dinner_signups:
      if order.diet == "Vegetarian":
        count += 1
    return count
  
  @rx.var(cache=False)
  def dinner_count_meat(self) -> int:
    count = 0
    for order in self.dinner_signups:
      if order.diet == "Meat":
        count += 1
    return count
  
  @rx.var(cache=False)
  def get_user_debt(self) -> float:
    return sum([order.total for order in self.current_user_orders])
  
