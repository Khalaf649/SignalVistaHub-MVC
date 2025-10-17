import os
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from skimage.transform import downscale_local_mean
from django.http import JsonResponse
from django.shortcuts import render


def process_sar(request):
    if request.method == "POST":
        folder_path = request.POST.get("folder_path")
        if not folder_path:
            return JsonResponse({"error": "No folder path provided."})

        if not os.path.exists(folder_path):
            return JsonResponse({"error": f"Folder not found: {folder_path}"})

        try:
            # Find first .tiff file in the SAFE folder
            tiff_file = None
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    if f.lower().endswith(".tiff"):
                        tiff_file = os.path.join(root, f)
                        break
                if tiff_file:
                    break

            if not tiff_file:
                return JsonResponse({"error": "No .tiff measurement file found in SAFE folder."})

            # Read first band with rasterio
            with rasterio.open(tiff_file) as src:
                image_data = src.read(1).astype(np.float32)

            # Downsample if too large
            max_dim = 2048
            if image_data.shape[0] > max_dim or image_data.shape[1] > max_dim:
                factor_row = max(1, image_data.shape[0] // max_dim)
                factor_col = max(1, image_data.shape[1] // max_dim)
                image_data = downscale_local_mean(image_data, (factor_row, factor_col))

            # Convert to dB
            amplitude_db = 10 * np.log10(image_data + 1e-6)

            # Plot
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.imshow(amplitude_db, cmap='gray', aspect='auto')
            ax.set_title(f"Sentinel-1 GRD Image (dB)\n{os.path.basename(tiff_file)}")
            ax.set_xlabel("Range bins")
            ax.set_ylabel("Azimuth lines")

            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            img_b64 = base64.b64encode(buf.getbuffer()).decode("utf8")

            return JsonResponse({"image": f"data:image/png;base64,{img_b64}"})

        except Exception as e:
            return JsonResponse({"error": f"Error processing GRD .SAFE folder: {e}"})

    return JsonResponse({"error": "Invalid request method."})