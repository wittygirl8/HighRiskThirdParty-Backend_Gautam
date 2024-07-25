import base64
import traceback

from utils.db import MSSQLConnection

db = MSSQLConnection()
from flask import current_app as app

class User:

    def login(self, data):
        try:
            username = data.get("username")
            app.logger.info(data.get("password"))
            password = base64.b64decode(data.get("password")).decode("utf-8")
            user = db.select(f"SELECT * FROM [app].[user] where username='{username}' and password='{password}' "
                             f"and isActive=1")
            if user:
                user = user[0]
                country = []
                if "type" in data and data["type"] == "admin":
                    pass
                else:
                    access = db.select(f"SELECT * FROM app.access a join app.country c on c.id = a.country_id "
                                       f"where user_id='{user['id']}'")
                    for each in access:
                        country.append(each["code"])
                user["country"] = country
                return user
        except Exception as e:
            print("Features.case_login(): " + str(e))
            traceback.print_exc()
            return None

    @staticmethod
    def get_claims(data):
        claims = []
        return claims

    def create(self, data):  # tbd
        try:

            return True, 'User Created successfully', {}
        except Exception as e:
            print("User.create(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def get_all(self, data):
        try:
            query = """
                select id, 
                    username, 
                    type, 
                    name, 
                    email, 
                    phone, 
                    isActive, 
                    updatedBy, 
                    createdOn, 
                    lastLoggedIn 
                from [app].[user]
            """
            users = db.select(query)
            return True, "All portal users", users
        except Exception as e:
            print("User.get_all(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def update(self, data):  # tbd
        try:
            # YOUR CODE HERE
            return True, 'User updated successfully', {}
        except Exception as e:
            print("User.update(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def delete(self, data):
        try:
            if "user_id" not in data and not data["user_id"]:
                return False, "Input error"
            _ret = db.exec(f"delete from [app].[user] WHERE user_id=?", data["user_id"])
            if not _ret:
                raise Exception("Something went wrong")
            return True, 'User deleted successfully', {}
        except Exception as e:
            print("User.delete(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"

    def status_update(self, data):
        try:
            if "user_id" not in data and not data["user_id"] and "status" not in data:
                return False, "Input error"
            _ret = db.exec(f"UPDATE [app].[user] SET isActive = ? WHERE id = ?", data["status"], data["user_id"])
            if not _ret:
                raise Exception("Something went wrong")
            return True, 'User updated successfully', {}
        except Exception as e:
            print("User.status_update(): " + str(e))
            traceback.print_exc()
            return False, "Something went wrong"
