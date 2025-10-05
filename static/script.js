document.addEventListener("DOMContentLoaded", () => {
  console.log("script.js loaded");

  const addCategoryBtn = document.getElementById("addCategoryBtn");
  const generateBtn = document.getElementById("generateBtn");
  const categoriesContainer = document.getElementById("categoriesContainer");
  const skuResult = document.getElementById("skuResult");
  const barcodeImage = document.getElementById("barcodeImage");
  const downloadRow = document.getElementById("downloadRow");

  // Helper: create a category row DOM node
  function createCategoryRow(type = "", value = "") {
    const div = document.createElement("div");
    div.className = "category-row category";
    div.innerHTML = `
      <input class="catType" placeholder="Category Type (e.g., Color)" value="${type}">
      <input class="catValue" placeholder="Category Value (e.g., Blue)" value="${value}">
      <button class="remove-row-btn" type="button" title="Remove">✕</button>
    `;
    // remove handler
    div.querySelector(".remove-row-btn").addEventListener("click", () => {
      div.remove();
    });
    return div;
  }

  // Add new category row
  addCategoryBtn.addEventListener("click", () => {
    categoriesContainer.appendChild(createCategoryRow());
  });

  // Ensure there's always at least one row (if someone removed them all)
  if (!categoriesContainer.querySelector(".category")) {
    categoriesContainer.appendChild(createCategoryRow());
  }

  // Generate SKU & barcode
  generateBtn.addEventListener("click", async (e) => {
    try {
      console.log("Generate button clicked");
      generateBtn.disabled = true;
      generateBtn.textContent = "Generating...";

      const productName = document.getElementById("productName").value.trim();
      if (!productName) {
        alert("Please enter product name");
        generateBtn.disabled = false;
        generateBtn.textContent = "Generate SKU & Barcode";
        return;
      }

      // gather categories
      const categories = {};
      const rows = categoriesContainer.querySelectorAll(".category");
      rows.forEach(row => {
        const t = row.querySelector(".catType").value.trim();
        const v = row.querySelector(".catValue").value.trim();
        if (t && v) categories[t] = v;
      });

      console.log("Payload:", { name: productName, categories });

      const endpoint = window.location.origin + "/generate_sku";
      console.log("Calling endpoint:", endpoint);

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: productName, categories })
      });

      let data;
      try {
        data = await res.json();
      } catch (jsonErr) {
        throw new Error("Invalid JSON response from server");
      }

      if (!res.ok) {
        throw new Error(data.error || JSON.stringify(data));
      }

      console.log("Server response:", data);
      skuResult.textContent = data.sku || "-";

     if (data.barcode_url) {
  // add cache-busting parameter
  const freshUrl = data.barcode_url + "?v=" + Date.now();
  barcodeImage.src = freshUrl;
  downloadRow.innerHTML = `<a class="download-btn" href="${freshUrl}" download>Download Barcode</a>`;
} else {
  barcodeImage.src = "";
  downloadRow.innerHTML = `<small style="color:#b00">Barcode generation failed on server</small>`;
}

    } catch (err) {
      console.error("Error generating SKU:", err);
      alert("Error generating SKU: " + (err.message || err));
    } finally {
      generateBtn.disabled = false;
      generateBtn.textContent = "Generate SKU & Barcode";
    }
  });

  // Quick test helpers you can run in Console:
  //  - document.getElementById('addCategoryBtn').click()
  //  - document.getElementById('generateBtn').click()
});
