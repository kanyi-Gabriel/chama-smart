from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import LoanApplication, LoanRepayment
from .serializers import (LoanApplicationSerializer,
                          LoanRepaymentSerializer,
                          LoanApprovalSerializer)
from chamas.models import Membership
from payments.daraja import stk_push


class ApplyForLoanView(APIView):
    """Member applies for a loan from their chama"""
    permission_classes = [IsAuthenticated]

    def post(self, request, chama_id):
        # Verify membership
        try:
            membership = Membership.objects.get(
                user=request.user,
                chama_id=chama_id,
                is_active=True
            )
        except Membership.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this chama'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check no active loan exists
        active_loan = LoanApplication.objects.filter(
            applicant=request.user,
            chama_id=chama_id,
            status__in=['pending', 'approved', 'disbursed']
        ).first()

        if active_loan:
            return Response(
                {'error': f'You already have an active loan in this chama (Status: {active_loan.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LoanApplicationSerializer(data=request.data)
        if serializer.is_valid():
            loan = serializer.save(
                applicant=request.user,
                chama_id=chama_id,
                ml_credit_score=membership.credit_score,
                ml_recommendation='approve' if membership.credit_score >= 60 else 'reject'
            )
            return Response({
                'message': 'Loan application submitted successfully',
                'loan': LoanApplicationSerializer(loan).data,
                'ml_info': {
                    'your_credit_score': membership.credit_score,
                    'recommendation': loan.ml_recommendation,
                    'note': 'Final decision is made by your chama admin'
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyLoansView(generics.ListAPIView):
    """Member sees all their loan applications"""
    permission_classes = [IsAuthenticated]
    serializer_class = LoanApplicationSerializer

    def get_queryset(self):
        return LoanApplication.objects.filter(
            applicant=request.user
        ).order_by('-applied_at')

    def get_queryset(self):
        return LoanApplication.objects.filter(
            applicant=self.request.user
        ).order_by('-applied_at')


class ChamaLoansView(generics.ListAPIView):
    """Admin sees all loan applications for their chama"""
    permission_classes = [IsAuthenticated]
    serializer_class = LoanApplicationSerializer

    def get_queryset(self):
        chama_id = self.kwargs['chama_id']
        return LoanApplication.objects.filter(
            chama_id=chama_id
        ).order_by('-applied_at')


class ReviewLoanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, loan_id):
        try:
            loan = LoanApplication.objects.get(id=loan_id)
        except LoanApplication.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            membership = Membership.objects.get(
                user=request.user,
                chama=loan.chama,
                is_active=True,
                status='active'
            )
        except Membership.DoesNotExist:
            return Response({'error': 'You are not a member of this chama'}, status=status.HTTP_403_FORBIDDEN)

        # Role-based approval limits
        role = membership.role
        action = request.data.get('action')

        if role == 'member':
            return Response({'error': 'Members cannot approve loans'}, status=status.HTTP_403_FORBIDDEN)

        if role == 'secretary':
            return Response({'error': 'Secretary can view but not approve loans. Only chairperson or treasurer can approve.'}, status=status.HTTP_403_FORBIDDEN)

        if loan.status != 'pending':
            return Response({'error': f'This loan has already been {loan.status}'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LoanApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if action == 'approve':
            # Treasurer can only approve up to 3x monthly contribution
            if role == 'treasurer':
                limit = loan.chama.contribution_amount * 3
                amount_requested = loan.amount_requested
                if amount_requested > limit:
                    return Response({
                        'error': f'Treasurer can only approve loans up to KES {limit}. This loan requires Chairperson approval.'
                    }, status=status.HTTP_403_FORBIDDEN)

            amount_approved = serializer.validated_data.get('amount_approved', loan.amount_requested)
            loan.status = 'approved'
            loan.amount_approved = amount_approved
            loan.reviewed_by = request.user
            loan.reviewed_at = timezone.now()
            loan.save()

            return Response({
                'message': f'Loan approved for KES {amount_approved} by {role}',
                'loan': LoanApplicationSerializer(loan).data
            })

        elif action == 'reject':
            loan.status = 'rejected'
            loan.reviewed_by = request.user
            loan.reviewed_at = timezone.now()
            loan.save()
            return Response({
                'message': 'Loan rejected',
                'loan': LoanApplicationSerializer(loan).data
            })


class RepayLoanView(APIView):
    """Member repays their loan via M-Pesa STK push"""
    permission_classes = [IsAuthenticated]

    def post(self, request, loan_id):
        try:
            loan = LoanApplication.objects.get(
                id=loan_id,
                applicant=request.user,
                status__in=['approved', 'disbursed']
            )
        except LoanApplication.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create pending repayment record
        repayment = LoanRepayment.objects.create(
            loan=loan,
            member=request.user,
            amount=amount,
            status='pending'
        )

        # Format phone for Daraja
        phone = request.user.phone_number
        if phone.startswith('0'):
            phone = '254' + phone[1:]

        # Trigger STK Push
        response = stk_push(
            phone_number=phone,
            amount=int(amount),
            account_reference=f'LOAN{loan.id}',
            description=f'Loan repayment - {loan.chama.name}'
        )

        if response.get('ResponseCode') == '0':
            return Response({
                'message': 'Repayment prompt sent to your phone',
                'repayment_id': repayment.id,
                'amount': amount
            })
        else:
            repayment.delete()
            return Response(
                {'error': 'Failed to initiate repayment'},
                status=status.HTTP_400_BAD_REQUEST
            )