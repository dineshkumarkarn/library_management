from .models import Book , Profile
from .serializers import Bookserializers , userSerializers , Loginserializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework import status
from django.contrib.auth import authenticate

from rest_framework_simplejwt.tokens import RefreshToken 

from rest_framework.permissions   import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import permission_classes
from .permissions                    import IsPremiumUser



from rest_framework import viewsets
from rest_framework.decorators import action
from django.http import FileResponse
import PyPDF2
import pyttsx3
import requests
import tempfile

from rest_framework.permissions import AllowAny


from .chatbot import chat , load_all_answers
qa_data = load_all_answers()

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def chatbot(request): 
    # 1. Use JWT for authentication
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.is_premium:
            return Response(
                {'Buy premium first.'},
                
            )
    # 2. Only allow authenticated users
    permission_classes     = [IsAuthenticated]   
    Que=request.data
    response=chat(Que,qa_data)
    return Response(response)

@api_view(['GET', 'POST'])  
@permission_classes([IsAuthenticated])
def index(request):
    
    if request.method=='GET':
        obj = Book.objects.all()
        books = Bookserializers(obj, many=True)
        return Response(books.data)
    
class registration(APIView):
    permission_classes = [AllowAny]
    def post (self, request):
        data= request.data
        print(data)
        serialiser=userSerializers(data=data)
        print(serialiser)
        if not serialiser.is_valid():
            return Response({
                'status':True ,'message':serialiser.errors},status=status.HTTP_400_BAD_REQUEST)
        
        user=serialiser.save()
        
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'status':True, 'message':'user is created', 'token': token.key}, status=status.HTTP_200_OK)
    
class login(APIView):
    def post(self, request):
        data=request.data
        serializer=Loginserializers(data=data)
        if not serializer.is_valid():
            return Response({
                'status': False, 
                'message':serializer.error_messages
               
                },status=status.HTTP_400_BAD_REQUEST
                            )
        user=authenticate(username=serializer.data['username'],password=serializer.data['password'])
        if user is None:
            return Response({  # ✅ ADDED: Handle failed authentication
                'status': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'status': True,
            'message': 'User logged in successfully',
            'token': token.key
        }, status=status.HTTP_200_OK)
            
    

    
class upload_books(APIView):
    def post(self,request):
        data=request.data
        uploud=Bookserializers(data=data)
        if not uploud.is_valid():
            return Response({
                'status': False, 
                'message':uploud.errors       
               
                },status=status.HTTP_400_BAD_REQUEST
                            )
        uploud.save()
        return Response({'status':True, 'message':'book successfully uploaded '}, status=status.HTTP_200_OK)
            
    
class MarkBookAsRead(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, book_id):
        user = request.user

        try:
            profile = user.profile
        except AttributeError:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        profile.read_books.add(book)
        return Response({'message': 'Book marked as read'}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=request.user)
        readed_book = Bookserializers(profile.read_books.all(), many=True).data
        return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "readed_book": readed_book,
        "is_premium":   profile.is_premium,
        
        
    })


