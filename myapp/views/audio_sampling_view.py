from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import numpy as np
from scipy.io import wavfile
from scipy.fft import fft
from scipy import signal
import librosa
import io
import base64
import traceback
import uuid

# In-memory storage for audio data (key: session_id)
audio_storage = {}




@require_http_methods(["POST"])
def analyze_audio(request):
    try:
        if 'audio' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No audio file provided'})

        audio_file = request.FILES['audio']

        # Load audio file
        audio_data, sample_rate = librosa.load(audio_file, sr=None)

        # Compute FFT to find max frequency
        fft_values = np.abs(fft(audio_data))
        freqs = np.fft.fftfreq(len(audio_data), 1 / sample_rate)

        # Get positive frequencies only
        positive_freqs = freqs[:len(freqs) // 2]
        positive_fft = fft_values[:len(fft_values) // 2]

        # Find highest frequency with at least 1% of peak energy
        threshold = np.max(positive_fft) * 0.01
        significant_indices = np.where(positive_fft > threshold)[0]

        if len(significant_indices) > 0:
            fmax = positive_freqs[significant_indices[-1]]
        else:
            fmax = positive_freqs[np.argmax(positive_fft)]

        # Calculate Nyquist frequency
        nyquist_freq = 2 * fmax

        # Generate unique ID for this audio session
        session_id = str(uuid.uuid4())

        # Store original audio in memory
        audio_storage[session_id] = {
            'audio_data': audio_data,
            'original_sr': int(sample_rate),
            'fmax': float(fmax),
            'nyquist_freq': float(nyquist_freq)
        }

        return JsonResponse({
            'success': True,
            'fmax': round(fmax, 2),
            'nyquist_freq': round(nyquist_freq, 2),
            'original_sr': int(sample_rate),
            'session_id': session_id
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



@require_http_methods(["POST"])
def resample_audio(request):
    try:
        session_id = request.POST.get('session_id')
        new_sr = int(request.POST.get('sampling_rate', 44100))

        if not session_id or session_id not in audio_storage:
            return JsonResponse({'success': False, 'error': 'No audio data found. Please analyze audio first.'})

        # Retrieve audio data from memory
        stored_data = audio_storage[session_id]
        audio_data = stored_data['audio_data']
        original_sr = stored_data['original_sr']
        nyquist_freq = stored_data['nyquist_freq']

        # Resample audio to target rate (no anti-aliasing filter to show aliasing effects)
        num_samples = int(len(audio_data) * new_sr / original_sr)
        resampled_audio = signal.resample(audio_data, num_samples)

        # For very low sample rates, upsample back to 44100 Hz for browser playback
        playback_sr = new_sr
        if new_sr < 8000:
            # Upsample back to 44100 for playback while maintaining the downsampled quality
            playback_sr = 44100
            upsampled_audio = signal.resample(resampled_audio, int(len(resampled_audio) * playback_sr / new_sr))
            resampled_audio = upsampled_audio

        # Normalize properly
        max_val = np.max(np.abs(resampled_audio))
        if max_val > 0:
            resampled_audio = resampled_audio / max_val * 0.85

        # Convert to 16-bit PCM with proper scaling
        resampled_audio = np.clip(resampled_audio, -1.0, 1.0)
        audio_int16 = np.int16(resampled_audio * 32767)

        # Create WAV in memory with playback sample rate
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, playback_sr, audio_int16)
        wav_buffer.seek(0)

        # Encode to base64 for playback
        audio_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')

        # Check if below Nyquist
        is_below_nyquist = new_sr < nyquist_freq

        return JsonResponse({
            'success': True,
            'audio_data': f'data:audio/wav;base64,{audio_base64}',
            'is_below_nyquist': is_below_nyquist,
            'current_sr': new_sr,
            'nyquist_freq': nyquist_freq
        })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)