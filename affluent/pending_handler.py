import os
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "..", "data")
os.makedirs(data_dir, exist_ok=True)

import pandas as pd
import numpy as np

class PendingHandler:
    def __init__(self, filename :str="submitted_movies.xlsx", save_filename: str="movies.xlsx", include_processed: bool=False, user_id: str=None) ->None:
        self.path = os.path.join(data_dir, filename)
        self.save_path = os.path.join(data_dir, save_filename)
        self.submitted_movies = None
        self.last_modified = 0
        self.include_preocessed = include_processed
        self.user_id = user_id
        self.load_submitted_movies(include_processed, user_id)

    def load_submitted_movies(self, include_processed: bool=False, user_id: str=None) ->None:   #for loading the excel file into a df

        if os.path.exists(self.path): #if the file exists loading into temp df else creating empty df with columns
            df = pd.read_excel(self.path)
            if not include_processed: 
                df = df[~(df["status"]=="processed")] #excluding processed rows if set to False
                if user_id is not None: df = df[df["submitted_by"]==user_id]
        else:
            df = pd.DataFrame(columns=["id", "movie_id", "title", "genre", "year", "type", "submitted_by", "status", "reason", "reviewed_by"])   #assigning empty columns if no file exists
            self.save_movies(path=self.path)
        
        self.submitted_movies = df
        self.last_modified = os.path.getmtime(self.path)

    def check_and_reload(self): #function to check if the file has been modified
        current_modified = os.path.getmtime(self.path)
        if current_modified > self.last_modified: self.load_submitted_movies(include_processed=self.include_preocessed, user_id=self.user_id)
    
    def save_movies(self, path=None) ->None|dict:
        
        if path and path == self.path:  #saving submitted file if path given and returning
            self.submitted_movies.to_excel(self.path, index=False)
            return None
        
        df_pending = self.submitted_movies  #copying the df into a local var
        filtered_df = df_pending[(df_pending["type"]=="new")&(df_pending["status"]=="approved")]    #filtering based on recent approved
        if filtered_df.empty: return None

        rejected_ids = []   #creating a list at the start to store the total rejected ids

        #filtering out the df using NaN values in the reviewed_by column and adding those ids to the list
        rejected_df_nan = filtered_df[filtered_df["reviewed_by"].isna()]
        rejected_ids_nan = rejected_df_nan["id"].tolist()
        rejected_ids.extend(rejected_ids_nan)   #appending the rejected ids to the main list

        #if there is any NaN values then setting the status to 'rejected' and adding reason then saving the submitted df
        if not rejected_df_nan.empty:
            self.submitted_movies.loc[self.submitted_movies["id"].isin(rejected_ids_nan), ["status", "reason"]] = ["rejected", "reviwed_by is NaN"]
            # self.save_movies(path=self.path)
        
        #getting the non NaN values in the reviewed_by section and if all NaN returning the rejected df
        filtered_df = filtered_df[filtered_df["reviewed_by"].notna()]
        if filtered_df.empty: return self.submitted_movies[self.submitted_movies["id"].isin(rejected_ids)].to_dict(orient="records") if rejected_ids else None

        filtered_df = filtered_df.sort_values("id") #sorting the df using ids and creating another column and filling it with stipped and lowered version of the title
        filtered_df["normalized_title"] = filtered_df["title"].str.strip().str.lower()
        
        duplicate_mask = filtered_df.duplicated(subset=["normalized_title", "year"], keep="last")   #keeping the last id if matched
        if duplicate_mask.any():    #setting the status of those duplicated ids to rejected and adding reason then saving
            duplicate_ids = filtered_df.loc[duplicate_mask, "id"].tolist()
            rejected_ids.extend(duplicate_ids)  #adding the duplicate rejected ids to the main list
            self.submitted_movies.loc[self.submitted_movies["id"].isin(duplicate_ids), ["status", "reason"]] = ["rejected", "duplicate submission"]
            # self.save_movies(path=self.path)
            
            filtered_df = filtered_df[~(duplicate_mask)]    #filtering out the non-duplicated mask
            

        if os.path.exists(self.save_path): df_main = pd.read_excel(self.save_path)  #getting the main movies file
        else: df_main = pd.DataFrame(columns=["movie_id","title","genre","year"])
    
        movie_id = df_main["movie_id"].max() if not df_main.empty else 0    #getting the max movie id

        na_mask = filtered_df["movie_id"].isna()    #getting the NaN movie_id rows
        if na_mask.any():   #generating a list from the movie_id and count range and assinging those NaN values according to the list
            count_na = na_mask.sum()
            new_movie_ids = list(range(movie_id + 1, movie_id + count_na + 1))
            filtered_df.loc[na_mask, "movie_id"] = new_movie_ids

        #normalizing titles from main file and adding them to another column and comparing those values 
        df_main["normalized_title"] = df_main["title"].str.strip().str.lower()

        #merging both files and creating another column called _merge and only keeping the submitted merged ones(meaning only the new ones)
        merged = filtered_df.merge(df_main[["normalized_title", "year"]], on=["normalized_title", "year"], how="left", indicator=True)  

        #selecting only the new additions and defining it to a new df with filtered columns
        new_movies = merged[merged["_merge"]=="left_only"]
        new_movies_id = new_movies["id"].tolist()   #getting the unique movies id and filtering the df
        filtered_df = filtered_df[filtered_df["id"].isin(new_movies_id)]
        rows_to_add = new_movies[["movie_id", "title", "genre", "year"]]

        #getting the duplicate datas, converting their ids to list and setting their status to 'rejected' and adding reason then saving
        duplicate_movies_main = merged[merged["_merge"]=="both"]
        duplicate_ids_main = duplicate_movies_main["id"].tolist()
        rejected_ids.extend(duplicate_ids_main) #appending the duplicate ids to the main list
        if duplicate_ids_main:
            self.submitted_movies.loc[self.submitted_movies["id"].isin(duplicate_ids_main), ["status", "reason"]] = ["rejected", "movie already exists in the database"]
            # self.save_movies(path=self.path)

        #dropping the new columns
        filtered_df = filtered_df.drop(columns=["normalized_title"])
        df_main = df_main.drop(columns=["normalized_title"])

        if not rows_to_add.empty:
            df_main = pd.concat([df_main, pd.DataFrame(rows_to_add)], ignore_index=True)   #adding to the end of main file and saving
            df_main.to_excel(self.save_path, index=False)

        #getting the ids of the saved df and changing those status from "approved" to "processed" and saving to the submitted files
        processed_ids = filtered_df["id"].tolist() 
        self.submitted_movies.loc[self.submitted_movies["id"].isin(processed_ids), 'status'] = "processed"
        self.save_movies(path=self.path)

        #getting the df of the rejected ids and converting it to a dict with record orient and retuning
        return self.submitted_movies[self.submitted_movies["id"].isin(rejected_ids)].to_dict(orient="records") if rejected_ids else None

    def update_movies(self) ->None|dict:
        
        df_pending = self.submitted_movies  #copying the database to a local var
        filtered_df = df_pending[(df_pending["type"]=="edit")&(df_pending["status"]=="approved")]   #filtering the df based on recent approved status
        if filtered_df.empty: return None

        rejected_ids = []   #creating a list to store all the rejected ids
        
        #filtering out the df using NaN values in the reviewed_by column
        rejected_df = filtered_df[filtered_df["reviewed_by"].isna()]

        #if there is any NaN values then setting the status to 'rejected' and adding reason then saving the submitted df
        if not rejected_df.empty:
            rejected_ids.extend(rejected_df["id"].tolist())  #adding the ids to the list
            self.submitted_movies.loc[self.submitted_movies["id"].isin(rejected_df["id"].tolist()), ["status", "reason"]] = ["rejected", "reviewed_by is NaN"]
            # self.save_movies(path=self.path)
        
        #getting the non NaN values in the reviewed_by section and retuning the rejected df after filtering from the submitted file if filtered_df is empty after filtering
        filtered_df = filtered_df[filtered_df["reviewed_by"].notna()]
        if filtered_df.empty:  return self.submitted_movies[self.submitted_movies["id"].isin(rejected_ids)].to_dict(orient="records") if rejected_ids else None

        if os.path.exists(self.save_path): df_main = pd.read_excel(self.save_path)  #getting the data from main file and assigning it to a local df
        else: df_main = pd.DataFrame(columns=["movie_id", "title", "genre", "year"])

        #filtering out the duplicate ids keeping the latest one and setting the status to 'rejected' and adding reason after converting the ids to a list
        duplicate_mask = filtered_df.sort_values("id").duplicated(subset=["movie_id"], keep="last")
        if duplicate_mask.any():
            duplicate_ids = filtered_df.loc[duplicate_mask, "id"].tolist()
            rejected_ids.extend(duplicate_ids)  #adding the duplicate ids to the list
            self.submitted_movies.loc[self.submitted_movies["id"].isin(duplicate_ids), ["status", "reason"]] = ["rejected", "duplicate submission"]
            # self.save_movies(path=self.path)

            filtered_df = filtered_df[~(duplicate_mask)]    #keeping only the latest values
            
        if not filtered_df.empty:
            merged = df_main.merge(filtered_df, on="movie_id", how="left", suffixes=("", "_new"))   #merging with the main file with defining the process into a local var and defining it later

            for col in ["title", "genre", "year"]:  #combing the new columns with the old one for filling the NaN values with the old data
                new_col = f"{col}_new"
                if new_col in merged.columns:
                    merged[col] = merged[new_col].combine_first(merged[col])

            merged.drop(columns=[c for c in merged.columns if c.endswith("_new")], inplace=True)    #deleting the new columns after merging and saving
            merged.to_excel(self.save_path, index=False)

        processed_ids = filtered_df["id"].tolist()  #getting the updated ids and changing their status from 'approved' to 'processed' and saving those in the submitted file and saving it
        self.submitted_movies.loc[self.submitted_movies["id"].isin(processed_ids), "status"] = "processed"
        self.save_movies(path=self.path)

        #filtering out the data from the submitted df using the rejected ids
        return self.submitted_movies[self.submitted_movies["id"].isin(rejected_ids)].to_dict(orient="records") if rejected_ids else None

    def submit_movie(self, movie_id: int=None, title: str=None, genre: str=None, year: int=None, type: str=None, submitted_by: int=None) ->None:

        if type not in ("edit", "new"): raise ValueError("type must be 'new' or 'edit'")    #raising error if data mismatched
        if type == "edit" and movie_id is None: raise ValueError("movie_id is required for 'edit' requests")
        if type == "new" and movie_id is None: movie_id = np.nan    #setting the movie_id to NaN if not given
        
        self.check_and_reload()

        if len(self.submitted_movies) == 0: id = 1  #setting the id for the data
        else: id = self.submitted_movies["id"].max() + 1
       
        #making a new row and concating it to the submitted file and saving it
        new_row = {
            "id": id,
            "movie_id": movie_id,
            "title": title,
            "genre": genre,
            "year": year,
            "type": type,
            "submitted_by": submitted_by,
            "status": "pending",
            "reason": np.nan,
            "reviewed_by": np.nan
        }

        self.submitted_movies = pd.concat([self.submitted_movies, pd.DataFrame([new_row])], ignore_index=True)
        self.save_movies(path=self.path)

    #showing data from the submitted df based on the filters and returning as a dict in records orient
    def show_submitted(self, ids: list=None, movie_id: list=None, type: str=None, submitted_by: str=None, status: str=None, reason: str=None, reviewed_by: str=None, limit: int=5) ->dict|None:
        if all(x is None for x in (ids, movie_id, type, submitted_by, status, reason, reviewed_by)): return None

        self.check_and_reload()

        #assigning the submitted df to a local df and adding mask to filter based on the filters
        df = self.submitted_movies
        mask = pd.Series(True, index = self.submitted_movies.index)
        if ids is not None: mask &= df["id"].isin(ids)
        if movie_id is not None: mask &= df["movie_id"].isin(movie_id)
        if type is not None: mask &= df["type"] == type
        if submitted_by is not None: mask &= df["submitted_by"] == submitted_by
        if status is not None: mask &= df["status"] == status
        if reason is not None: mask &= df["reason"].str.contains(reason, case=False, na=False)
        if reviewed_by is not None: mask &= df["reviewed_by"] == reviewed_by

        return df[mask].tail(limit).to_dict(orient="records")
    
    #updating data in the submitted df based on the given values and only if status and reviewed_by matches to avoid overwritting
    def update_submitted(self, update_dict: dict=None, status: str=None, reviewed_by: str=None) ->None|dict:
        if update_dict is None: return None

        self.check_and_reload()

        #converting the dict into a local df and filtering accepted and rejected rows
        update_df = pd.DataFrame(update_dict)
        mask = self.submitted_movies["id"].isin(update_df["id"].tolist())
        if status is not None: mask &= self.submitted_movies["status"] == status ; rejected_mask_temp = self.submitted_movies["status"] != status
        if reviewed_by is not None: mask &= self.submitted_movies["reviewed_by"] == reviewed_by ; rejected_mask_temp &= self.submitted_movies["reviewed_by"] != reviewed_by
        if rejected_mask_temp.any():
            rejected_mask = self.submitted_movies["id"].isin(update_df["id"].tolist()) & rejected_mask_temp

        if mask.any():  #checking if any row is satisfied
            update_df = update_df.set_index("id").loc[self.submitted_movies.loc[mask, "id"]]

            self.submitted_movies.loc[mask, ["movie_id", "title", "genre", "year", "type", "submitted_by", "status", "reason", "reviewed_by"]] = update_df[["movie_id", "title", "genre", "year", "type", "submitted_by", "status", "reason", "reviewed_by"]].values
            self.save_movies(path=self.path)

        if rejected_mask_temp.any():
            return self.submitted_movies[rejected_mask].to_dict(orient="records")
        else: return None

    def clear_all(self) ->None: #setting the df to empty ans saving it
        self.submitted_movies = pd.DataFrame(columns=["id", "movie_id", "title", "genre", "year", "type", "submitted_by", "status", "reason", "reviewed_by"])
        self.save_movies(path=self.path)

    def clear_specific(self,id: str=None, movie_id: int=None, type: str=None, submitted_by: str=None) ->None:    #filtering the df using the data and removing it from the file
        self.check_and_reload()
        
        df = self.submitted_movies
        if id is None:
            df = df[~((df["movie_id"]==movie_id) & (df["type"]==type) & (df["submitted_by"]==submitted_by))]
        else: df = df[~(df["id"]==id)]
        self.submitted_movies = df
        self.save_movies(path=self.path)

    #the function recieves a dict and the reviewer's username and makes changes the status and reason according to the reviewer's decision
    def change_status_submitted(self, decision_dict: dict, reviewed_by: str) ->None|dict: #the decision_dict should be in the "records" orient
        if decision_dict is None and reviewed_by is None: return None
        
        self.check_and_reload()

        df_update = pd.DataFrame(decision_dict) #converting the dict into a df and filtering out the ids with the dict ids
        mask = (self.submitted_movies["id"].isin(df_update["id"].tolist())) & (self.submitted_movies["status"]=="reviewing") & (self.submitted_movies["reviewed_by"]==reviewed_by)
        rejected_mask = (self.submitted_movies["id"].isin(df_update["id"].tolist())) & ((self.submitted_movies["status"]!="reviewing") | (self.submitted_movies["reviewed_by"]!=reviewed_by))

        #rearraging the ids by filtering out the ids from the the submitted file using mask
        df_update = df_update.set_index("id").loc[self.submitted_movies.loc[mask, "id"]] 
        
        #updating the values of the specific columns and saving
        self.submitted_movies.loc[mask, ["status", "reason", "reviewed_by"]] = df_update[["status", "reason", "reviewed_by"]].values  
        self.save_movies(path=self.path)

        if rejected_mask.any():
            return self.submitted_movies[rejected_mask].to_dict(orient="records")
        
    #getting the data of given ids from the submitted file and setting the status to 'reviewing' and reviewed_by to the dev name
    def mark_as_reviewing(self, ids: list, reviewed_by: str) ->dict|None:   
        if any(x is None for x in(ids, reviewed_by)): return None
        
        self.check_and_reload()

        mask = self.submitted_movies["id"].isin(ids) & self.submitted_movies["status"] == "pending"
        self.submitted_movies.loc[mask, ["status", "reviewed_by"]] = ["reviewing", reviewed_by]
        self.save_movies(path=self.path)

        return self.submitted_movies[mask].to_dict(orient="records")


#need to change the save funcion so that it auto puts the nan movie ids from the movies data before saving  #completed
#need to check the update function logic    #completed