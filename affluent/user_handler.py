import pandas as pd
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "..", "data")
os.makedirs(data_dir, exist_ok=True)
# print(base_dir)

class UserHandler:
    def __init__(self, filename: str="users.xlsx") ->None:
        
        self.path = os.path.join(data_dir, filename)
        self.users = None
        self.load_users()

    def load_users(self) ->None:   #for loading the excel file into a df

        if os.path.exists(self.path): self.users = pd.read_excel(self.path)
        else:
            self.users = pd.DataFrame(columns=["user_id", "username", "age"])   #assigning empty columns if no file exists
            self.save_users()

    def save_users(self) ->None:
        self.users.to_excel(self.path, index=False)

    def add_user(self, username: str, age: int) ->int:

        if len(self.users) == 0: user_id = 1
        else: user_id = self.users['user_id'].max() + 1

        new_row = {
            "user_id": user_id,
            "username": username,
            "age": age
        }

        self.users = pd.concat([self.users, pd.DataFrame([new_row])], ignore_index=True)
        self.save_users()
        return user_id
    
    def get_user(self, user_id: int=None, username: str=None) ->dict|None:
        if user_id is None and username is None: return None
        
        if user_id is not None: user = self.users[self.users['user_id'] == user_id]
        else: user = self.users[self.users['username'] == username]
        if len(user)==0: return None

        return user.iloc[0].to_dict()
    

# users = UserHandler()
# print(users.get_user(username="Alice"))