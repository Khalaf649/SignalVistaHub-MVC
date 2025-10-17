document.getElementById("simulateBtn").addEventListener("click", async () => {
  const freq = parseFloat(document.getElementById("frequency").value);
  const vel = parseFloat(document.getElementById("velocity").value);
  const dur = parseFloat(document.getElementById("duration").value);

  const resultsDiv = document.getElementById("results");
  resultsDiv.innerText = "Processing...";

  try {
    const res = await fetch("/doppler/simulate/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        frequency: freq,
        velocity: vel,
        duration: dur,
      }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();

    if (data.status !== "success") {
      resultsDiv.innerText = "Error: " + data.error;
      return;
    }

    // --- Audio playback ---
    const audioBlob = base64ToBlob(data.audio, "audio/wav");
    const audioURL = URL.createObjectURL(audioBlob);
    const player = document.getElementById("audioPlayer");
    player.src = audioURL;
    player.play();

    // --- Plot amplitude vs time ---
    plotChart(
      "ampChart",
      "Amplitude vs Time",
      data.time,
      data.amplitude,
      "#0059b3"
    );

    // --- Plot frequency vs time ---
    plotChart(
      "freqChart",
      "Frequency vs Time",
      data.time,
      data.frequency,
      "#ff9800"
    );

    // --- Show results ---
    resultsDiv.innerHTML = `
                    <strong>Results:</strong><br>
                    Max Frequency: ${data.max_frequency.toFixed(2)} Hz<br>
                    Min Frequency: ${data.min_frequency.toFixed(2)} Hz<br>
                    Shift Ratio: ${data.shift_ratio.toFixed(3)}
                `;
  } catch (err) {
    resultsDiv.innerText = "Error: " + err.message;
  }
});

// Helper: Convert Base64 to Blob
function base64ToBlob(base64, type = "application/octet-stream") {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type });
}

// Helper: Plot chart
let charts = {};
function plotChart(canvasId, label, xData, yData, color) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  if (charts[canvasId]) charts[canvasId].destroy();
  charts[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels: xData,
      datasets: [
        {
          label,
          data: yData,
          borderColor: color,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { display: false },
      },
    },
  });
}
