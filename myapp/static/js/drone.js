const analyzeBtn = document.getElementById("analyzeBtn");
const resampleBtn = document.getElementById("resampleBtn");
const classifyBtn = document.getElementById("classifyBtn");
const resultDiv = document.getElementById("result");
const classificationSpan = document.getElementById("classification");
const confidenceSpan = document.getElementById("confidence");
const loadingDiv = document.getElementById("loading");
const analysisResultsDiv = document.getElementById("analysisResults");
const originalSrSpan = document.getElementById("originalSr");
const nyquistFreqSpan = document.getElementById("nyquistFreq");
const fmaxSpan = document.getElementById("fmax");
const resampleSlider = document.getElementById("resampleSlider");
const resampleValueSpan = document.getElementById("resampleValue");
const resampleStatus = document.getElementById("resampleStatus");

let currentAudioFile = null;
let currentAnalysisData = null;
let resampledAudioData = null;
let currentSampleRate = null;

// Step 1: Analyze audio (get sample rate, frequencies, etc.)
analyzeBtn.addEventListener("click", async () => {
  console.log(10);
  const fileInput = document.getElementById("audioFile");
  if (!fileInput.files.length) {
    alert("Please select an audio file first!");
    return;
  }

  currentAudioFile = fileInput.files[0];
  await analyzeAudio(currentAudioFile);
});

// Step 2: Resample audio when slider changes and button is clicked
resampleBtn.addEventListener("click", async () => {
  if (!currentAudioFile || !currentAnalysisData) {
    alert("Please analyze an audio file first!");
    return;
  }

  const newSampleRate = parseInt(resampleSlider.value);
  if (newSampleRate === 0) {
    alert("Please select a valid sample rate!");
    return;
  }

  await resampleAudio(currentAudioFile, newSampleRate);
});

// Step 3: Classify the (resampled) audio
classifyBtn.addEventListener("click", async () => {
  if (!currentAudioFile) {
    alert("Please analyze an audio file first!");
    return;
  }

  await classifyAudio();
});

// Update slider value display
resampleSlider.addEventListener("input", (e) => {
  resampleValueSpan.textContent = e.target.value;
});

async function analyzeAudio(audioFile) {
  const formData = new FormData();
  formData.append("audio", audioFile);

  resultDiv.style.display = "none";
  analysisResultsDiv.style.display = "none";
  loadingDiv.style.display = "block";
  resampleStatus.textContent = "";

  try {
    const response = await fetch("http://127.0.0.1:8000/analyze/", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    console.log(data);

    if (data.success) {
      // Store analysis data
      currentAnalysisData = data;
      currentSampleRate = data.original_sr;

      // Display analysis results
      originalSrSpan.textContent = data.original_sr;
      nyquistFreqSpan.textContent = data.nyquist_freq;
      fmaxSpan.textContent = data.fmax;

      // Setup slider
      resampleSlider.max = data.original_sr;
      resampleSlider.value = data.original_sr;
      resampleValueSpan.textContent = data.original_sr;

      analysisResultsDiv.style.display = "block";

      // Reset classification results
      classificationSpan.textContent = "";
      confidenceSpan.textContent = "";
      resampledAudioData = null;
      resampleStatus.textContent = "Using original audio sample rate";
    } else {
      alert("Error");
    }
  } catch (error) {
    alert("Failed to connect to API: " + error);
  }

  loadingDiv.style.display = "none";
}

async function resampleAudio(audioFile, newSampleRate) {
  const formData = new FormData();
  formData.append("audio", audioFile);
  formData.append("sampling_rate", newSampleRate.toString());

  loadingDiv.style.display = "block";
  resampleStatus.textContent = "Resampling...";

  try {
    const resampleResponse = await fetch("http://127.0.0.1:8000/resample/", {
      method: "POST",
      body: formData,
    });

    const resampleData = await resampleResponse.json();
    console.log(resampleData);

    if (!resampleData.audio_data) {
      throw new Error(resampleData.error || "No audio returned from server");
    }

    // ✅ Set audio source to the returned base64 WAV
    const audioPlayer = document.getElementById("resampledAudioPlayer");
    audioPlayer.src = resampleData.audio_data;
    audioPlayer.style.display = "block"; // show player
    audioPlayer.play(); // automatically play (optional)

    resampledAudioData = resampleData.audio_data;
    currentSampleRate = newSampleRate;
    resampleStatus.textContent = `Audio resampled to ${newSampleRate} Hz successfully!`;

    // Clear previous classification results
    classificationSpan.textContent = "";
    confidenceSpan.textContent = "";
    resultDiv.style.display = "none";
  } catch (error) {
    console.error("Resampling error:", error);
    resampleStatus.textContent = "Failed to resample audio: " + error.message;
  } finally {
    loadingDiv.style.display = "none";
  }
}

async function classifyAudio() {
  loadingDiv.style.display = "block";
  resultDiv.style.display = "none";

  try {
    let response;

    if (resampledAudioData) {
      // Convert base64 string to Blob
      const base64Data = resampledAudioData.split(",")[1];
      const byteCharacters = atob(base64Data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const audioBlob = new Blob([byteArray], { type: "audio/wav" });
      const audioFile = new File([audioBlob], "resampled.wav", {
        type: "audio/wav",
      });

      // Create form data for upload
      const formData = new FormData();
      formData.append("audio", audioFile);

      response = await fetch("http://127.0.0.1:8000/drones/analyze/", {
        method: "POST",
        body: formData,
      });
    } else {
      // Use original audio file
      const formData = new FormData();
      formData.append("audio", currentAudioFile);

      response = await fetch("http://127.0.0.1:8000/drones/analyze/", {
        method: "POST",
        body: formData,
      });
    }

    const classificationData = await response.json();

    if (classificationData.status === "success") {
      classificationSpan.textContent = classificationData.classification;
      confidenceSpan.textContent = classificationData.confidence;
      resultDiv.style.display = "block";
    } else {
      alert("Classification error: " + classificationData.status);
    }
  } catch (error) {
    alert("Failed to classify audio: " + error);
  }

  loadingDiv.style.display = "none";
}
