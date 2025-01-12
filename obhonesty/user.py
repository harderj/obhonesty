from typing import Dict
import reflex as rx

class User(rx.Base):
  name: str
  password: str
  email: str
  telephone: str
  address: str

  def __str__(self):
    return f"User(name={self.name}, password={self.password})"

  @staticmethod
  def from_dict(x: Dict[str, str]):
    return User(
      name=x['name'],
      password=x['password'],
      email=x['email'],
      telephone=x['telephone'],
      address=x['address']
    )

