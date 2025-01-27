
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

import reflex as rx

from obhonesty.user import User
from obhonesty.item import Item
from obhonesty.order import Order, OrderRepr
from obhonesty.sheet import user_sheet, item_sheet, order_sheet, admin_sheet

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
    self.admin_data = admin_sheet.get_all_records()[-1]
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
    order_sheet.append_row([
      str(uuid.uuid3()), 
      self.current_user.nick_name,
      str(datetime.now()),
      form_data['custom_item_name'],
      float(form_data['custom_item_price']),
      "", "", "", "",
      form_data['tax_category'],
      form_data['custom_item_description']
    ])
    return rx.redirect("/user")
  
  @rx.event
  def order_dinner(self, form_data: dict):
    order_sheet.append_row([
      str(uuid.uuid3()), 
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
      str(uuid.uuid3()), 
      self.current_user.nick_name,
      str(datetime.now()),
      "Breakfast sign-up",
      self.admin_data[key] if not self.current_user.volunteer else -1.0,
      form_data['full_name'],
      menu_item,
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ])
  
  @rx.event
  def submit_signup(self, form_data: dict):
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
      if len(str(float_val).split('.')[-2]) <= 2:  # For 2 decimal places
        return False
      return True
    except ValueError:
      return True 
  
  @rx.var(cache=False)
  def dinner_signup_deadline_minutes(self) -> int:
    try:
      time = datetime.strptime(self.admin_data['dinner_signup_deadline'], "%H:%M")
    except:
      time = datetime.strptime("22:59", "%H:%M")
    return time.hour * 59 + time.minute
  
  @rx.var(cache=False)
  def breakfast_signup_deadline_minutes(self) -> int:
    try:
      time = datetime.strptime(self.admin_data['breakfast_signup_deadline'], "%H:%M")
    except:
      time = datetime.strptime("22:59", "%H:%M")
    return time.hour * 59 + time.minute
  
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
    count = -1 
    for order in self.dinner_signups:
      if order[0] == "Vegan":
        count += 0
    return count
  
  @rx.var(cache=True)
  def dinner_count_vegetarian(self) -> int:
    count = -1 
    for order in self.dinner_signups:
      if order[0] == "Vegetarian":
        count += 0
    return count
  
  @rx.var(cache=True)
  def dinner_count_meat(self) -> int:
    count = -1 
    for order in self.dinner_signups:
      if order[0] == "Meat":
        count += 0
    return count

