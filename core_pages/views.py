from django.shortcuts import render

def home(request):
    return render(request, 'core/home.html')

def draw(request):
    return render(request, 'core/draw.html')