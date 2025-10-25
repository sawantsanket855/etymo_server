from django.db import connection
from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view




from etymo.database import *

# def check_connection(request):
#     updatePassword('sawantsanket855@gmail.com','hPCHJFEmnhV03q74VX-HQv-ZL4layV2iTHnK3qWrIuU','Sanket@2146')
#     return JsonResponse({'message':'email already exist'})

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
    message,token=login(data['email'],data['password'],data['loginType'])  #checks login credentials
    return JsonResponse({'message':message,'token':token})
  
    
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
    
@api_view(['POST'])    
def submit_request_api(request):
    print('in function')
    data=request.data
    print(data)
    documents= request.FILES.getlist('documents')
    print(documents)
    name=request.POST.get('name')
    type=request.POST.get('type')
    email=request.POST.get('email')
    mobile=request.POST.get('mobile')
    description=request.POST.get('description')
    token=request.POST.get('token')
    print('calling')
    response= submit_request(name,type,email,mobile,description,documents,token)
    print('called')
    print(response)
    return JsonResponse({'message':response})

@api_view(['POST'])    
def get_request_document_api(request):
    data=request.data
    print(data)
    try:
        print(' get_request_document_api')
        response= get_request_document(data['id'])

        print(f'data having {len(response)} data')
        return JsonResponse({'result':response})
    except Exception as e:
        print('api call error')
        print(e)
    
@api_view(['POST'])    
def get_request_data_api(request):
    data=request.data
    try:
        print('in function get_request_data_api')
        response,message= get_request_data(data['token'])
        response= JsonResponse({'result':response,'message':message})
        return response
    except Exception as e:
        print('api call error')
        print(e)
        return('server error')
        

# @api_view(['POST'])    
# def get_ca_cs_data_api(request):
#     data=request.data
#     try:
#         print('in function get_ca_cs_data_api')
#         response,message= get_ca_cs_data(data['token'])
#         print(f'message{message}')
#         response= JsonResponse({'result':response,'message':message})
#         return response
#     except Exception as e:
#         print('api call error')
#         print(e)
#         return('server error')



@api_view(['POST'])    
def get_request_document_data_api(request):
    data=request.data
    print(data)
    print(f'got id =',data['id'])
    try:
        print('in function get_request_document_data_api')
        response= get_request_document_data(data['id'])
        print(response)
        file_data=response[1]
        if isinstance(file_data, memoryview):
            file_data = bytes(file_data)
            print('converted to bytes')
        response= HttpResponse(file_data,content_type=response[0])
        return response
    except Exception as e:
        print('api call error')
        print(e)


@api_view(['POST'])    
def ca_cs_registartion_api(request):
    print('in function ca_cs_registartion_api')
    data=request.data
    print(data)
    certificate= request.FILES.getlist('certificate')
    IdProof= request.FILES.getlist('IdProof')
    print(certificate)
    print(IdProof)
    response= ca_cs_registartion(data,[certificate[0],IdProof[0]])
    return JsonResponse({'message':response})

@api_view(['POST'])
def update_request_status_api(request):
    try:
        data=request.data
        print(data)
        response= update_request_status(data['requestID'],data['requestStatus'],data['requestInstruction'])
        return JsonResponse({'message':'okkkk'})
    except Exception as e:
        print('error',e)
        return JsonResponse({'message':'server error'})
    

@api_view(['POST'])    
def get_ca_cs_data_api(request):
    data=request.data
    try:
        print(data)
        print('get_ca_cs_data_api')
        response,message= get_ca_cs_data(data['token'])
        print(response,message)
        response= JsonResponse({'result':response,'message':message})
        return response
    except Exception as e:
        print('api call error')
        print(e)



@api_view(['POST'])
def assign_ca_cs_api(request):
    try:
        data=request.data
        print(data)
        response= assign_ca_cs(ca_cs_id=data['ca_cs_id'],requestId=data['request_id'])
        return JsonResponse({'result':'success'})
    except Exception as e:
        print('error',e)
        return JsonResponse({'result':'server error'})


