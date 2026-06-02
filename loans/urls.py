from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.MyLoansView.as_view(), name='my-loans'),
    path('chama/<int:chama_id>/', views.ChamaLoansView.as_view(), name='chama-loans'),
    path('chama/<int:chama_id>/apply/', views.ApplyForLoanView.as_view(), name='apply-loan'),
    path('<int:loan_id>/review/', views.ReviewLoanView.as_view(), name='review-loan'),
    path('<int:loan_id>/repay/', views.RepayLoanView.as_view(), name='repay-loan'),
]