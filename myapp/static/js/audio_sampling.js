const audioFileInput = document.getElementById("audioFile");
const resultsSection = document.getElementById("resultsSection");
const errorBox = document.getElementById("errorBox");
const successBox = document.getElementById("successBox");
const samplingSlider = document.getElementById("samplingSlider");
const sliderValue = document.getElementById("sliderValue");
const audioPlayer = document.getElementById("audioPlayer");
const loader = document.getElementById("loader");

let nyquistFreq = 0;

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.add("show");
  setTimeout(() => errorBox.classList.remove("show"), 5000);
}

function showSuccess(message) {
  successBox.textContent = message;
  successBox.classList.add("show");
  setTimeout(() => successBox.classList.remove("show"), 3000);
}

async function analyzeAudio() {
  const file = audioFileInput.files[0];
  if (!file) {
    showError("Please select an audio file");
    return;
  }
  console.log(file);

  const formData = new FormData();
  formData.append("audio", file);

  loader.style.display = "block";
  errorBox.classList.remove("show");

  try {
    const response = await fetch("/analyze/", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    console.log(data);

    if (data.success) {
      nyquistFreq = data.nyquist_freq;

      document.getElementById("fmax").textContent = data.fmax;
      document.getElementById("nyquist").textContent = data.nyquist_freq;
      document.getElementById("originalSr").textContent = data.original_sr;

      samplingSlider.min = 1;
      samplingSlider.max = data.original_sr;
      samplingSlider.value = data.original_sr;

      resultsSection.classList.remove("hidden");
      showSuccess("Audio analyzed successfully!");
      updateSliderDisplay();
      resampleAudio();
    } else {
      showError("Error: " + data.error);
    }
  } catch (error) {
    showError("Error analyzing audio: " + error.message);
  } finally {
    loader.style.display = "none";
  }
}

function updateSliderDisplay() {
  const currentValue = parseInt(samplingSlider.value);
  sliderValue.textContent = currentValue + " Hz";

  if (currentValue < nyquistFreq) {
    sliderValue.classList.add("warning");
    samplingSlider.classList.add("warning");
    sliderValue.textContent += " ⚠️ Below Nyquist";
  } else {
    sliderValue.classList.remove("warning");
    samplingSlider.classList.remove("warning");
  }
}

async function resampleAudio() {
  const file = audioFileInput.files[0];
  console.log(file);
  if (!file) {
    showError("Please select an audio file");
    return;
  }

  const formData = new FormData();
  formData.append("audio", file);
  const samplingRate = parseInt(samplingSlider.value);
  formData.append("sampling_rate", samplingRate);
  console.log(formData);

  try {
    const response = await fetch("/resample/", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    audioPlayer.src = data.audio_data;
    console.log("Audio loaded:", data.audio_data.substring(0, 50));
  } catch (error) {
    showError("Error: " + error.message);
  }
}

samplingSlider.addEventListener("input", () => {
  updateSliderDisplay();
  resampleAudio();
});