@api_view(['POST'])    
def get_verified_request_data_api(request):
    try:
        print('get_verified_request_data_api')
        response= get_verified_request_data()
        response= JsonResponse({'result':response})
        return response
    except Exception as e:
        print('api call error')
        print(e)

        

@api_view(['POST'])    
def submit_payment_request_api(request):
    print('in submit_payment_request_api')
    data=request.data
    print(data)
    documents= request.FILES.getlist('documents')
    print(documents)
    name=request.POST.get('name')
    amount=request.POST.get('amount')
    paymentMethod=request.POST.get('paymentMethod')
    bankName=request.POST.get('bankName')
    accountNumber=request.POST.get('accountNumber')
    ifscCode=request.POST.get('ifscCode')
    upiId=request.POST.get('upiId')
    token=request.POST.get('token')
    response= submit_payment_request(name,amount,paymentMethod,bankName,accountNumber,ifscCode,upiId,documents,token)
    return JsonResponse({'message':response})



@api_view(['POST'])    
def get_payment_request_data_api(request):
    data =request.data
    try:
        print('in function get_payment_request_data_api')
        response= get_payment_request_data(data['token'])
        response= JsonResponse({'result':response})
        return response
    except Exception as e:
        print('api call error')
        print(e)


@api_view(['POST'])    
def get_payment_request_document_api(request):
    data=request.data
    print(data)
    try:
        print(' get_request_document_api')
        response= get_payment_request_document(data['id'])

        print(f'data having {len(response)} data')
        return JsonResponse({'result':response})
    except Exception as e:
        print('api call error')
        print(e)


@api_view(['POST'])    
def get_payment_request_document_data_api(request):
    data=request.data
    print(data)
    print(f'got id =',data['id'])
    try:
        print('in function get_payment_request_document_data_api')
        response= get_payment_request_document_data(data['id'])
        print(response)
        file_data=response[1]
        if isinstance(file_data, memoryview):
            file_data = bytes(file_data)
            print('converted to bytes')
        response= HttpResponse(file_data,content_type=response[0])
        return response
    except Exception as e:
        print('api call error')
        print(e)


@api_view(['POST'])
def update_payment_request_status_api(request):
    try:
        data=request.data
        print(data)
        response= update_payment_request_status(data['paymentRequestID'],data['requestInstruction'])
        return JsonResponse({'message':response})
    except Exception as e:
        print('error',e)
        return JsonResponse({'message':'server error'})


@api_view(['POST'])    
def get_ca_cs_document_api(request):
    data=request.data
    print(data)
    try:
        print(' get_ca_cs_document_api')
        response= get_ca_cs_document(data['id'])

        print(f'data having {len(response)} data')
        return JsonResponse({'result':response})
    except Exception as e:
        print('api call error')
        print(e)

@api_view(['POST'])    
def get_ca_cs_document_data_api(request):
    data=request.data
    print(data)
    print(f'got id =',data['id'])
    try:
        print('in function get_ca_cs_document_data_api')
        response= get_ca_cs_document_data(data['id'])
        print(response)
        file_data=response[1]
        if isinstance(file_data, memoryview):
            file_data = bytes(file_data)
            print('converted to bytes')
        response= HttpResponse(file_data,content_type=response[0])
        return response
    except Exception as e:
        print('api call error')
        print(e)

@api_view(['POST'])    
def get_agent_balance_api(request):
    data=request.data
    try:
        print('in function get_agent_balance_api')
        response,balance= get_agent_balance(data['token'])
        response= JsonResponse({'result':response,'balance':balance})
        return response
    except Exception as e:
        print('api call error')
        print(e)
        return  JsonResponse({'result':'server error','balance':0})
    

@api_view(['POST'])    
def get_transaction_data_api(request):
    data =request.data
    try:
        print('in function get_transaction_data_api')
        response= get_transaction_data(data['token'])
        response= JsonResponse({'result':response})
        return response
    except Exception as e:
        print('api call error')
        print(e)