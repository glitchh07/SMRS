import os
base_dir = os.path.dirname(os.path.abspath(__file__))

import pandas as pd
import numpy as np
from colorama import Fore, Style, init
init(autoreset=True)

from datetime import datetime

def main_menu(Controller, choice: int=None, user_id: int=None, username: str=None) ->int|None:
    
    if not choice:
        print(Fore.CYAN + Style.BRIGHT + "\n  Main Menu")
        print(Fore.CYAN + "="*100)
        print(Fore.LIGHTCYAN_EX + Style.BRIGHT + '''
        1. Search Movie
        2. Get Recommendation
        3. Watchlist
        4. Add Rating
        5. History
        6. Submit Movie Requests
        7. Submit Wrong Info Requests
        8. Submit History
        9. Modify your Submits
        10. Exit
        ''')
    
    if choice is None or user_id is None: return None
    if username is None: username = "User ID: " + user_id
    if choice == 1: 
        movie_list = search_movie(Controller)
        add_to_watchlist_helper(Controller, user_id=user_id, movie_data=movie_list)
    elif choice == 2: get_recommendation(Controller, user_id=user_id)
    elif choice == 3: user_watchlist(Controller, user_id=user_id)
    elif choice == 4: add_rating(Controller, user_id=user_id)
    elif choice == 5: get_user_history(Controller, user_id=user_id)
    elif choice == 6: request_new_movie(Controller, user_id=user_id)
    elif choice == 7: report_wrong_info(Controller, user_id=user_id)
    elif choice == 8: show_submitted(Controller, user_id=user_id, username=username)
    elif choice == 9: modify_submitted(Controller, user_id=user_id)
    elif choice == 10: return 10
    else: return None


def handle_add_user(Controller) ->dict|None:
    while True:    
        username = input(Fore.YELLOW + Style.BRIGHT + "\nEnter your username: ").strip()
        while not username:
            print(Fore.RED + Style.BRIGHT + "\nPlease enter a valid username\n")
            username = input(Fore.YELLOW + Style.BRIGHT + "Enter your username: ").strip()
        user_dict = Controller.get_user(username=username)
        if not user_dict:
            ask = input(Fore.MAGENTA + Style.BRIGHT + "No username found!! Register(y/n)?: ").strip().lower()
            if ask not in ("yes", "y", ""): return None
            while True:
                age = input(Fore.YELLOW + Style.BRIGHT + "\nEnter your age: ")
                if not age.isdigit():
                    print(Fore.RED + Style.BRIGHT + "Enter a valid age!!")
                    continue
                age = int(age)
                if age < 1 or age > 100:
                    print(Fore.RED + Style.BRIGHT + "Enter a valid age!!")
                    continue
                break

            user_dict = Controller.add_user(username=username, age=age)
            if user_dict.get("user_id", None): print(Fore.GREEN + Style.BRIGHT+ "\nNew user registered...")
        else:
            ask = input(Fore.MAGENTA + Style.BRIGHT + "\nExisting username found!! Login (y/n)?:").strip().lower()
            if ask not in ("yes", "y", ""):
                print(Fore.MAGENTA + Style.BRIGHT + "\nSkipped Login...\n")
                continue
        print(Fore.GREEN + Style.BRIGHT + f"\nLogged in as '{user_dict.get("username", None)}'!!\n")
        print(Fore.CYAN + "="*100)
        return user_dict

def get_user_history(Controller, user_id: int=None, for_func: bool=False, only_na: bool=False) -> None|list:
    if not user_id:
        print(Fore.RED + Style.BRIGHT + "\nNo user id entered...\n")
        return
    
    # Get user history from controller
    history_data = Controller.get_user_history(user_id=user_id)
    
    if not history_data:
        print(Fore.YELLOW + Style.BRIGHT + "\nNo viewing history found for this user id...\n")
        return
    
    # Convert to DataFrame and clean data
    history_df = pd.DataFrame(history_data)
    
    # Exclude rows where rating is NaN if it is not used by a function
    if not for_func and not only_na: history_df = history_df.dropna(subset=['rating'])
    
    #if only na values are needed
    if only_na: history_df = history_df[history_df["rating"].isna() & history_df["would_recommend"].isna()]
    
    if history_df.empty and not only_na:
        print(Fore.YELLOW + Style.BRIGHT + "\nNo rated movies found in your history...\n")
        return
    elif history_df.empty and only_na:
        print(Fore.YELLOW + Style.BRIGHT + "\nNo movies found in your watchlist...\n")
        return
    
    # Get all movie IDs from history
    movie_ids = history_df['movie_id'].tolist()
    
    # Get movie details using search_movie with list of movie IDs
    movie_details_list = Controller.search_movie(Controller, movie_id=movie_ids)
    
    # Create a mapping of movie_id to movie details
    movie_map = {}
    if movie_details_list:
        for movie in movie_details_list:
            movie_map[movie['movie_id']] = movie
    
    # Build display data in the same order as history data
    display_data = []
    for movie in history_df.itertuples():
        movie_info = movie_map.get(movie.movie_id, {})
        display_data.append({
            'movie_id': movie.movie_id,
            'title': movie_info.get('title', f"Movie ID: {movie.movie_id}"),
            'genre': movie_info.get('genre', 'Unknown'),
            'year': movie_info.get('year', 'Unknown'),
            'user_rating': movie.rating,
            'would_recommend': movie.would_recommend,
        })
    
    # Create display DataFrame
    display_df = pd.DataFrame(display_data)
    
    if for_func: 
        return display_df["movie_id"].tolist(), display_df["title"].tolist(), display_df["genre"].tolist() #this is if this function is used for another function

    if not only_na:
        print(Fore.CYAN + Style.BRIGHT + "History")
    else:
        print(Fore.CYAN + Style.BRIGHT + "Watchlist")

    print(Fore.CYAN + "="*100)

    # Show total available history
    total_entries = len(display_df)
    print(Fore.GREEN + Style.BRIGHT + f"\n📊 You have {total_entries} rated movies in your history")
    
    # Ask how many to display
    while True:
        try:
            display_count_input = input(Fore.YELLOW + Style.BRIGHT +  f"How many recent movies would you like to see? (1-{total_entries}, or 'all'): ").strip().lower()
            
            if display_count_input == 'all':
                display_count = total_entries
                break
            elif display_count_input.isdigit():
                display_count = int(display_count_input)
                if 1 <= display_count <= total_entries:
                    break
                else:
                    print(Fore.RED + Style.BRIGHT + f"Please enter a number between 1 and {total_entries}!")
            else:
                print(Fore.RED + Style.BRIGHT + "Please enter a valid number or 'all'!")
        except ValueError:
            print(Fore.RED + Style.BRIGHT + "Invalid input! Please try again.")
    
    # Since history data is reversed, take the tail to get most recent entries
    recent_data = display_df.tail(display_count)
    display_df = display_df.tail(display_count) #filtering the rows for helper function
    
    # Display the history (showing oldest to newest from top to bottom)
    print(Fore.CYAN + Style.BRIGHT + f"\n🎬 Your Recent Movie History (showing {len(recent_data)} of {total_entries}):")
    print(Fore.CYAN + "="*150)
    
    for idx, (_, movie) in enumerate(recent_data.iterrows()):
        title_display = f"{Fore.CYAN}{movie['title']}{Style.RESET_ALL}".ljust(30)
        genre_display = f"  {Fore.LIGHTRED_EX}Genre: {Style.RESET_ALL}{Fore.LIGHTWHITE_EX}{movie['genre']}{Style.RESET_ALL}".ljust(50)
        year_display = f"{Fore.LIGHTRED_EX}Year: {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}{movie['year']}{Style.RESET_ALL}".ljust(40)
        rating_display = f"{Fore.LIGHTRED_EX}Your Rating: {Style.RESET_ALL}{Fore.YELLOW}{movie['user_rating'] if not pd.isna(movie["user_rating"]) else ""}/10{Style.RESET_ALL}".ljust(55)
        
        # Handle would_recommend NaN values - show "Empty"
        if pd.isna(movie['would_recommend']):
            recommend_display = f"{Fore.LIGHTRED_EX}Recommend: ".ljust(60)
        else:
            recommend_display = f"{Fore.LIGHTRED_EX}Recommend: {Style.RESET_ALL}{Fore.GREEN if movie['would_recommend'] else Fore.RED}{'Yes' if movie['would_recommend'] else 'No'}{Style.RESET_ALL}".ljust(60)
        
        print(f"{idx + 1}. {title_display} {genre_display} {year_display} {rating_display} {recommend_display}")
        print(Fore.LIGHTWHITE_EX + "-"*150)
    
    print(Fore.GREEN + Style.BRIGHT + f"\n✨ Showing most recent {len(recent_data)} movies (oldest to newest from top to bottom)")

    update_rating_helper(user_id=user_id, display_df=display_df)

