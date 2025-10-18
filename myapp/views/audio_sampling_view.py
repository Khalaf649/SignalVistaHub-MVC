from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import numpy as np
from scipy.io import wavfile
from scipy.fft import fft
from scipy import signal
import librosa
import io
import base64
import traceback



@require_http_methods(["POST"])
def analyze_audio(request):
    try:
        if 'audio' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No audio file provided'})

        audio_file = request.FILES['audio']

        # Load audio
        audio_data, sample_rate = librosa.load(audio_file, sr=None)

        # FFT for frequency analysis
        fft_values = np.abs(fft(audio_data))
        freqs = np.fft.fftfreq(len(audio_data), 1 / sample_rate)

        # Positive frequencies
        positive_freqs = freqs[:len(freqs) // 2]
        positive_fft = fft_values[:len(fft_values) // 2]

        # Find significant frequency range
        threshold = np.max(positive_fft) * 0.01
        significant_indices = np.where(positive_fft > threshold)[0]

        if len(significant_indices) > 0:
            fmax = positive_freqs[significant_indices[-1]]
        else:
            fmax = positive_freqs[np.argmax(positive_fft)]

        nyquist_freq = 2 * fmax

        return JsonResponse({
            'success': True,
            'fmax': round(fmax, 2),
            'nyquist_freq': round(nyquist_freq, 2),
            'original_sr': int(sample_rate),
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



@require_http_methods(["POST"])
def resample_audio(request):
    try:
        if 'audio' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No audio file provided'})

        new_sr = int(request.POST.get('sampling_rate', 44100))
        audio_file = request.FILES['audio']

        # Load original audio
        audio_data, original_sr = librosa.load(audio_file, sr=None)

        # Resample
        num_samples = int(len(audio_data) * new_sr / original_sr)
        resampled_audio = signal.resample(audio_data, num_samples)

        # Handle very low sample rates by upsampling for playback
        playback_sr = new_sr
        if new_sr < 8000:
            playback_sr = 44100
            upsampled_audio = signal.resample(resampled_audio, int(len(resampled_audio) * playback_sr / new_sr))
            resampled_audio = upsampled_audio

        # Normalize
        max_val = np.max(np.abs(resampled_audio))
        if max_val > 0:
            resampled_audio = resampled_audio / max_val * 0.85

        resampled_audio = np.clip(resampled_audio, -1.0, 1.0)
        audio_int16 = np.int16(resampled_audio * 32767)

        # Convert to WAV in memory
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, playback_sr, audio_int16)
        wav_buffer.seek(0)

        audio_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')

        # Nyquist check
        fft_values = np.abs(fft(audio_data))
        freqs = np.fft.fftfreq(len(audio_data), 1 / original_sr)
        positive_freqs = freqs[:len(freqs) // 2]
        positive_fft = fft_values[:len(fft_values) // 2]
        fmax = float(positive_freqs[np.argmax(positive_fft)])  # force Python float
        nyquist_freq = float(2 * fmax)
        is_below_nyquist = bool(new_sr < nyquist_freq)  # force Python bool

        return JsonResponse({
            'audio_data': f'data:audio/wav;base64,{audio_base64}',
            'is_below_nyquist': is_below_nyquist,
            'current_sr': int(new_sr),
            'nyquist_freq': round(nyquist_freq, 2),
        
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

   