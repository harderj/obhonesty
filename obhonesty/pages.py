from datetime import datetime
from typing import Callable

import reflex as rx

from obhonesty.aux import two_decimal_points
from obhonesty.constants import breakfast_items, tax_categories
from obhonesty.item import Item
from obhonesty.order import Order
from obhonesty.state import State
from obhonesty.user import User


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
            rx.form(
              rx.flex(
                rx.input(
                  name="item_name",
                  type="hidden",
                  value=item.name
                ),
                rx.input(
                  placeholder="Quantity",
                  name="quantity",
                  default_value='1.0',
                  type="number"
                )
              ),
              rx.flex(
                rx.dialog.close(
                  rx.button("Register", type="submit")
                ), 
                rx.dialog.close(rx.button(f"Cancel")),
                spacing="3",
                justify="end" 
              ),
              on_submit=State.order_item
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
    rx.foreach(State.items.values(), item_button)
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
            ),
            rx.input(
              placeholder="Phone number (required)",
              name="phone_number",
              required=True
            ),
            rx.input(
              placeholder="Email (required)",
              name="email",
              required=True,
              type="email"
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
          rx.text("Note: you are signing up for todays dinner. Sign up again tomorrow for tomorrows dinner."),
          rx.spacer(),
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
          rx.text("Note: you are signing up for todays breakfast. Sign up again tomorrow for tomorrows breakfast."),
          rx.spacer(),
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
  def show_row(order: Order):
    return rx.table.row(
      rx.table.cell(order.time),
      rx.table.cell(order.item),
      rx.table.cell(f"{order.quantity}"),
      rx.table.cell(f"{order.price}€"),
      rx.table.cell(f"{order.total}€")
    )
  
  return rx.container(rx.center(rx.vstack(
    rx.heading(f"Hello {State.current_user.nick_name}"),
    rx.button(f"Back to orders and items", on_click=rx.redirect("/user")),
    rx.table.root(
      rx.table.header(
        rx.table.row(
          rx.table.column_header_cell("Time"),
          rx.table.column_header_cell("Item"),
          rx.table.column_header_cell("Quantity"),
          rx.table.column_header_cell("Unit Price"),
          rx.table.column_header_cell("Total")
        )
      ),
      rx.table.body(
        rx.foreach(
          State.current_user_orders, show_row
        )
      )
    )
  )))

def admin() -> rx.Component:
  def user_button(user: User):
    return rx.button(
      f"{user.full_name} ({user.nick_name})",
      on_click=State.redirect_to_admin_user_page(user)
    )
  return rx.container(rx.center(
    rx.vstack(
      rx.heading(f"Admin"),
      rx.button("Dinner", on_click=rx.redirect("/admin/dinner")),
      rx.button("Breakfast", on_click=rx.redirect("/admin/breakfast")),
      rx.button("Tax", on_click=rx.redirect("/admin/tax")),
      rx.text("Users:"),
      rx.foreach(State.users, user_button)
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
  def show_signup(signup: Order):
    return rx.table.row( 
      rx.table.cell(signup.receiver),
      rx.table.cell(signup.diet),
      rx.table.cell(signup.allergies)
    )

  return rx.container(rx.center(
    rx.vstack(
      rx.heading("Dinner"),
      rx.button("Go back", on_click=rx.redirect("/admin")),
      rx.text(f"Total eating dinner: {State.dinner_count}"),
      rx.text(f"Vegan: {State.dinner_count_vegan}"),
      rx.text(f"Vegatarian: {State.dinner_count_vegetarian}"),
      rx.text(f"Meat: {State.dinner_count_meat}"),
      rx.table.root(
        rx.table.header(
          rx.table.row(
            rx.table.column_header_cell("Name"),
            rx.table.column_header_cell("Diet"),
            rx.table.column_header_cell("Allergies")
          )
        ),
        rx.table.body(
          rx.foreach(State.dinner_signups, show_signup)
        ),
        variant="surface",
        size="3"
      )
    )
  ))

def admin_breakfast() -> rx.Component:
  def show_signup(signup: Order):
    return rx.table.row( 
      rx.table.cell(signup.time),
      rx.table.cell(signup.receiver),
      rx.table.cell(signup.diet),
      rx.table.cell(signup.allergies)
    )

  return rx.container(rx.center(
    rx.vstack(
      rx.heading("Breakfast"),
      rx.button("Go back", on_click=rx.redirect("/admin")),
      rx.table.root(
        rx.table.header(
          rx.table.row(
            rx.table.column_header_cell("Time"),
            rx.table.column_header_cell("Name"),
            rx.table.column_header_cell("Diet"),
            rx.table.column_header_cell("Allergies")
          )
        ),
        rx.table.body(
          rx.foreach(State.breakfast_signups, show_signup)
        ),
        variant="surface",
        size="3"
      )
    )
  ))

def admin_user_page() -> rx.Component:
  return rx.container(rx.center(rx.vstack(
    rx.heading("User information"),
    rx.button("Go back", on_click=rx.redirect("/admin")),
    rx.text(f"Full name: {State.current_user.full_name}"),
    rx.text(f"Nick name: {State.current_user.nick_name}"),
    rx.text(f"Email: {State.current_user.email}"),
    rx.text(f"Phone: {State.current_user.phone_number}"),
    rx.text(f"Address: {State.current_user.address}"),
    rx.text(f"Owes: {State.get_user_debt}€")
  )))