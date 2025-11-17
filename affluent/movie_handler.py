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
    
    def get_movie(self, movie_id: int) ->dict:
        movie = self.movies[self.movies['movie_id'] == movie_id]
        if len(movie) == 0: return None

        return movie.iloc[0].to_dict()
    
# movie_handler = MovieHandler()
# print(movie_handler.get_movie(101))