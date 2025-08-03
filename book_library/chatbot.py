import sqlite3
import os
import re
from collections import defaultdict, Counter

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "answers.txt")
def load_all_answers():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # collect answers into a dictionary with a list of answers per question
    q_dict = defaultdict(list)
    pairs = re.findall(r"Q:\s*(.*?)\s*\nA:\s*(.*?)\s*\n", content, re.DOTALL)
    for q, a in pairs:
        q_dict[q.strip().lower()].append(a.strip())
    return q_dict

def Books(Que,qa_dict):
    if Que.lower() in ["suggestions" , "suggest some books " , " books " , "suggest "]:
        user_Q = input("which types of books you want read : ")
        if user_Q:
            # Path to your media folder (update if different)
            MEDIA_ROOT = os.path.join(os.getcwd(), 'media')  # or set full path manually
            print(user_Q)

            # Connect to DB and fetch rows
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            query = "SELECT id, bookname, genres, book FROM book_library_Book WHERE genres LIKE ?"
            cursor.execute(query, ('%' + user_Q + '%',))
            rows = cursor.fetchall()

            # Display and open each file
            for i, row in enumerate(rows):
                
                print(f"{i}: {row[1]} (Genre: {row[2]})")
                
                print("data fetching")
                print(f"ID: {row[0]}")
                print(f"Book Name: {row[1]}")
                print(f"Genre: {row[2]}")
                print(f"File: {row[3]}")
                print("-" * 40) 
                return {
                  "id": row[0],
                  "bookname": row[1],
                  "genre": row[2],
                  "file": row[3],
                }
                
                
            try:
                    book_number = int(input("\nSelect a book by typing its number: "))
                    if 0 <= book_number < len(rows):
                        selected_row = rows[book_number]
                        selected_file = selected_row[3]  # Assuming this is the file path or name
                        print(f"\nYou selected: {selected_row[1]}")
                        return selected_row ,selected_file
                        print(f"File path: {selected_file}")
                    else:
                        print("Invalid selection.")
            except ValueError:
                    print("Please enter a valid number.")
            
            
            
            conn.close()
        
    else:

            
        Que = Que.strip().lower()
        answers = qa_dict.get(Que)
        if not answers:
            return "🤖 I don’t have an answer for that yet."

        # Option 1: Most frequent answer (if duplicates exist)
        most_common = Counter(answers).most_common(1)[0][0]
        return most_common




from .models import Book
from .serializers import Bookserializers


from collections import Counter
import json
from datetime import datetime

a_data = load_all_answers()
def chat(Que, a_dict):
    # Fetch all books
    
    obj = Book.objects.all()
    books = Bookserializers(obj, many=True)
    book_list = books.data
    print(book_list)
    print(Que)
    if isinstance(Que, dict):
            Que_clean = Que.get("Que", "").strip().lower()
            print("🧼 Cleaned question:", Que_clean)
    elif isinstance(Que, str):
            Que_clean = Que.strip().lower()
            print("🧼 Cleaned question:", Que_clean)
    else:
            Que_clean = ""
            print("⚠️ Invalid question format")

        # 🔹 Handle book suggestion questions directly
    
    if Que_clean in ["suggestions", "suggest some books", "books", "suggest"]:
        
        
        return {
                "response": "📚 Here are some books you might enjoy!",
                "books": book_list
            }
        
    elif Que_clean in ["romance","classic","action","drama","novel","thriller"]:
        obj = Book.objects.filter(genres=Que_clean)
        books = Bookserializers(obj, many=True)
        book_list = books.data
        return book_list
            
    elif Que_clean == "":
        strings="which types of books you want to read","if you want randoms books so just type suggestions"
        return {"welcome to the books suggestions section",strings, }
    
    elif Que_clean not in  ["suggestions", "suggest some books", "books", "suggest","romance","classic","action","drama","novel","thriller"]:
        
        return Books(Que_clean,a_dict)

        
    