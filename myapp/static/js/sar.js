document.getElementById("load-btn").addEventListener("click", function () {
  const folderPath = document.getElementById("folder-path").value;
  if (!folderPath) {
    alert("Please enter a folder path.");
    return;
  }

  const formData = new URLSearchParams();
  formData.append("folder_path", folderPath);

  fetch("{% url 'process_sar' %}", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  })
    .then((response) => response.json())
    .then((data) => {
      const outputDiv = document.getElementById("output");
      if (data.error) {
        outputDiv.innerHTML = `<p style="color:red;">${data.error}</p>`;
      } else if (data.image) {
        outputDiv.innerHTML = `<img src="${data.image}" style="max-width: 100%;">`;
      }
    })
    .catch((error) => {
      alert("An error occurred: " + error);
    });
});
