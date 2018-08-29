from django.http import HttpResponse

def checkView(request, *args, **kwargs):
    return HttpResponse('OK')
