from django.db import connection
from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt

def check_connection(request):
    with connection.cursor() as cursor:
        cursor.execute("select * from student")
        rows=cursor.fetchall()
        print(rows)
        return HttpResponse(rows[0][1])

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