def user_watchlist(Controller, user_id:str=None) ->None:
    get_user_history(Controller, user_id=user_id, only_na=True)

def update_rating_helper(Controller, user_id: str, display_df: pd.DataFrame) -> None:
    """Helper function to update existing ratings in user history"""
    
    print(Fore.CYAN + Style.BRIGHT + "\n🔄 Update Rating")
    print(Fore.CYAN + "="*100)
    
    # Ask if user wants to update any rating
    update_choice = input(Fore.YELLOW + Style.BRIGHT + "Do you want to update any details from the following? (y/n): ").strip().lower()
    if update_choice not in ("yes", "y", ""):
        return
    
    # Get user info for user_id
    user_info = Controller.get_user(user_id=user_id)
    if not user_info:
        print(Fore.RED + Style.BRIGHT + "User not found!")
        return
    
    user_id = user_info.get("user_id")
    
    # Let user select which rating to update
    while True:
        try:
            if len(display_df) > 1: choice_input = input(Fore.YELLOW + Style.BRIGHT + f"\nEnter the movie number you want to update (1-{len(display_df)}): ").strip()
            else: choice_input = "1"
            if choice_input.isdigit():
                choice = int(choice_input) - 1
                if 0 <= choice < len(display_df):
                    selected_movie = display_df.iloc[choice]
                    break
                else:
                    print(Fore.RED + Style.BRIGHT + f"Please enter a number between 1 and {len(display_df)}!")
            else:
                print(Fore.RED + Style.BRIGHT + "Please enter a valid number!")
        except ValueError:
            print(Fore.RED + Style.BRIGHT + "Invalid input! Please try again.")
    
    print(Fore.CYAN + Style.BRIGHT + f"\n🎬 Updating rating for: {Fore.CYAN}{selected_movie['title']}{Style.RESET_ALL}")
    print(Fore.CYAN + "="*100)
    
    # Get new rating
    while True:
        try:
            rating_input = input(Fore.YELLOW + Style.BRIGHT + f"Enter new rating (0-10) [Current: {selected_movie['user_rating'] if not pd.isna(selected_movie['user_rating']) else "Empty"}/10] or press Enter to keep current: ").strip()
            if not rating_input:  # User pressed Enter to keep current
                if not pd.isna(selected_movie['user_rating']):
                    new_rating = selected_movie['user_rating']
                    break
                else:
                    print(Fore.RED + Style.BRIGHT + "Rating cannot be empty!!")
                    continue
            if not rating_input.replace('.', '').isdigit():
                print(Fore.RED + Style.BRIGHT + "Please enter a valid number!")
                continue
            new_rating = round(float(rating_input), 1)
            if new_rating < 0 or new_rating > 10:
                print(Fore.RED + Style.BRIGHT + "Rating should be between 0 to 10!")
                continue
            break
        except ValueError:
            print(Fore.RED + Style.BRIGHT + "Invalid input! Please try again.")
    
    # Get new would_recommend
    current_recommend = selected_movie['would_recommend']
    current_recommend_text = ("Yes" if current_recommend else "No") if not pd.isna(current_recommend) else "Empty"
    
    recommend_input = input(Fore.YELLOW + Style.BRIGHT + f"Would you recommend this movie? (y/n) [Current: {current_recommend_text}] or press Enter to keep current: ").strip().lower()
    
    if recommend_input in ("yes", "y"):
        new_would_recommend = True
    elif recommend_input in ("no", "n"):
        new_would_recommend = False
    elif not recommend_input:  # User pressed Enter
        new_would_recommend = current_recommend
    else:
        new_would_recommend = current_recommend  # Keep current for invalid input
    
    # Show changes summary
    print(Fore.CYAN + Style.BRIGHT + "\n📝 Changes Summary:")
    print(f"Movie: {Fore.CYAN}{selected_movie['title']}{Style.RESET_ALL}")
    print(f"Rating: {Fore.YELLOW}{selected_movie['user_rating'] if not pd.isna(selected_movie["user_rating"]) else ""}/10 {Style.RESET_ALL}→ {Fore.GREEN}{new_rating}/10{Style.RESET_ALL}")
    
    old_recommend_text = "Yes" if current_recommend else "No" if not pd.isna(current_recommend) else "Empty"
    new_recommend_text = "Yes" if new_would_recommend else "No" if not pd.isna(new_would_recommend) else "Empty"
    print(f"Recommend: {Fore.YELLOW}{old_recommend_text}{Style.RESET_ALL} → {Fore.GREEN}{new_recommend_text}{Style.RESET_ALL}")
    
    # Confirm update
    confirm = input(Fore.RED + Style.BRIGHT + "\nConfirm update? (y/n): ").strip().lower()
    if confirm not in ("yes", "y", ""):
        print(Fore.YELLOW + Style.BRIGHT + "Update cancelled...")
        return
    
    # Call controller to update rating using update_data method
    Controller.update_data(
        user_id=user_id,
        movie_id=selected_movie['movie_id'],
        rating=new_rating,
        would_recommend=new_would_recommend
    )
    
    print(Fore.GREEN + Style.BRIGHT + "\n✅ Rating updated successfully!")

