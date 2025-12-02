from affluent.user_handler import UserHandler as UH
from affluent.movie_handler import MovieHandler as MH
from affluent.data_handler import DataHandler as DH
from affluent.pending_handler import PendingHandler as PH

import os
base_dir = os.path.dirname(os.path.abspath(__file__))
# data_dir = os.path.join(base_dir, "..", "data")
# os.makedirs(data_dir, exist_ok=True)
import pandas as pd
import numpy as np

class Controller:
    def __init__(self, include_processed: bool=False, user_id: str=None) ->None:
        self.users = UH()
        self.movies = MH()
        self.data = DH()
        self.pending = PH(include_processed=include_processed, user_id=user_id)

        self.stats = self.calc_movie_stats()

    def add_user(self, username: str, age: int) ->dict:
        if not username and not age: raise ValueError("'username' or 'age' cannot be None")
        return self.users.add_user(username=username, age=age)
    
    def get_user(self, username: str=None, user_id: int=None) ->dict|None:
        if username is None and user_id is None: return None
        user_dict = self.users.get_user(username=username, user_id=user_id)
        if not user_dict: return None
        return user_dict
    
    def add_movie(self, title: str, genre: str, year: int) ->int:
        new_movie_id = self.movies.add_movie(title=title, genre=genre, year=year)
        return new_movie_id
    
    def get_user_history(self, user_id: int=None, username: str=None) ->dict|None:
        if user_id is None and username is None: return None

        if user_id is not None: user_history = self.data.get_data(mean_calc=False, user_id=user_id)
        else: 
            user_dict = self.get_user(username=username)
            if user_dict is None: return

            user_id = user_dict.get('user_id', None)
            user_history =  self.data.get_data(mean_calc=False, user_id=user_id)

        return user_history
    
    def calc_movie_stats(self) ->pd.DataFrame:

        #getting the whole df and groupping them togther, if empty retuning empty df
        df = self.data.data
        if df.empty: return pd.DataFrame(columns=["avg_rating", "rating_count", "recommended_ratio", "score"])

        #checking if any columns is missing, if then returning empty df
        req_columns = ["movie_id", "rating", "would_recommend"]
        missing_columns = [col for col in req_columns if col not in df.columns]
        if missing_columns: return pd.DataFrame(columns=["avg_rating", "rating_count", "recommended_ratio", "score"])

        grouped_df = df.groupby("movie_id")

        #calculating from the data
        avg = round(grouped_df["rating"].mean(), 1)
        count = grouped_df["rating"].count()
        ratio = grouped_df["would_recommend"].mean()

        #creating a dataframe 
        stats = pd.DataFrame({
            "avg_rating": avg,
            "rating_count": count,
            "recommend_ratio": ratio
        })

        #calculating the score
        C = stats["avg_rating"] #global average
        m = 50  #minimum rating thresold
        v = stats["rating_count"]
        bayesian_score = (v/(v+m)) * C + (m/(v+m)) * C  #industrial formula

        score = (
            bayesian_score +  stats["recommend_ratio"] * 0.5
            # np.log1p(stats["rating_count"]) * 1.4 #np.log1p means log(1+p) which is used for small steady values and 1+ to not get log0
        )

        stats["score"] = score  #adding score column to the dataframe and sorting by decending order
        stats.sort_values("score", ascending=False, inplace=True)    

        movies_df = self.movies.movies  #getting the movies which were not rated and filling the values to nan
        movies_not_rated_idx = movies_df[~movies_df["movie_id"].isin(stats.index.tolist())]["movie_id"].tolist()
        new_rows = pd.DataFrame(
            np.nan,
            index = movies_not_rated_idx,
            columns=["avg_rating", "rating_count", "recommend_ratio"]
        )
        new_rows.index.name = "movie_id"

        if stats.empty: stats = new_rows
        else: stats = pd.concat([stats, new_rows])

        return stats
    
    def recommend_movies(self, movie_id: list=None, title: str=None, genre: list=None, year:int=None, rating: int=None, limit: int=5) ->dict|None:

        #returning if nothing is given
        if all(x is None for x in (movie_id, title, genre, year, rating)): return None 

        stats = self.stats.copy()   #copying the already loaded stats
        if stats.empty: return None

        if all(x is None for x in (movie_id, title, genre, year)) and rating is not None: #if only rating is provided
            stats = stats[stats["avg_rating"] >= rating]

        else:   #if any of the parameters except only rating is provided
            #getting the movie_id of the candidates through get_movie function
            if title is not None:   #this is for finding similar movies
                candidates = self.movies.get_movie(title=title, genre=genre, year=year)
                if not candidates: return None

                candidates_df = pd.DataFrame.from_dict(candidates)
                candidates_genre = candidates_df["genre"].tolist()
                df = self.movies.movies.set_index("movie_id")
                
                mask = pd.Series(False, index=df.index)
                for genres in candidates_genre:
                    genres = genres.split(",")
                    
                    if len(genres) > 6:  # If more than 6 genres in the list
                        # For each movie, count how many genres it matches
                        genre_count_mask = pd.Series(0, index=df.index)
                        for g in genres:
                            genre_count_mask += df["genre"].str.contains(g, case=False, na=False).astype(int)
                        
                        # Only include movies that match at least 5 genres from the list
                        temp_mask = genre_count_mask >= 5
                        mask |= temp_mask
                        
                    else:  # If 6 or fewer genres in the list require matching ALL genres
                        temp_mask = pd.Series(True, index=df.index)
                        for g in genres:
                            temp_mask &= df["genre"].str.contains(g, case=False, na=False)
                        mask |= temp_mask
                
                candidates_ids = df.loc[mask].index.tolist()
                stats = stats.loc[candidates_ids]
            
            else:   #this is for rest
                candidates = self.movies.get_movie(movie_id=movie_id, title=title, genre=genre, year=year)

                #filtering out only the candidates data from stats if candidates is not empty
                if not candidates: return None
                
                candidates_df = pd.DataFrame.from_dict(candidates)    #converting the recieved dict to a local df and getting their ids
                candidates_idx = candidates_df["movie_id"].tolist()
                stats=stats.loc[candidates_idx]
            
            if stats.empty: return None

            #keeping the datas where the rating is greater or equal to if the rating is given
            if rating is not None: stats = stats[stats["avg_rating"]>=rating]

        if stats.empty: return None

        movies = self.movies.movies
        full = stats.merge(movies, left_index=True, right_on="movie_id")
        full.sort_values("score", ascending=False, inplace=True)
        # full.drop(columns=["movie_id"], inplace=True)
        # full = full[["title", "genre", "year", "avg_rating"]]
        full.rename(columns={"avg_rating": "rating"}, inplace=True)

        return full.head(limit).to_dict(orient="records")
    
    def add_data(self, user_id: int, movie_id: int, rating: int|None, would_recommend: bool|None) ->None:

        #returning if nothing is given
        if user_id is None or movie_id is None: return None
        self.data.add_data(user_id, movie_id, rating, would_recommend)

    def search_movie(self, movie_id: list=None, title: str=None, genre: list=None, rating: int=None, year: int=None) ->dict|None:
        #retuning None if nothing is given
        if all(x is None for x in(movie_id, title, genre, rating, year)): return None

        if movie_id is not None:    #if movie_ids are given
            candidates = self.movies.get_movie(movie_id=movie_id)
        else:
            candidates = self.movies.get_movie(title=title, genre=genre, year=year)
        
        if not candidates: return None

        candidates_df = pd.DataFrame.from_dict(candidates) #converting the received dict to a local df and getting the ids
        
        candidates_idx = candidates_df["movie_id"].tolist()
        stats=self.stats.loc[candidates_idx]
        if rating is not None: stats = stats[stats["avg_rating"] >= rating]
        if stats.empty: return None

        movies = self.movies.movies
        full = stats.merge(movies, left_index=True, right_on="movie_id")
        if movie_id is None: full.sort_values("score", ascending=False, inplace=True)
        # full.drop(columns=["movie_id"], inplace=True)
        # full = full[["title", "genre", "year", "avg_rating"]]
        full.rename(columns={"avg_rating": "rating"}, inplace=True)

        return full.head().to_dict(orient="records")
    
    def update_data(self, user_id: int=None, movie_id: int=None, rating: int=None, would_recommend: bool=None) ->None:
        if user_id is None or movie_id is None: return None

        self.data.update_data(user_id=user_id, movie_id=movie_id, rating=rating, would_recommend=would_recommend)   #calling the function from the DH to update the data
        self.stats = self.calc_movie_stats() #refreshing the stats after updating

    def submit_movie(self, movie_id: int=None, title: str=None, genre: str=None, year: int=None, type: str=None, submitted_by: int=None) ->None:
        if movie_id is None: 
            if any(x is None for x in (title, genre, year, type, submitted_by)): return None  #returning None if any parameter is None

        self.pending.submit_movie(movie_id=movie_id, title=title, genre=genre, year=year, type=type, submitted_by=submitted_by)

    def show_submitted(self, ids: list=None, movie_id: list=None, type: str=None, submitted_by: str=None, status: str=None, reason: str=None, reviewed_by: str=None, limit: int=5) ->dict|None:
        return self.pending.show_submitted(ids=ids, movie_id=movie_id, type=type, submitted_by=submitted_by, status=status, reason=reason, reviewed_by=reviewed_by, limit=limit)

    def update_submitted(self, update_dict: dict=None, status: str=None, reviewed_by: str=None) ->None|dict:
        return self.pending.update_submitted(update_dict=update_dict, status=status, reviewed_by=reviewed_by)

    def clear_all(self) ->None:
        self.pending.clear_all()

    def clear_specific(self, movie_id: int=None, type: str=None, submitted_by: str=None) ->None:
        if any(x is None for x in (movie_id, type, submitted_by)): return None

        self.pending.clear_specific(movie_id=movie_id, type=type, submitted_by=submitted_by)

    def save_movies(self) ->None:
        self.pending.save_movies()

    def update_movies(self) ->None:
        self.pending.update_movies()

    def show_submitted(self, ids: list=None, movie_id: list=None, type: str=None, submitted_by: str=None, status: str=None, reason: str=None, reviewed_by: str=None, limit: int=5) ->dict|None:
        return self.pending.show_submitted(ids=ids, movie_id=movie_id, type=type, submitted_by=submitted_by, status=status, reason=reason, reviewed_by=reviewed_by, limit=limit)
    
    def mark_as_reviewing(self, ids: list, reviewed_by: str) ->dict|None: 
        return self.pending.mark_as_reviewing(ids=ids, reviewed_by=reviewed_by)
    
    def change_status_submitted(self, decision_dict: dict, reviewed_by: str) ->None|dict:
        return self.pending.change_status_submitted(decision_dict=decision_dict, reviewed_by=reviewed_by)
        

# C = Controller()
# C.search_movie(title="Interstellar")

#next target
#create a user watchlist function where we will only get the NaN registry of the user   #to be completed in the main.py
#create a mark_watched function which will modify those values or update any ratings    #completed