class read_book(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = Bookserializers
    http_method_names = ['get']

    @action(detail=True, methods=['get'])
    def read(self, request, pk=None):
        obj  = self.get_object()
        data = Bookserializers(obj).data
        return Response({
            'status': True,
            'message': 'successfully fetched',
            'data': data
        })

    @action(detail=True, methods=['get'])
    def read_audio(self, request, pk=None):
        obj = self.get_object()
        if not obj.book:
            raise Http404("No PDF on this book.")

        # Build full PDF URL
        pdf_url = request.build_absolute_uri(obj.book.url)

        # 1. Download PDF
        try:
            resp = requests.get(pdf_url)
            resp.raise_for_status()
        except Exception:
            return Response({'status': False, 'message': 'Failed to download PDF'}, status=502)

        # 2. Extract text in memory
        pdf_stream = io.BytesIO(resp.content)
        reader     = PyPDF2.PdfReader(pdf_stream)
        text       = "".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            return Response({'status': False, 'message': 'No readable text'}, status=204)

        # 3. Create a closed temp file for pyttsx3 to write into
        tmp_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        tmp_audio_path = tmp_audio.name
        tmp_audio.close()   # ← ensure the handle is released

        # 4. Run TTS
        engine = pyttsx3.init()
        engine.save_to_file(text, tmp_audio_path)
        engine.runAndWait()

        # 5. Stream it back
        return FileResponse(
            open(tmp_audio_path, 'rb'),
            content_type='audio/mpeg',
            filename=f'book_{pk}.mp3'
        )
        
        
        
        
# src/views.py

from django.shortcuts                import get_object_or_404
from rest_framework.views            import APIView
from rest_framework.response         import Response
from rest_framework.permissions      import AllowAny, IsAuthenticated
from rest_framework.generics         import ListAPIView, CreateAPIView, RetrieveAPIView
from rest_framework.parsers          import MultiPartParser, FormParser
from rest_framework                   import status

import nltk
from nltk.tokenize                   import sent_tokenize, word_tokenize
from nltk.tag                        import pos_tag
from nltk.chunk                      import ne_chunk

from .models                         import Book, Quiz, Profile
from .serializers                    import Bookserializers, QuizSerializer
from .permissions                    import IsPremiumUser

# Download NLTK data on startup (only the first time)
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')


# ————— Helpers for Auto-Generating Quizzes —————

def get_book_text(book_file):
    """
    Read and decode an uploaded book file to plain UTF-8 text.
    """
    try:
        return book_file.read().decode('utf-8')
    except Exception:
        return ""


def extract_candidate_questions(text):
    """
    Use NLTK to find sentences containing a proper noun
    and replace that noun with a blank.
    """
    sentences = sent_tokenize(text)
    questions = []

    for sentence in sentences:
        words          = word_tokenize(sentence)
        tagged         = pos_tag(words)
        named_entities = ne_chunk(tagged)

        for i, (word, tag) in enumerate(tagged):
            if tag == 'NNP':  # Proper noun → obvious blank
                q_text = sentence.replace(word, '_____')
                questions.append((q_text, word))
                break

    return questions


def create_quizzes_for_book(book_obj):
    """
    Generate Quiz instances for a Book the first time
    someone requests its quiz list.
    """
    if not book_obj.book:
        return

    raw_text = get_book_text(book_obj.book)
    if not raw_text:
        return

    qna_pairs = extract_candidate_questions(raw_text)
    for question, answer in qna_pairs:
        Quiz.objects.create(book=book_obj, question=question, answer=answer)


# ————— API Views —————

class BookListView(ListAPIView):
    
    queryset           = Book.objects.all()
    serializer_class   = Bookserializers
    permission_classes = [AllowAny]
    def list(self, request, *args, **kwargs):
        # 1) enforce premium
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.is_premium:
            return Response(
                {'Buy premium first.'},
                
            )

        # 2) premium → use DRF’s built-in list logic
        return super().list(request, *args, **kwargs)


class BookCreateView(CreateAPIView):
    
    queryset           = Book.objects.all()
    serializer_class   = Bookserializers
    permission_classes = [IsAuthenticated, IsPremiumUser]
    parser_classes     = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        book_obj = serializer.save(uploader=self.request.user)
        create_quizzes_for_book(book_obj)


class BookQuizView(ListAPIView):
    """
    Premium-only endpoint:
    List (and auto-generate) quizzes for a single Book.
    """
    serializer_class   = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Premium check
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.is_premium:
            return Response(
                {'detail': 'Buy premium first.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Auto-generate quizzes if none exist yet
        book = get_object_or_404(Book, id=kwargs['book_id'])
        if not Quiz.objects.filter(book=book).exists():
            create_quizzes_for_book(book)

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Quiz.objects.filter(book_id=self.kwargs['book_id'])


class AllQuizListView(ListAPIView):
    """
    List all quizzes, but only for premium users.
    """
    queryset            = Quiz.objects.all()
    serializer_class    = QuizSerializer
    permission_classes  = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # 1) enforce premium
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.is_premium:
            return Response(
                {'detail': 'Buy premium first.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2) premium → use DRF’s built-in list logic
        return super().list(request, *args, **kwargs)


class QuizDetailView(RetrieveAPIView):
    """
    Retrieve a single Quiz instance.
    """
    queryset           = Quiz.objects.all()
    serializer_class   = QuizSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg   = 'quiz_id'


class QuizSubmitView(APIView):
    """
    Premium-only: accept a dict of { quiz_id: user_answer, … },
    compute a % score, and return it.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id, *args, **kwargs):
        # Premium check
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.is_premium:
            return Response(
                {'detail': 'Buy premium first.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Process submission
        answers = request.data.get('answers', {})
        total   = len(answers)
        correct = 0

        for qid_str, user_ans in answers.items():
            quiz = get_object_or_404(Quiz, id=int(qid_str))
            if quiz.answer.strip().lower() == str(user_ans).strip().lower():
                correct += 1

        score = (correct / total * 100) if total else 0
        return Response({'score': round(score, 2)})


class UpgradeToPremiumView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        print("profile", profile)
        # profile.is_premium = True
        # profile.save()
        # return Response({"message": "Upgraded to premium!"})

# {
# "username" : "dinesh",
# "email" : "xyz@xyz.com",
# "mobile_number" : "2326532",
# "password" : "1234"
# }