def request_new_movie(Controller, user_id: str) ->None:
    if not user_id:
        print(Fore.RED + Style.BRIGHT + "\nNo user id entered...\n")
        return None
    
    print(Fore.CYAN + Style.BRIGHT + '''
    Welcome to Request new movie menu. Here you can submit a request to add a new movie. 
    Our Reviewer will review your request and you can find the status your requests in the 'Submit History' tab.
    You can modify your submit requests after the submit from the 'Modify your Submits' tab.
    ''')

    ask = input(Fore.YELLOW + Style.BRIGHT + "Do you wish to proceed ? (y/n)")
    if ask not in ("yes", "y", ""): return None
    
    title = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\nEnter movie title: ").strip().lower().title()
    while not title: title = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Enter movie title: ").strip().lower().title()

    genre = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Enter the genres separated by commas: ").replace(" ", "").split(",")
    while not genre: genre = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Enter the genre separated by commas: ").replace(" ", "").split(",")
    genre = [g.title() for g in genre]
    genre = ", ".join(genre)

    year = int(int(input(Fore.YELLOW + Style.BRIGHT + "Enter the movie year: ")))
    while not year or (year < 1800 or year > datetime.now().year):
        print(Fore.RED + Style.BRIGHT + "\nMovie year should be between 1800 and current year!!\n")
        year = int(year = int(input(Fore.YELLOW + Style.BRIGHT + "Enter the movie year: ")))

    Controller.submit_movie(title=title, genre=genre, year=year, type="new", submitted_by=user_id)
    print(Fore.GREEN + Style.BRIGHT + "Request Submitted!!")
    return None

def report_wrong_info(Controller, user_id: str) ->None:
    if not user_id:
        print(Fore.RED + Style.BRIGHT + "\nNo user id entered...\n")
        return None
    
    print(Fore.YELLOW + Style.BRIGHT + '''
    Welcome to the Submit Wrong Info Request menu. Here you can submit a request to modify a movie's request.
    Our Reviewer will review your request and you can find the status your requests in the 'Submit History' tab.
    You can modify your submit requests after the submit from the 'Modify your Submits' tab.    
    ''')

    ask = input(Fore.CYAN + Style.BRIGHT + "Do you wish to proceed ? (y/n)")
    if ask not in ("yes", "y", ""): return None    
    
    movie_list = search_movie(Controller)

    ids = int(input(Style.BRIGHT + Fore.YELLOW + "Enter the movie id that you want to modify: ")) - 1
    while ids > len(movie_list):
        print(Fore.RED + Style.BRIGHT + "\nEnter a valid movie id!!\n")
        ids = int(input(Style.BRIGHT + Fore.YELLOW + "Enter the movie id that you want to modify: ")) - 1

    movie = movie_list[ids]

    # Get user inputs with skip options
    title = input(Fore.LIGHTRED_EX + Style.BRIGHT + "Enter new title (or press 'Enter' to keep current): " + Style.RESET_ALL).strip()
    genre = input(Fore.LIGHTRED_EX + Style.BRIGHT + "Enter new genre (or press 'Enter' to keep current): " + Style.RESET_ALL).replace(" ", "")

    # Year input with validation loop
    while True:
        year_input = input(Fore.LIGHTRED_EX + Style.BRIGHT + "Enter new release year (or press 'Enter' to keep current): " + Style.RESET_ALL).strip()
        
        if not year_input:  # User pressed Enter
            year = None
            break
        if year <= 1800 or year >= datetime.now().year:
            print(Fore.RED + Style.BRIGHT + "\nMovie year should be between 1800 and current year!!\n")
            continue
        elif year_input.isdigit() and len(year_input) == 4:  # Valid year
            year = int(year_input)
            break
        else:
            print(Fore.RED + "Please enter a valid 4-digit year or press Enter to skip." + Style.RESET_ALL)
            continue

    # Convert empty strings to None
    title = title if title else None
    genre = genre if genre else None

    # Check if all fields are empty
    if all(x is None for x in [title, genre, year]):
        print(Fore.YELLOW + "No changes submitted - all fields were empty." + Style.RESET_ALL)
        return

    # Fill missing values from current movie data
    if not title: title = movie['title']
    if not genre: genre = movie['genre']
    if not year: year = movie['year']

    # Process genre
    genre = genre.replace("scifi", "sci-fi")

    # Display the updated movie info
    print(Fore.CYAN + Style.BRIGHT + "\nUpdated Movie Details:" + Style.RESET_ALL)
    title_display = f"{Fore.CYAN}{title}{Style.RESET_ALL}"
    genre_display = f"{Fore.MAGENTA}{genre}{Style.RESET_ALL}" 
    year_display = f"{Fore.GREEN}{year}{Style.RESET_ALL}"

    print(f"Title: {title_display} | Genre: {genre_display} | Year: {year_display}")

    confirm = input(Fore.RED + Style.BRIGHT + "Are these infos correct? (y/n)").strip().lower()
    if confirm in ("no", "n"):
        print(Fore.YELLOW + Style.BRIGHT + "Skipped modifying!!...")
        return None
    else:
        print(Fore.GREEN + Style.BRIGHT + "Request Sent!! You can check status from 'Submit History' tab...")

    # Calling the submit function
    Controller.submit_movie(
        movie_id=movie['movie_id'],  # Use original movie ID for edits
        title=title,
        genre=genre, 
        year=year,
        type="edit",
        submitted_by=user_id 
    )    

