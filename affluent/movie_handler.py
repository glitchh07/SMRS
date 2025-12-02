import pandas as pd
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "..", "data")
os.makedirs(data_dir, exist_ok=True)

class MovieHandler:
    def __init__(self, filename :str="movies.xlsx") ->None:
        self.path = os.path.join(data_dir, filename)
        self.movies = None
        self.load_movies()

    def load_movies(self) ->None:   #for loading the excel file into a df

        if os.path.exists(self.path): self.movies = pd.read_excel(self.path)
        else:
            self.movies = pd.DataFrame(columns=["movie_id", "title", "genre", "year"])   #assigning empty columns if no file exists
            self.save_movies()

    def save_movies(self) ->None:
        self.movies.to_excel(self.path, index=False)

    def add_movie(self, title: str, genre: str, year: int) ->int:

        if len(self.movies) == 0: movie_id = 1
        else: movie_id = self.movies['movie_id'].max() + 1

        new_row = {
            "movie_id": movie_id,
            "title": title,
            "genre": genre,
            "year": year
        }

        self.movies = pd.concat([self.movies, pd.DataFrame([new_row])], ignore_index=True)
        self.save_movies()
        return movie_id
    
    def get_movie(self, movie_id: list=None, title: str=None, genre: list=None, year: int=None) ->dict|None:
        if all(x is None for x in(movie_id, title, genre, year)): return None

        if isinstance(genre, str): genre = [genre]   #converting the genre if its a str
        
        df = self.movies
        mask = pd.Series(True, index=df.index)

        if movie_id is not None and isinstance(movie_id, list): mask &= (df['movie_id'].isin(movie_id))
        if title is not None: mask &= df['title'].str.contains(title, case=False, na=False)
        if genre is not None:
            genre_mask = pd.Series(False, index=df.index)
            for g in genre:
                genre_mask |= df['genre'].str.contains(g, case=False, na=False)
            mask &= genre_mask
        if year is not None: mask &= (df['year']==year)

        if mask.empty: return None  #checking for valid mask

        filtered_movies = df[mask]
        if filtered_movies.empty: return None

        return filtered_movies.to_dict(orient="records")

    
# movie_handler = MovieHandler()
# print(movie_handler.get_movie(101))