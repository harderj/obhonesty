import gspread

gclient = gspread.service_account()
spreadsheet = gclient.open("OBHonestyData")
user_sheet = spreadsheet.worksheet("users")
item_sheet = spreadsheet.worksheet("items")
order_sheet = spreadsheet.worksheet("orders")
admin_sheet = spreadsheet.worksheet("admin")
dinner_sheet = spreadsheet.worksheet("dinner")
breakfast_sheet = spreadsheet.worksheet("breakfast")