def show_submitted(Controller, user_id: int= None, username: str=None) -> None:
    if not user_id:
        print(Fore.RED + Style.BRIGHT + "\nNo user_id found...\n")
        return
    
    # Get submitted movies for this user
    submitted_data = Controller.show_submitted(submitted_by=user_id)
    
    if not submitted_data:
        print(Fore.YELLOW + Style.BRIGHT + f"\nNo submitted movies found for '{username}'...\n")
        return
    
    # Convert to DataFrame
    submitted_df = pd.DataFrame(submitted_data)
    
    # Show total submissions
    total_submissions = len(submitted_df)
    print(Fore.CYAN + Style.BRIGHT + "Submitted Movies History")
    print(Fore.CYAN + "="*100)
    print(Fore.GREEN + Style.BRIGHT + f"\n📊 You have {total_submissions} submitted movie requests")
    
    # Ask how many to display
    while True:
        try:
            if total_submissions != 1: 
                display_count_input = input(Fore.YELLOW + Style.BRIGHT +  f"How many recent submissions would you like to see? (1-{total_submissions}, or 'all'): ").strip().lower()
            
                if display_count_input == 'all':
                    display_count = total_submissions
                    break
                elif display_count_input.isdigit():
                    display_count = int(display_count_input)
                    if 1 <= display_count <= total_submissions:
                        break
                    else:
                        print(Fore.RED + Style.BRIGHT + f"Please enter a number between 1 and {total_submissions}!")
                else:
                    print(Fore.RED + Style.BRIGHT + "Please enter a valid number or 'all'!")
            else: display_count_input = 1
        except ValueError:
            print(Fore.RED + Style.BRIGHT + "Invalid input! Please try again.")
    
    # Get the most recent submissions (tail of the data)
    recent_data = submitted_df.tail(display_count)
    
    # Display the submissions
    print(Fore.CYAN + Style.BRIGHT + f"\n📝 Your Recent Submissions (showing {len(recent_data)} of {total_submissions}):")
    print(Fore.CYAN + "="*150)
    
    for idx, (_, submission) in enumerate(recent_data.iterrows()):
        title_display = f"{Fore.CYAN}{submission['title']}{Style.RESET_ALL}".ljust(30)
        genre_display = f"{Fore.LIGHTRED_EX}Genre: {Style.RESET_ALL}{Fore.LIGHTWHITE_EX}{submission.get('genre', 'N/A')}{Style.RESET_ALL}".ljust(50)
        year_display = f"{Fore.LIGHTRED_EX}Year: {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}{submission.get('year', 'N/A')}{Style.RESET_ALL}".ljust(60)
        
        # Submission type and status
        type_display = f"{Fore.LIGHTRED_EX}Type: {Style.RESET_ALL}{Fore.MAGENTA if submission['type'] == 'new' else Fore.CYAN}{submission['type'].title()}{Style.RESET_ALL}".ljust(50)
        status_display = f"{Fore.LIGHTRED_EX}Status: {Style.RESET_ALL}{Fore.YELLOW if submission['status'] == 'pending' else Fore.GREEN if submission['status'] == 'approved' else Fore.RED}{submission['status'].title()}{Style.RESET_ALL}".ljust(50)
        
        print(f"{idx + 1}. {title_display} {genre_display} {year_display} {status_display} {type_display}")
        print(Fore.LIGHTWHITE_EX + "-"*150)
    
    print(Fore.GREEN + Style.BRIGHT + f"\n✨ Showing most recent {len(recent_data)} submissions (oldest to newest from top to bottom)")

