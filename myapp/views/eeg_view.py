import os
import tempfile
import shutil
import mne
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


TRUNC_SECS = 10  # keep first N seconds only


@csrf_exempt
def eeg_upload(request):
    """Handle uploaded EEG .set files and return signal(s) for plotting (truncated to first TRUNC_SECS)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'})

    set_file = request.FILES.get('set_file')
    if not set_file:
        return JsonResponse({'error': '.set file is required'})

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        set_path = os.path.join(temp_dir, set_file.name)

        # Save uploaded file
        with open(set_path, 'wb') as f:
            for chunk in set_file.chunks():
                f.write(chunk)

        # Load EEG data using MNE (preload to access data)
        raw = mne.io.read_raw_eeglab(set_path, preload=True)
        data, times = raw.get_data(return_times=True)  # data shape: (n_channels, n_samples)
        channels = raw.ch_names
        fs = int(raw.info.get('sfreq', 0) or 0)
        if fs <= 0:
            # fallback or error
            raw.close()
            return JsonResponse({'error': 'Invalid sampling frequency from file'})

        # Truncate to first TRUNC_SECS seconds (server-side)
        max_samples = min(data.shape[1], int(fs * TRUNC_SECS))
        if max_samples <= 0:
            raw.close()
            return JsonResponse({'error': 'No samples found in uploaded file'})

        data_trunc = data[:, :max_samples]  # still (n_channels, n_samples_trunc)

        # Convert to shape (samples, channels) for frontend (same as before)
        signals = data_trunc.T.tolist()  # shape: (n_samples_trunc, n_channels)

        # close raw to free resources
        raw.close()

        return JsonResponse({
            'signals': signals,
            'channels': channels,
            'fs': fs
        })

    except Exception as e:
        return JsonResponse({'error': str(e)})
    finally:
        # cleanup temporary directory if created
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


