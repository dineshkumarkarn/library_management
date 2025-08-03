from django.db import models
from django.contrib.auth.models import User

# Create your models here.


from django.contrib.auth.models import AbstractUser


    
    
class Book(models.Model):
    bookname=models.CharField(max_length=100)
    genres=models.CharField(max_length=50)
    book=models.FileField(upload_to='Books/')
    discription=models.TextField()
    
    def __str__(self):
        return self.bookname
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    read_books = models.ManyToManyField(Book, blank=True)
    mobile=models.CharField(max_length=15, blank=True)
    is_premium = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class Quiz(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='quizzes')
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)

    def __str__(self):
        return f"Quiz for {self.book.bookname}"
    