def modify_submitted(Controller, user_id: int = None) -> None:
    if not user_id:
        print(Fore.RED + Style.BRIGHT + "\nNo user ID provided...\n")
        return
    
    print(Fore.CYAN + Style.BRIGHT + "Modify Submitted Requests")
    print(Fore.CYAN + "="*100)
    
    # Get user's pending submissions
    submitted_data = Controller.show_submitted(
        submitted_by=user_id, 
        status="pending"
    )
    
    if not submitted_data:
        print(Fore.YELLOW + Style.BRIGHT + f"\nNo pending submissions found...\n")
        return
    
    # Convert to DataFrame
    submitted_df = pd.DataFrame(submitted_data)
    
    # Show pending submissions
    print(Fore.CYAN + Style.BRIGHT + "\n📋 Your Pending Submissions:")
    print(Fore.CYAN + "-"*150)
    
    for idx, (_, submission) in enumerate(submitted_df.iterrows()):
        title_display = f"{Fore.CYAN}{submission['title']}{Style.RESET_ALL}".ljust(30)
        genre_display = f"{Fore.LIGHTRED_EX}Genre: {Style.RESET_ALL}{Fore.LIGHTWHITE_EX}{submission.get('genre', 'N/A')}{Style.RESET_ALL}".ljust(60)
        year_display = f"{Fore.LIGHTRED_EX}Year: {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}{submission.get('year', 'N/A')}{Style.RESET_ALL}".ljust(60)
        type_display = f"{Fore.LIGHTRED_EX}Type: {Style.RESET_ALL}{Fore.MAGENTA if submission['type'] == 'new' else Fore.CYAN}{submission['type'].title()}{Style.RESET_ALL}".ljust(60)
        
        print(f"{idx + 1}. {title_display} {genre_display} {year_display} {type_display}")
        print(Fore.LIGHTWHITE_EX + "-"*150)
    
    # If only 1 submission, auto-select it
    if len(submitted_df) == 1:
        choice_input = "1"
    else:
        # Let user select which submission to modify
        while True:
            try:
                choice_input = input(Fore.YELLOW + Style.BRIGHT + f"\nEnter the submission number you want to modify (1-{len(submitted_df)}): ").strip()
                if choice_input.isdigit():
                    choice = int(choice_input) - 1
                    if 0 <= choice < len(submitted_df):
                        break
                    else:
                        print(Fore.RED + Style.BRIGHT + f"Please enter a number between 1 and {len(submitted_df)}!")
                else:
                    print(Fore.RED + Style.BRIGHT + "Please enter a valid number!")
            except ValueError:
                print(Fore.RED + Style.BRIGHT + "Invalid input! Please try again.")
    
    choice = int(choice_input) - 1
    selected_submission = submitted_df.iloc[choice].to_dict()
    
    print(Fore.CYAN + Style.BRIGHT + f"\n🎬 Modifying: {Fore.CYAN}{selected_submission['title']}{Style.RESET_ALL}")
    print(Fore.CYAN + "="*100)
    
    # Show modification options
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "\nModification Options (choose multiple with commas):")
    print("1. Update Title")
    print("2. Update Genre")
    print("3. Update Year")
    print("4. Delete Request")
    print("5. Cancel")
    
    # Get user's choice(s)
    while True:
        choices_input = input(Fore.YELLOW + Style.BRIGHT + "\nEnter your choice(s) (e.g., '1,2,3' or '4'): ").strip()
        
        if not choices_input:
            print(Fore.RED + Style.BRIGHT + "Please enter at least one choice!")
            continue
        
        if choices_input == '5':
            print(Fore.YELLOW + Style.BRIGHT + "Modification cancelled...")
            return
        
        # Parse choices
        choices = []
        valid = True
        for choice_str in choices_input.split(','):
            choice_str = choice_str.strip()
            if choice_str.isdigit() and 1 <= int(choice_str) <= 4:
                choices.append(int(choice_str))
            else:
                print(Fore.RED + Style.BRIGHT + f"Invalid choice '{choice_str}'. Please enter numbers 1-4 separated by commas.")
                valid = False
                break
        
        if valid and choices:
            break
    
    # Check if delete is selected with other options
    if 4 in choices and len(choices) > 1:
        print(Fore.YELLOW + Style.BRIGHT + "\n⚠️  Delete selected with other options. Only delete will be performed.")
        choices = [4]  # Only keep delete
    
    # Process each choice
    updated_submission = selected_submission.copy()
    changes_made = {}
    
    for choice in choices:
        if choice == 1:  # Update Title
            current_title = selected_submission.get('title', '')
            new_title = input(Fore.YELLOW + Style.BRIGHT + f"Enter new title [Current: {current_title}]: ").strip()
            if new_title and new_title != current_title:
                updated_submission['title'] = new_title
                changes_made['title'] = (current_title, new_title)
                print(Fore.GREEN + f"✓ Title updated")
        
        elif choice == 2:  # Update Genre
            current_genre = selected_submission.get('genre', '')
            new_genre = input(Fore.YELLOW + Style.BRIGHT + f"Enter new genre(s) [Current: {current_genre}]: ").strip()
            if new_genre and new_genre != current_genre:
                updated_submission['genre'] = new_genre
                changes_made['genre'] = (current_genre, new_genre)
                print(Fore.GREEN + f"✓ Genre updated")
        
        elif choice == 3:  # Update Year
            current_year = selected_submission.get('year', '')
            while True:
                new_year_input = input(Fore.YELLOW + Style.BRIGHT + f"Enter new year [Current: {current_year}]: ").strip()
                if not new_year_input:
                    print(Fore.YELLOW + "Year update skipped.")
                    break
                
                if new_year_input.isdigit():
                    new_year = int(new_year_input)
                    if new_year == current_year:
                        print(Fore.YELLOW + "Year unchanged.")
                        break
                    
                    if 1800 <= new_year <= datetime.now().year:
                        updated_submission['year'] = new_year
                        changes_made['year'] = (current_year, new_year)
                        print(Fore.GREEN + f"✓ Year updated")
                        break
                    else:
                        print(Fore.RED + f"Year must be between 1800 and {datetime.now().year}")
                else:
                    print(Fore.RED + "Please enter a valid year!")
        
        elif choice == 4:  # Delete Request
            confirm = input(Fore.RED + Style.BRIGHT + "\n⚠️  Are you sure you want to DELETE this request? (y/n): ").strip().lower()
            if confirm in ("yes", "y", ""):
                updated_submission['status'] = 'deleted'
                changes_made['status'] = ('pending', 'deleted')
                print(Fore.GREEN + "✓ Request marked for deletion")
            else:
                print(Fore.YELLOW + "Delete cancelled.")
    
    # Check if anything was actually changed
    if not changes_made:
        print(Fore.YELLOW + Style.BRIGHT + "\nNo changes made. Submission unchanged.")
        return
    
    # Show summary of changes with old -> new format
    print(Fore.CYAN + Style.BRIGHT + "\n📝 Changes Summary:")
    print(Fore.CYAN + "-"*100)
    
    for key, (old_val, new_val) in changes_made.items():
        print(f"{key.title()}: {Fore.YELLOW}{old_val}{Style.RESET_ALL} → {Fore.GREEN}{new_val}{Style.RESET_ALL}")
    
    # Confirm update
    confirm = input(Fore.RED + Style.BRIGHT + "\nConfirm these changes? (y/n): ").strip().lower()
    if confirm not in ("yes", "y", ""):
        print(Fore.YELLOW + Style.BRIGHT + "Changes discarded...")
        return
    
    # Call controller to update submission
    rejected_rows = Controller.update_submitted(
        update_dict=[updated_submission],
        status="pending"
    )
    
    # Process the result
    process_update_result(rejected_rows, updated_submission)

def process_update_result(rejected_rows, updated_submission):
    """Helper function to process update results"""
    if rejected_rows is None:
        # None means all successful
        show_success_message(updated_submission)
    elif isinstance(rejected_rows, list):
        if len(rejected_rows) > 0:
            # Show rejected rows
            display_rejected_rows(rejected_rows, updated_submission)
        else:
            # Empty list means all successful
            show_success_message(updated_submission)
    else:
        print(Fore.RED + Style.BRIGHT + "\n❌ Failed to update submission. Invalid response.")

def display_rejected_rows(rejected_rows, updated_submission):
    """Display rejected rows in proper format"""
    our_submission_id = updated_submission.get('id')
    our_submission_rejected = False
    
    print(Fore.YELLOW + Style.BRIGHT + f"\n⚠️  The following submissions could not be updated:")
    print(Fore.YELLOW + "="*200)
    
    for rejected in rejected_rows:
        # Check if this is our submission
        if rejected.get('id') == our_submission_id:
            our_submission_rejected = True
        
        # Display the rejected row
        display_rejected_row(rejected)
    
    # Determine outcome
    if not our_submission_rejected:
        print(Fore.GREEN + Style.BRIGHT + "\n✅ Your submit request was modified successfully!")
    else:
        print(Fore.RED + Style.BRIGHT + "\n❌ Your submission could not be updated.")

