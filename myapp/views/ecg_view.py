import os
import tempfile
import wfdb
from django.http import JsonResponse
from django.shortcuts import render





def ecg_upload(request):
    """Handle uploaded ECG .dat/.hea files and return signal(s) for plotting"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'})

    # Get uploaded files
    dat_file = request.FILES.get('dat_file')
    hea_file = request.FILES.get('hea_file')

    if not dat_file or not hea_file:
        return JsonResponse({'error': 'Both .dat and .hea files are required'})

    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Save both files
        dat_path = os.path.join(temp_dir, dat_file.name)
        hea_path = os.path.join(temp_dir, hea_file.name)

        with open(dat_path, 'wb') as f:
            for chunk in dat_file.chunks():
                f.write(chunk)
        with open(hea_path, 'wb') as f:
            for chunk in hea_file.chunks():
                f.write(chunk)

        # Read ECG record (wfdb automatically uses both files)
        base_name = os.path.splitext(dat_path)[0]
        record = wfdb.rdrecord(base_name)

        # Convert to JSON-friendly structures
        signals = record.p_signal.tolist()
        channels = record.sig_name
        fs = record.fs

        return JsonResponse({
            'signals': signals,
            'channels': channels,
            'fs': fs
        })

    except Exception as e:
        return JsonResponse({'error': str(e)})