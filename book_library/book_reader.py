import pyttsx3 
from .serializers import Bookserializers
from .models import Book

def book_reader():
    obj = Book.objects.all()