def display_rejected_row(rejected):
    """Display a single rejected row"""
    title = rejected.get('title', 'Unknown')
    genre = rejected.get('genre', 'N/A')
    year = rejected.get('year', 'N/A')
    status = rejected.get('status', 'N/A')
    
    title_display = f"{Fore.CYAN}{title}{Style.RESET_ALL}".ljust(30)
    genre_display = f"{Fore.LIGHTRED_EX}Genre: {Style.RESET_ALL}{Fore.LIGHTWHITE_EX}{genre}{Style.RESET_ALL}".ljust(60)
    year_display = f"{Fore.LIGHTRED_EX}Year: {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}{year}{Style.RESET_ALL}".ljust(60)
    status_display = f"{Fore.LIGHTRED_EX}Status: {Style.RESET_ALL}{Fore.RED if status == 'rejected' else Fore.YELLOW}{status.title()}{Style.RESET_ALL}".ljust(60)
    
    print(f"  • {title_display} {genre_display} {year_display} {status_display}")
    
    # If status is rejected, show reason
    if status == 'rejected' and 'reason' in rejected and rejected['reason']:
        reason = rejected['reason']
        print(f"    {Fore.LIGHTRED_EX}Reason: {Style.RESET_ALL}{Fore.YELLOW}{reason}{Style.RESET_ALL}")
    
    print(Fore.LIGHTWHITE_EX + "-"*200)

def show_success_message(updated_submission):
    """Show success message based on update type"""
    if updated_submission.get('status') == 'deleted':
        print(Fore.GREEN + Style.BRIGHT + "\n✅ Your request was deleted successfully!")
    else:
        print(Fore.GREEN + Style.BRIGHT + "\n✅ Your submission was updated successfully!")

def search_movie(Controller) ->dict|None:
    
    title = input(Fore.YELLOW + Style.BRIGHT + "Enter the movie title to search matching results (or press 'Enter' to skip to the next filter): ").strip().lower()
    if not title: title = None
    genre = input(Fore.YELLOW + Style.BRIGHT + "Enter the genres seperated by commas (or press 'Enter' to skip to the next filter): ")
    if not genre: genre = None
    elif genre: genre = genre.replace(" ", "").replace("scifi", "sci-fi").split(",")
    while True:
        rating = input(Fore.YELLOW + Style.BRIGHT + "Enter the minimum rating (or press 'Enter' to skip to the next filter): ")
        if not rating: 
            rating = None
            break
        if not rating.replace('.', '').isdigit():
            print(Fore.RED + Style.BRIGHT + "Please enter a valid number!!")
            continue
        rating = round(float(rating),1)
        if rating < 0 or rating > 10: 
            print(Fore.RED + Style.BRIGHT + "Rating should be between 0 to 10!!")
            continue
        break
    while True:
        year = input(Fore.YELLOW + Style.BRIGHT + "Enter the movie year (or press 'Enter' to skip): ")
        if not year: 
            if not year: year = None
            break
        if not year.isdigit():
            print(Fore.RED + Style.BRIGHT + "Please enter a valid number!!")
            continue
        year = int(year)
        while year <= 1800 or year >= datetime.now().year:
            print(Fore.RED + Style.BRIGHT + "\nMovie year should be between 1800 and current year!!\n")
            continue
        break
    
    if all(x == "" for x in (title, year, rating, genre)): 
        print(Fore.RED + Style.BRIGHT + "\nNo filters entered!! Skipping search...\n")
        return None
    
    movie_list = Controller.search_movie(title=title, genre=genre, year=year, rating=rating)
    if not movie_list: print(Fore.RED + Style.BRIGHT + "\nNo movies found...\n") ; return None
    print("\n" + Fore.LIGHTWHITE_EX + "-"*200 )
    for idx, movie in enumerate(movie_list):
        title_display = f"{Fore.CYAN}{movie['title']}{Style.RESET_ALL}".ljust(40)
        rating_display = f"{Fore.LIGHTRED_EX}Rating: {Style.RESET_ALL} {Fore.YELLOW}{movie['rating']}{Style.RESET_ALL}/10".ljust(60) 
        genre_display = f"{Fore.LIGHTRED_EX}Genre: {Style.RESET_ALL} {Fore.LIGHTWHITE_EX}{movie['genre']}{Style.RESET_ALL}".ljust(60)
        year_display = f"{Fore.LIGHTRED_EX}Released Year: {Style.RESET_ALL} {Fore.LIGHTBLUE_EX}{movie['year']}{Style.RESET_ALL}".ljust(60)
        
        print(f"{idx + 1}. {title_display} {rating_display} {genre_display} {year_display}")
        print(Fore.LIGHTWHITE_EX + "-"*200)
    return movie_list

