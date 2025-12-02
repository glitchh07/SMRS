import pandas as pd
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "..", "data")
os.makedirs(data_dir, exist_ok=True)

class DataHandler:
    def __init__(self, filename: str="data.xlsx") ->None:
        self.path = os.path.join(data_dir, filename)
        self.last_modified = 0
        self.data = None
        self.load_data()

    def load_data(self) ->None:

        if os.path.exists(self.path): self.data = pd.read_excel(self.path)
        else:
            self.data = pd.DataFrame(columns=["user_id", "movie_id", "rating", "would_recommend"])
            self.save_data()
        self.last_modified = os.path.getmtime(self.path)

    def save_data(self) ->None:
        self.data.to_excel(self.path, index=False)

    def check_and_reload(self):
        current_modified = os.path.getmtime(self.path)

        if current_modified > self.last_modified: self.load_data()
    
    def add_data(self, user_id: int, movie_id: int, rating: int|None, would_recommend: bool|None) ->None:

        self.check_and_reload()

        new_row = {
            "user_id": user_id,
            "movie_id": movie_id,
            "rating": rating,
            "would_recommend": float(would_recommend)
        }

        self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)
        self.save_data()
        self.load_data()

    @staticmethod
    def mean_calculate(df: pd.DataFrame) ->dict:

        return {
            "avg_rating": round(df['rating'].mean(), 1) if not df.empty else None,
            "recommend_ratio": df["would_recommend"].mean() if "would_recommend" in df.columns and not df.empty else None,
            "rating_count": df["rating"].count()
        }

    def get_data(self, mean_calc: bool=True, user_id: int=None, movie_id: int=None, rating: int=None, would_recommend: bool=None) ->dict|None:
        if all(x is None for x in (user_id, movie_id, rating, would_recommend)): return None
        
        self.check_and_reload()

        df = self.data
        mask = pd.Series(True, index=df.index)

        if user_id is not None: mask &= (df['user_id'] == user_id)
        if movie_id is not None: mask &= (df['movie_id'] == movie_id)
        if rating is not None: mask &= (df['rating'] >= rating)
        if would_recommend is not None: mask &= (df['would_recommend'] == would_recommend)

        filtered_df = df[mask]
        if filtered_df.empty: return None

        if mean_calc: return self.mean_calculate(filtered_df)
        else: return filtered_df.to_dict(orient="records")

    def update_data(self, user_id: int=None, movie_id: int=None, rating:int =None, would_recommend:bool=None) ->None:
        if user_id is None or movie_id is None: return None

        self.check_and_reload()

        mask = (self.data["user_id"]==user_id) & (self.data["movie_id"]==movie_id)
        self.data.loc[mask, ["rating","would_recommend"]] = [rating, float(would_recommend)]

        self.save_data()

# data = DataHandler()
# print(data.get_data(user_id=1, mean_calc=False))
