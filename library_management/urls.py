"""
URL configuration for library_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include

from book_library.views import registration , login , UserProfileView ,upload_books , MarkBookAsRead , read_book , BookQuizView , index, chatbot

from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from book_library.views import read_book
from rest_framework.authtoken.views import obtain_auth_token
from book_library.views import (
    BookListView,
    BookCreateView,
    BookQuizView,
    AllQuizListView,
    QuizDetailView,
    QuizSubmitView,
)


router = DefaultRouter()

router.register(r'books', read_book)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',index),
    path('api/index/',index , name="home"), 
    path('api/chat',chatbot),
    path('api/registration/',registration.as_view()),
    path('api/login/',login.as_view()),
    path('api/profile/', UserProfileView.as_view()),
    path('api-token-auth/', obtain_auth_token),  
    path('api/upload/',upload_books.as_view()),
    path('api/mark_read/<int:book_id>/', MarkBookAsRead.as_view()),
    path('api/books/<int:book_id>/quizzes/', BookQuizView.as_view()),
    path('api/', include(router.urls)),
    path('api/books/',                       BookListView.as_view()),

    # Premium: upload a new book (auto-generate quizzes)
    path('api/books/upload/',                BookCreateView.as_view()),

    # Premium: list (and auto-generate) quizzes for one book
    path('api/books/<int:book_id>/quizzes/', BookQuizView.as_view()),

    # Authenticated: list every quiz across all books
    path('api/quizzes/',                     AllQuizListView.as_view()),

    # Authenticated: retrieve a single quiz
    path('api/quizzes/<int:quiz_id>/',       QuizDetailView.as_view()),

    # Authenticated: submit answers and get a score
    path('api/quizzes/<int:quiz_id>/submit/',QuizSubmitView.as_view()),
    
    
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