def get_recommendation(Controller, user_id: str=None) -> None:
    
    print(Fore.CYAN + Style.BRIGHT + "Movie Recommendation System")
    print(Fore.CYAN + "="*100)
    
    # Get recommendation type
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + '''
    Choose recommendation type:
    1. Based on your watch history
    2. Based on your ratings
    3. Based on similar movies
    4. Popular movies
    5. New releases
    ''')
    
    while True:
        rec_type = input(Fore.YELLOW + Style.BRIGHT + "Enter your choice (1-5): ").strip()
        if not rec_type:
            print(Fore.RED + Style.BRIGHT + "\nPlease select a recommendation type!\n")
            continue
        if rec_type.isdigit() and 1 <= int(rec_type) <= 5:
            rec_type = int(rec_type)
            break
        else:
            print(Fore.RED + Style.BRIGHT + "\nPlease enter a valid number between 1-5!\n")
    
    # Set year to current year
    current_year = datetime.now().year
    year = current_year if rec_type == 5 else None
    
    # Additional filters for some recommendation types
    title = None
    genre = None
    rating = None
    
    if rec_type == 3:  # Similar movies
        title = input(Fore.YELLOW + Style.BRIGHT + "Enter a movie title to find similar movies (or press 'Enter' to skip): ").strip().lower()
        if not title: title = None
    
    if rec_type in [2, 3, 4]:  # All except new releases and watch history
        genre = input(Fore.YELLOW + Style.BRIGHT + "Enter preferred genres separated by commas (or press 'Enter' to skip): ")
        if not genre: 
            genre = None
        elif genre:
            genre = genre.replace(" ", "").replace("scifi", "sci-fi").split(",")

    if rec_type == 1: ids_exclude, _, genre = get_user_history(Controller, user_id=user_id, for_func=True)
    else: ids_exclude = []
    if rec_type in [1, 2, 3, 4]:  # All except new releases
        while True:
            rating_input = input(Fore.YELLOW + Style.BRIGHT + "Enter minimum rating (0-10) or press 'Enter' to skip: ")
            if not rating_input:
                rating = None
                break
            if not rating_input.replace('.', '').isdigit():
                print(Fore.RED + Style.BRIGHT + "Please enter a valid number!!")
                continue
            rating = round(float(rating_input), 1)
            if rating < 0 or rating > 10:
                print(Fore.RED + Style.BRIGHT + "Rating should be between 0 to 10!!")
                continue
            break
    
    # Get number of recommendations
    while True:
        limit_input = input(Fore.YELLOW + Style.BRIGHT + "How many recommendations would you like? (default: 5): ")
        if not limit_input:
            limit = 5
            break
        if not limit_input.isdigit():
            print(Fore.RED + Style.BRIGHT + "Please enter a valid number!!")
            continue
        limit = int(limit_input)
        if limit <= 0 or limit > 50:
            print(Fore.RED + Style.BRIGHT + "Please enter a number between 1-50!")
            continue
        break
    
    # Get recommendations from controller
    movie_list = Controller.recommend_movies(
        title=title,
        genre=genre,
        year=year,
        rating=rating,
        limit=limit
    )
    
    if not movie_list:
        print(Fore.RED + Style.BRIGHT + f"\nNo {current_year} recommendations found with the given criteria...\n")
        return
    
    movie_list_filtered = []    #creating an empty list and only keeping the unwatched movies in there
    for movie in movie_list:
        if movie["movie_id"] not in ids_exclude: movie_list_filtered.append(movie)
    if not movie_list_filtered: 
        print(Fore.MAGENTA + Style.BRIGHT + "\nNo unwatched movies found after filtering with the given options!!\n")
        return

    # Display recommendations
    print("\n" + Fore.GREEN + Style.BRIGHT + f"🎬 Found {len(movie_list)} Recommendations for {current_year}:")
    print(Fore.LIGHTWHITE_EX + "-"*200)
    
    for idx, movie in enumerate(movie_list_filtered):
        title_display = f"{Fore.CYAN}{movie['title']}{Style.RESET_ALL}".ljust(40)
        rating_display = f"{Fore.LIGHTRED_EX}Rating: {Style.RESET_ALL} {Fore.YELLOW}{movie['rating']}{Style.RESET_ALL}/10".ljust(60) 
        genre_display = f"{Fore.LIGHTRED_EX}Genre: {Style.RESET_ALL} {Fore.LIGHTWHITE_EX}{movie['genre']}{Style.RESET_ALL}".ljust(60)
        year_display = f"{Fore.LIGHTRED_EX}Year: {Style.RESET_ALL} {Fore.LIGHTBLUE_EX}{movie['year']}{Style.RESET_ALL}".ljust(60)
        
        print(f"{idx + 1}. {title_display} {rating_display} {genre_display} {year_display}")
        print(Fore.LIGHTWHITE_EX + "-"*200)

    add_to_watchlist_helper(Controller, user_id=user_id, movie_data=movie_list_filtered)

def add_rating(Controller, user_id: int = None) -> None:
    if not user_id:
        print(Fore.RED + Style.BRIGHT + "\nNo user ID provided...\n")
        return
    
    print(Fore.CYAN + Style.BRIGHT + "Add Rating")
    print(Fore.CYAN + "="*100)
    
    # Ask if user wants to add rating from watchlist
    ask_watchlist = input(Fore.YELLOW + Style.BRIGHT + "Do you want to add rating from your watchlist? (y/n): ").strip().lower()
    
    movie_ids = []
    movie_titles = []
    
    if ask_watchlist in ("yes", "y", ""):
        
        # Get unwatched movies from watchlist
        user_watchlist(Controller, user_id=user_id)
        result = get_user_history(Controller, user_id=user_id, for_func=True, only_na=True)
        if result:
            movie_ids, movie_titles, _ = result
            print(Fore.GREEN + Style.BRIGHT + f"\nFound {len(movie_ids)} unwatched movies in your watchlist")

        return
    else:
        # Let user search for a movie to rate
        print(Fore.CYAN + Style.BRIGHT + "\nLet's find a movie to rate...")
        movie_list = search_movie(Controller)
        if not movie_list:
            return
        movie_titles = [movie['title'] for movie in movie_list]
        movie_ids = [movie['movie_id'] for movie in movie_list]
    
    if not movie_ids:
        print(Fore.RED + Style.BRIGHT + "\nNo movies found to rate...\n")
        return
    
    # # Display movies to choose from
    # print(Fore.CYAN + Style.BRIGHT + "\n🎬 Select a movie to rate:")
    # print(Fore.CYAN + "="*100)
    
    # for idx, (movie_id, title) in enumerate(zip(movie_ids, movie_titles)):
    #     print(f"{idx + 1}. {Fore.CYAN}{title}{Style.RESET_ALL} (ID: {movie_id})")
    
    # Let user select a movie
    while True:
        try:
            if not len(movie_ids) != 1: movie_choice = input(Fore.YELLOW + Style.BRIGHT + f"\nEnter the movie number (1-{len(movie_ids)}): ").strip()
            else: movie_choice = "1"
            if movie_choice.isdigit():
                movie_choice = int(movie_choice) - 1
                if 0 <= movie_choice < len(movie_ids):
                    selected_movie_id = movie_ids[movie_choice]
                    selected_movie_title = movie_titles[movie_choice]
                    break
                else:
                    print(Fore.RED + Style.BRIGHT + f"Please enter a number between 1 and {len(movie_ids)}!")
            else:
                print(Fore.RED + Style.BRIGHT + "Please enter a valid number!")
        except ValueError:
            print(Fore.RED + Style.BRIGHT + "Invalid input! Please try again.")
    
    # Get rating
    while True:
        try:
            rating_input = input(Fore.YELLOW + Style.BRIGHT + f"\nEnter your rating for '{selected_movie_title}' (0-10): ").strip()
            if not rating_input:
                print(Fore.RED + Style.BRIGHT + "Rating is required!")
                continue
            if not rating_input.replace('.', '').isdigit():
                print(Fore.RED + Style.BRIGHT + "Please enter a valid number!")
                continue
            rating = round(float(rating_input), 1)
            if rating < 0 or rating > 10:
                print(Fore.RED + Style.BRIGHT + "Rating should be between 0 to 10!")
                continue
            break
        except ValueError:
            print(Fore.RED + Style.BRIGHT + "Invalid input! Please try again.")
    
    # Get would_recommend (optional)
    would_recommend = np.nan
    recommend_input = input(Fore.YELLOW + Style.BRIGHT + "Would you recommend this movie? (y/n) - Press Enter to skip: ").strip().lower()
    if recommend_input in ("yes", "y"):
        would_recommend = True
    elif recommend_input in ("no", "n"):
        would_recommend = False
    # If user presses Enter or gives invalid input, would_recommend remains None
    
    # Confirm before submitting
    print(Fore.CYAN + Style.BRIGHT + "\n📝 Review your rating:")
    print(f"Movie: {Fore.CYAN}{selected_movie_title}{Style.RESET_ALL}")
    print(f"Rating: {Fore.YELLOW}{rating}/10{Style.RESET_ALL}")
    print(f"Recommend: {Fore.GREEN if would_recommend else Fore.RED if would_recommend is False else Fore.YELLOW}{'Yes' if would_recommend else 'No' if would_recommend is False else 'Not specified'}{Style.RESET_ALL}")
    
    confirm = input(Fore.RED + Style.BRIGHT + "\nConfirm submission? (y/n): ").strip().lower()
    if confirm not in ("yes", "y", ""):
        print(Fore.YELLOW + Style.BRIGHT + "\nRating submission cancelled...")
        return
    
    # Call controller to add rating
    Controller.add_data(
        user_id=user_id,
        movie_id=selected_movie_id,
        rating=rating,
        would_recommend=would_recommend
    )
    
    print(Fore.GREEN + Style.BRIGHT + "\n✅ Rating added successfully!")


