from rest_framework import serializers
from .models import Book , Quiz
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class Bookserializers(serializers.ModelSerializer):
    class Meta:
        model=Book
        fields=['id','bookname','genres','book']
        
class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'question', 'answer']

class userSerializers(serializers.Serializer):
    username=serializers.CharField(max_length=50)
    email=serializers.EmailField()
    mobile=serializers.CharField(max_length=15)
    password=serializers.CharField(max_length=15)
    
    def validate(self, data):
        if data.get('username') and User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username is taken")

        if data.get('email') and User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email is taken")

        return data
    
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
              
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
class Loginserializers(serializers.Serializer):
    username=serializers.CharField(max_length=50)
    password=serializers.CharField(max_length=15)
    
    
    

    