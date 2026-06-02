from django.shortcuts import render, redirect


def home(request):
    return render(request, 'core/home.html')


def login_view(request):
    return render(request, 'core/login.html')


def register_view(request):
    return render(request, 'core/register.html')


def dashboard_view(request):
    return render(request, 'core/dashboard.html', {
        'user_data': True,  # triggers sidebar layout
        'active_page': 'dashboard'
    })


def chamas_view(request):
    return render(request, 'core/chamas.html', {
        'user_data': True,
        'active_page': 'chamas'
    })


def chama_detail_view(request, chama_id):
    return render(request, 'core/chama_detail.html', {
        'user_data': True,
        'active_page': 'chamas',
        'chama_id': chama_id
    })


def contributions_view(request):
    return render(request, 'core/contributions.html', {
        'user_data': True,
        'active_page': 'contributions'
    })


def loans_view(request):
    return render(request, 'core/loans.html', {
        'user_data': True,
        'active_page': 'loans'
    })


def analytics_view(request):
    return render(request, 'core/analytics_dashboard.html', {
        'user_data': True,
        'active_page': 'analytics'
    })


def draw(request):
    return render(request, 'core/draw.html')