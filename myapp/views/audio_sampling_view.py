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
import io
import base64
import numpy as np
import librosa
import soundfile as sf
import tensorflow as tf
from transformers import pipeline
from django.http import JsonResponse




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

ANTI_ALIAS_MODEL_PATH = "anti_alias_model.h5"

try:
    aa_model = tf.keras.models.load_model(ANTI_ALIAS_MODEL_PATH, compile=False)
    MODEL_LOADED = True
    print("✅ Anti-aliasing model loaded successfully!")
except Exception as e:
    print(f"⚠ Could not load anti-aliasing model: {e}")
    MODEL_LOADED = False
    aa_model = None

# Load Hugging Face Gender Classifier
try:
    classifier = pipeline("audio-classification", model="prithivMLmods/Common-Voice-Gender-Detection")
    print("✅ Gender classifier loaded successfully!")
except Exception as e:
    print(f"⚠ Could not load gender classifier: {e}")
    classifier = None


# -------------------------------
# Helper: Apply Anti-Aliasing
# -------------------------------
def apply_model_reconstruction(y_input, sr_input):
    if not MODEL_LOADED:
        print("⚠ Model not available, performing standard upsampling.")
        return librosa.resample(y_input, orig_sr=sr_input, target_sr=16000)

    try:
        model_sr = 16000
        model_len = 48000
        y_upsampled = librosa.resample(y_input, orig_sr=sr_input, target_sr=model_sr)

        reconstructed_chunks = []
        for i in range(0, len(y_upsampled), model_len):
            chunk = y_upsampled[i:i + model_len]
            len_chunk = len(chunk)
            if len_chunk < model_len:
                chunk = np.pad(chunk, (0, model_len - len_chunk), mode='constant')

            model_input = chunk[np.newaxis, ..., np.newaxis]
            pred_chunk = np.squeeze(aa_model.predict(model_input, verbose=0))
            if len_chunk < model_len:
                pred_chunk = pred_chunk[:len_chunk]
            reconstructed_chunks.append(pred_chunk)

        y_reconstructed = np.concatenate(reconstructed_chunks)
        return y_reconstructed
    except Exception as e:
        print(f"❌ Error during reconstruction: {e}")
        return librosa.resample(y_input, orig_sr=sr_input, target_sr=16000)


# -------------------------------
# Django Endpoint
# -------------------------------
@require_http_methods(["POST"])
def predict_audio(request):
    """
    POST endpoint that:
    - takes an uploaded audio file,
    - applies anti-aliasing,
    - classifies gender,
    - returns base64 of reconstructed audio + prediction result.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Only POST requests allowed."})

    if "audio" not in request.FILES:
        return JsonResponse({"success": False, "error": "No audio file uploaded."})

    try:
        # Load uploaded audio
        audio_file = request.FILES["audio"]
        y, sr = librosa.load(audio_file, sr=None)
        print(f"Loaded audio with SR={sr}, length={len(y)/sr:.2f}s")

        # Apply anti-aliasing
        y_reconstructed = apply_model_reconstruction(y, sr)

        # Save to memory buffer as WAV
        buffer = io.BytesIO()
        sf.write(buffer, y_reconstructed, 16000, format="WAV")
        buffer.seek(0)

        # Classify reconstructed audio
        if classifier:
            # Hugging Face pipeline works directly with np.ndarray or file-like
            results = classifier({"array": y_reconstructed, "sampling_rate": 16000})
            top = results[0]
            label = top["label"]
            score = round(top["score"], 3)
        else:
            label, score = "unknown", 0.0

        # Encode audio as base64 for frontend playback
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        audio_data_uri = f"data:audio/wav;base64,{audio_base64}"

        return JsonResponse({
            "success": True,
            "label": label,
            "confidence": score,
            "audio_data": audio_data_uri
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

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

   