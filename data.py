from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Items, Users

# Create database and create a shortcut for easier to update database
engine = create_engine('sqlite:///appitemcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Creating an user
user_one = Users(name="admin", email="admin@admin.com")
session.add(user_one)
session.commit()

# Transportation
category_one = Category(user_id=1, name="Transportation")
session.add(category_one)
session.commit()

# Household
category_two = Category(user_id=1, name="Household")
session.add(category_two)
session.commit()

# Adding items into Category
item = Items(user_id=1, name="Tires",
             description="Tires made of Rubber"
             "They are the main parts in vehicles.",
             Category=category_one)
session.add(item)
session.commit()

item = Items(user_id=1, name="Oil",
             description="Oils provides lubrication to the engines "
             "Oil is most essential item in todays vehicle industries. ",
             Category=category_one)
session.add(item)
session.commit()

item = Items(user_id=1, name="Washing Machine",
             description="The machine that washes our clothes"
             "without human efforts. ",
             Category=category_two)
session.add(item)
session.commit()

item = Items(user_id=1, name="Microwave",
             description="Microwave helps us to prepare food easily & "
             "fast. It is the important items in todays kitchen",
             Category=category_two)
session.add(item)
session.commit()


print("added Category and Items!")
