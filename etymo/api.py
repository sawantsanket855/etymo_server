from django.db import connection
from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view




from etymo.database import login, register, sendOTP, sendPasswordResetEmail, updatePassword, verifyOTP

def check_connection(request):
    updatePassword('sawantsanket855@gmail.com','hPCHJFEmnhV03q74VX-HQv-ZL4layV2iTHnK3qWrIuU','Sanket@2146')
    return JsonResponse({'message':'email already exist'})

@csrf_exempt
def get_word_data(request):
    words_list = request.GET.getlist('highlightedWords')
    print(words_list)
    words=tuple(words_list)
    # words=('aspiration','asthma','bradycardia')
    with connection.cursor() as cursor:
        cursor.execute(f"select * from tbl_medical_terms where medical_term in {words}")
        rows=cursor.fetchall()
        return JsonResponse({'results':rows})
    
   
@api_view(['POST'])
def login_api(request):
    print(request.method)
    data=request.data
    result=login(data['email'],data['password'])  #checks login credentials
    return JsonResponse({'message':result})
  
    
@api_view(['POST'])
def register_api(request):
    data=request.data
    result=register(data['username'],data['email'],data['password'])
    return JsonResponse({'message':result})

@api_view(['POST'])   
def sendOTP_api(request):
    print('sending email')
    data=request.data
    result=sendOTP(data['email'])
    return JsonResponse({'message':result})

@api_view(['POST'])
def verifyOTP_api(request):
    data=request.data
    result=verifyOTP(data['email'],data['otp'])
    return JsonResponse({'message':result})

@api_view(['POST'])
def sendPasswordResetEmail_api(request):
    data=request.data
    result=sendPasswordResetEmail(data['email'])
    return JsonResponse({'message':result})

@api_view(['POST'])    
def updatePassword_api(request):
    data=request.data
    result=updatePassword(data['email'],data['reset_token'],data['password'])
    return JsonResponse({'message':result})
    

    




