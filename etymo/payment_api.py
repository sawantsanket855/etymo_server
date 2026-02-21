
from django.http import HttpResponse,JsonResponse
from rest_framework.decorators import api_view

from etymo.payment_database import razorpay_create_request, razorpay_payment_data

@api_view(['POST'])
def razorpay_create_request_api(request):
    try:
        data =request.data
        response=razorpay_create_request(data['token'],data['amount'])
        if(response[0]=='success'):
            return JsonResponse({'message':response[0],'amount':response[1],'order_id':response[2]})
        else:
            return JsonResponse({'message':response[0]})
    except Exception as e:
        print('api call error')
        print(e)
        return JsonResponse({'message':'internal server error'})
    
@api_view(['POST'])
def razorpay_payment_data_api(request):
    try:
        data =request.data
        result= razorpay_payment_data(payment_id=data['razorpay_payment_id'],order_id=data['razorpay_order_id'],signature=data['razorpay_signature'])
        print(data['razorpay_payment_id'])
        print(data['razorpay_order_id'])
        print(data['razorpay_signature'])
    
        return HttpResponse('payment successful')
    except Exception as e:
        print('api call error')
        print(e)