from django.urls import path
from .views import home_view, ecg_view, eeg_view, sar_view, doppler_view, drones_view, \
    audio_sampling_view  # import from views folder
from .views.home_view import audio_sampling

urlpatterns = [

    #    HOME    #
    path('', home_view.home, name='home'),
    path('ecg/', home_view.ecg, name='ecg'),
    path('eeg/', home_view.eeg, name='eeg'),
    path('sar/', home_view.sar, name='sar'),
    path('doppler/', home_view.doppler, name='doppler'),
    path('drones/', home_view.drones, name='drones'),
    path('audio/', home_view.audio_sampling, name='audio_sampling'),




    #   ECG  #
    path('ecg/upload/', ecg_view.ecg_upload, name='ecg_upload'),


    #   EEG   #
path('eeg/upload/', eeg_view.eeg_upload, name='eeg_upload'),



    #   SAR   #
path('sar/process/', sar_view.process_sar, name='process_sar'),



    #   Doppler   #
path('doppler/simulate/', doppler_view.simulate_doppler, name='doppler_simulate'),


    #   Drones   #

path('drones/analyze/',drones_view.drone_upload,name='drone_upload'),



    #   audio sampling   #

    path('analyze/', audio_sampling_view.analyze_audio, name='analyze_audio'),
    path('resample/', audio_sampling_view.resample_audio, name='resample_audio'),

]