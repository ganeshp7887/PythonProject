from django.shortcuts import render
from Response_Builder.Instore_response_builder import Transaction_Processing

def Home(request):
    if request.method == 'GET':
        init = request.GET.get("init")
        Transaction_Processing().InitAESDKRequest()
        print(init)
    return render(request, "index.html")
