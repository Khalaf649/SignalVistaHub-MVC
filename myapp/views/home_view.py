from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
def ecg(request):
    return render(request, 'ecg.html')
def eeg(request):
    return render(request, 'eeg.html')
def sar(request):
    return render(request, 'sar.html')
def doppler(request):
    return render(request, 'doppler.html')
def drones(request):
    return render(request, 'drones.html')
def audio_sampling(request):
    return render(request, 'audio_sampling.html')