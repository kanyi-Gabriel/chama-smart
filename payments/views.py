import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from contributions.models import Contribution
from .daraja import stk_push


@login_required
def initiate_payment(request, contribution_id):
    """
    Called when a member clicks 'Pay Contribution'.
    Triggers STK Push to their phone.
    """
    try:
        contribution = Contribution.objects.get(id=contribution_id, member=request.user)
    except Contribution.DoesNotExist:
        return JsonResponse({'error': 'Contribution not found'}, status=404)

    # Format phone: 0712345678 → 254712345678
    phone = request.user.phone_number
    if phone.startswith('0'):
        phone = '254' + phone[1:]

    response = stk_push(
        phone_number=phone,
        amount=contribution.amount,
        account_reference=f"CHAMA{contribution.chama.id}",
        description=f"{contribution.chama.name} contribution"
    )

    if response.get('ResponseCode') == '0':
        # Payment prompt sent successfully
        contribution.status = 'pending'
        contribution.save()
        return JsonResponse({'message': 'Payment prompt sent to your phone', 'data': response})
    else:
        return JsonResponse({'error': 'Failed to initiate payment', 'data': response}, status=400)


@csrf_exempt
def mpesa_callback(request):
    """
    Safaricom calls this URL after payment is processed.
    We update the contribution status based on the result.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        result = data.get('Body', {}).get('stkCallback', {})
        result_code = result.get('ResultCode')
        
        # Get the M-Pesa reference from callback metadata
        metadata = result.get('CallbackMetadata', {}).get('Item', [])
        mpesa_ref = None
        amount = None

        for item in metadata:
            if item.get('Name') == 'MpesaReceiptNumber':
                mpesa_ref = item.get('Value')
            if item.get('Name') == 'Amount':
                amount = item.get('Value')

        if result_code == 0:
            # Payment successful
            if mpesa_ref:
                Contribution.objects.filter(
                    status='pending',
                    member__phone_number__endswith=str(result.get('PhoneNumber', ''))[-9:]
                ).order_by('-transaction_date').first()
                
                Contribution.objects.filter(status='pending').order_by('-transaction_date').update(
                    status='completed',
                    mpesa_reference=mpesa_ref
                )

        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})

    return JsonResponse({'error': 'Invalid request'}, status=400)