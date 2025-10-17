import os
import torch
from django.http import JsonResponse
from transformers import pipeline
from django.views.decorators.csrf import csrf_exempt



def drone_upload(request):
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]

        # Save uploaded file temporarily
        temp_path = f"temp_{audio_file.name}"
        with open(temp_path, "wb+") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        try:
            # Load the Hugging Face model
            model_id = "preszzz/drone-audio-detection-05-17-trial-0"
            classifier = pipeline(
                "audio-classification",
                model=model_id,
                device=0 if torch.cuda.is_available() else -1
            )

            # Predict
            predictions = classifier(temp_path)
            top = predictions[0]
            result = {
                "classification": top["label"],
                "confidence": round(top["score"], 4),
                "status": "success"
            }

        except Exception as e:
            result = {"error": str(e)}

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return JsonResponse(result)

    return JsonResponse({"error": "No audio file uploaded."}, status=400)