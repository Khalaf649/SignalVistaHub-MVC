import io
import json
import base64
import numpy as np
from scipy.io.wavfile import write
from django.http import JsonResponse


def simulate_doppler(request):
    """
    Simulates Doppler effect — returns audio (Base64) + analysis data
    """
    if request.method != "POST":
        return JsonResponse({"status": "failed", "error": "Use POST method"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        frequency = float(data.get("frequency"))
        velocity = float(data.get("velocity"))
        duration = float(data.get("duration"))
        fs = int(data.get("fs", 8000))  # default sampling rate
    except Exception as e:
        return JsonResponse({"status": "failed", "error": f"Invalid input: {str(e)}"}, status=400)

    try:
        v_sound = 343.0  # speed of sound (m/s)
        d = 5.0          # perpendicular distance (m)

        # Time array
        t = np.linspace(0, duration, int(duration * fs), endpoint=False)
        t0 = duration / 2.0
        x = velocity * (t - t0)
        r = np.sqrt(x**2 + d**2)

        # Doppler-shifted frequency
        v_rad = velocity * (-x) / r
        f_o = frequency * v_sound / (v_sound - v_rad)

        # Generate waveform
        dt = t[1] - t[0]
        phi = 2 * np.pi * np.cumsum(f_o) * dt
        signal = np.sin(phi)

        # Apply amplitude scaling (inverse-square law)
        amp = 1.0 / (r**2)
        amp /= np.max(amp)
        signal *= amp
        signal /= np.max(np.abs(signal))

        # Stereo effect
        left = signal * np.sqrt(0.5 * (1 - x / r))
        right = signal * np.sqrt(0.5 * (1 + x / r))
        signal_stereo = np.column_stack((left, right))

        # Save to WAV in memory
        wav_bytes = io.BytesIO()
        write(wav_bytes, fs, np.int16(signal_stereo * 32767))
        wav_bytes.seek(0)

        # Encode WAV as Base64 for JSON transfer
        audio_base64 = base64.b64encode(wav_bytes.read()).decode("utf-8")

        # Frequency stats
        max_freq = float(np.max(f_o))
        min_freq = float(np.min(f_o))
        shift_ratio = max_freq / min_freq if min_freq != 0 else float("inf")

        return JsonResponse({
            "status": "success",
            "audio": audio_base64,  # base64-encoded audio
            "time": t.tolist(),
            "amplitude": signal.tolist(),
            "frequency": f_o.tolist(),
            "max_frequency": max_freq,
            "min_frequency": min_freq,
            "shift_ratio": shift_ratio,
            "fs":fs
        })

    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=500)