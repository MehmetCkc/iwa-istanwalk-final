from flask_login import UserMixin


class User(UserMixin):
    def __init__(
        self, id, name, surname, email, user_type, profile_picture=None, location=None
    ):
        self.id = id
        self.name = name
        self.surname = surname
        self.email = email
        self.user_type = user_type
        self.profile_picture = profile_picture
        self.location = location

    def getFullName(self):
        return f"{self.name} {self.surname}"

    def isGuide(self):
        return self.user_type == "guide"

    def isCustomer(self):
        return self.user_type == "member"

    def isAdmin(self):
        return self.user_type == "admin"