def add_to_watchlist_helper(Controller, user_id: int, movie_data: list) -> None:
    """
    Helper function to add multiple movies to watchlist
    
    Args:
        user_id: User ID to add movies for
        movie_data: List of movie dicts in records format
    """
    if not user_id or not movie_data:
        print(Fore.RED + Style.BRIGHT + "\nInvalid input for watchlist addition...\n")
        return
    
    ask = input(Fore.YELLOW + Style.BRIGHT +  f"\n Do you want to add these to your watchlist (y/n)?: ").strip()
    if ask not in ("yes", "y", ""): return None

    # Get user's selection
    while True:
        try:
            selection_input = input(Fore.YELLOW + Style.BRIGHT +  f"\nEnter movie numbers to add to watchlist (e.g., '1,3,5' or '2'): ").strip()
            
            if not selection_input:
                print(Fore.YELLOW + Style.BRIGHT + "No selection made. Cancelling...")
                return
            
            # Parse comma-separated numbers
            selected_indices = []
            valid_selection = True
            
            for num_str in selection_input.split(','):
                num_str = num_str.strip()
                if num_str.isdigit():
                    idx = int(num_str) - 1
                    if 0 <= idx < len(movie_data):
                        selected_indices.append(idx)
                    else:
                        print(Fore.RED + Style.BRIGHT + f"Number {num_str} is out of range (1-{len(movie_data)})!")
                        valid_selection = False
                        break
                else:
                    print(Fore.RED + Style.BRIGHT + f"Invalid input '{num_str}'. Please enter numbers only!")
                    valid_selection = False
                    break
            
            if valid_selection and selected_indices:
                # Remove duplicates while preserving order
                selected_indices = list(dict.fromkeys(selected_indices))
                break
            elif valid_selection and not selected_indices:
                print(Fore.RED + Style.BRIGHT + "Please select at least one movie!")
        
        except ValueError:
            print(Fore.RED + Style.BRIGHT + "Invalid input format. Please try again.")
    
    # Get selected movies
    selected_movies = [movie_data[idx] for idx in selected_indices]
    
    # Show selection summary
    print(Fore.CYAN + Style.BRIGHT + "\n📝 Selected Movies for Watchlist:")
    for idx, movie in enumerate(selected_movies):
        print(f"  {idx + 1}. {Fore.CYAN}{movie['title']}{Style.RESET_ALL}")
    
    # Confirm addition
    confirm = input(Fore.YELLOW + Style.BRIGHT + f"\nAdd {len(selected_movies)} movie(s) to your watchlist? (y/n): ").strip().lower()
    if confirm not in ("yes", "y", ""):
        print(Fore.YELLOW + Style.BRIGHT + "Cancelled...")
        return
    
    for movie in selected_movies:
        Controller.add_data(
            user_id=user_id,
            movie_id=movie['movie_id'],
            rating=np.nan,  # NaN for watchlist
            would_recommend=np.nan  # Also NaN for watchlist
        )

    print(Fore.GREEN + Style.BRIGHT + f"✅ Successfully added movie(s) to your watchlist!")

def starting_the_function():
    from controller.middle_man import Controller
    user_controller = Controller(include_processed=True)

    user_dict = handle_add_user(user_controller)
    if user_dict is None: return None   
    
    Controller = Controller(include_processed=True, user_id=user_dict.get("user_id", None))

    while True:
        main_menu(Controller)

        choice = input(Fore.BLUE + Style.BRIGHT + "Enter you choice (e.g., 1): ").strip()
        if not choice.isdigit(): continue
        choice = int(choice)
        if choice < 1 or choice > 10:
            print(Fore.RED + Style.BRIGHT + "Choice should be between 1-10!!")
            continue
        print()
        if main_menu(Controller, choice=choice, user_id=user_dict.get("user_id", None), username=user_dict.get("username", None)) == 10: break

starting_the_function()
# print(Controller.recommend_movies(title="inter"))
# print(Controller.search_movie(title="joker"))

#fix submit history next and from the modify submit function 
#need to write the dev frontend next time