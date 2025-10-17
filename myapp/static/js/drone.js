const form = document.getElementById("droneForm");
const resultDiv = document.getElementById("result");
const classificationSpan = document.getElementById("classification");
const confidenceSpan = document.getElementById("confidence");
const loadingDiv = document.getElementById("loading");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const fileInput = document.getElementById("audioFile");
  if (!fileInput.files.length) {
    alert("Please select an audio file first!");
    return;
  }

  const formData = new FormData();
  formData.append("audio", fileInput.files[0]);

  resultDiv.style.display = "none";
  loadingDiv.style.display = "block";

  try {
    const response = await fetch("http://127.0.0.1:8000/drones/analyze/", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (data.status === "success") {
      classificationSpan.textContent = data.classification;
      confidenceSpan.textContent = data.confidence;
      resultDiv.style.display = "block";
    } else {
      alert("Error: " + data.status);
    }
  } catch (error) {
    alert("Failed to connect to API: " + error);
  }

  loadingDiv.style.display = "none";
});
