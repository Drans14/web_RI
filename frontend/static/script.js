// ===================
// Sidebar Navigation
// ===================
const hamburgerBtn   = document.getElementById('hamburgerBtn');
const sidebar        = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const mainArea       = document.getElementById('mainArea');

function toggleSidebar() {
  hamburgerBtn.classList.toggle('active');
  sidebar.classList.toggle('open');
  sidebarOverlay.classList.toggle('active');

  const backItem = document.querySelector('.back-item');
  if (sidebar.classList.contains('open')) {
    backItem.style.display = 'flex';
  } else {
    backItem.style.display = 'none';
  }

  if (window.innerWidth >= 1200) {
    mainArea.classList.toggle('sidebar-open');
  }
}

hamburgerBtn.addEventListener('click', toggleSidebar);
sidebarOverlay.addEventListener('click', toggleSidebar);

document.addEventListener('click', function(e) {
  if (
    window.innerWidth < 1200 &&
    !sidebar.contains(e.target) &&
    !hamburgerBtn.contains(e.target) &&
    sidebar.classList.contains('open')
  ) {
    toggleSidebar();
  }
});

window.addEventListener('resize', function() {
  if (window.innerWidth >= 1200) {
    sidebarOverlay.classList.remove('active');
  } else {
    mainArea.classList.remove('sidebar-open');
  }
});

// ===================
// Page Navigation
// ===================
const pages = {
  home:      document.getElementById('homePage'),
  dashboard: document.getElementById('dashboardPage'),
  upload:    document.getElementById('uploadPage'),
  analisis:  document.getElementById('analisisPage')
};

function showPage(page) {
  // Hide all pages
  Object.values(pages).forEach(p => {
    if (p) {
      p.style.display = 'none';
    }
  });
  
  // Show selected page
  if (pages[page]) {
    pages[page].style.display = 'block';
    
    // Load files when showing upload page
    if (page === 'upload') {
      loadFilesFromServer();
    }
  }

  // Update active navigation item
  document.querySelectorAll('.nav-item').forEach(nav => {
    if (nav.dataset.page) {
      nav.classList.toggle('active', nav.dataset.page === page);
    }
  });

  // Close sidebar on mobile after navigation
  if (window.innerWidth < 1200 && sidebar.classList.contains('open')) {
    toggleSidebar();
  }
}

function goToHome() {
  showPage('home');
  if (sidebar.classList.contains('open')) toggleSidebar();
}

function handleGetStarted() {
  showPage('upload');
}

function closeSidebar() {
  if (sidebar.classList.contains('open')) toggleSidebar();
}

// Initialize with home page
showPage('home');

// Add click event listeners to navigation items
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', function(e) {
    e.preventDefault();
    const page = this.dataset.page;
    if (page) {
      showPage(page);
    }
  });
});

// ===================
// Upload & File Table
// ===================
let uploadedFiles = [];

const dropzone       = document.querySelector('.dropzone');
const uploadBtn      = document.querySelector('.upload-btn');
const fileInput      = document.getElementById('fileInput');
const fileTableBody  = document.getElementById('fileTableBody');

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function renderTable() {
  if (!fileTableBody) return;
  
  fileTableBody.innerHTML = '';
  uploadedFiles.forEach((file, idx) => {
    let statusText = '❌ Format Salah';
    if (file.status === 'success') statusText = '✅ Berhasil Diupload';
    if (file.status === 'duplicate') statusText = '❌ File Sudah Ada';
    
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${file.name}</td>
      <td>${formatSize(file.size)}</td>
      <td>${statusText}</td>
      <td>
        <button class="action-btn" title="Delete" onclick="deleteFile(${idx})">🗑️</button>
      </td>
    `;
    fileTableBody.appendChild(row);
  });
}

function loadFilesFromServer() {
  fetch('/files')
    .then(res => {
      if (!res.ok) {
        throw new Error('Network response was not ok');
      }
      return res.json();
    })
    .then(files => {
      uploadedFiles = files || [];
      renderTable();
    })
    .catch(error => {
      console.error('Error loading files:', error);
      uploadedFiles = [];
      renderTable();
    });
}

function deleteFile(idx) {
  if (idx < 0 || idx >= uploadedFiles.length) return;
  
  const file = uploadedFiles[idx];
  const formData = new FormData();
  formData.append('name', file.name);

  fetch('/delete', {
    method: 'POST',
    body: formData
  })
  .then(res => res.text())
  .then(msg => {
    if (msg === 'OK') {
      loadFilesFromServer();
    } else {
      alert('Gagal menghapus file');
    }
  })
  .catch(error => {
    console.error('Error deleting file:', error);
    alert('Gagal menghapus file');
  });
}

// Make deleteFile available globally
window.deleteFile = deleteFile;

// Upload button click handler
if (uploadBtn) {
  uploadBtn.addEventListener('click', () => {
    if (fileInput) {
      fileInput.click();
    }
  });
}

// File input change handler
if (fileInput) {
  fileInput.addEventListener('change', function() {
    const file = this.files[0];
    if (!file) return;

    // Validate file type
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx') {
      alert('File harus berformat CSV atau XLSX');
      this.value = '';
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    // Show loading state
    uploadBtn.textContent = 'Uploading...';
    uploadBtn.disabled = true;

    fetch('/upload', {
      method: 'POST',
      body: formData
    })
    .then(res => res.text())
    .then(msg => {
      let status = 'fail';
      if (msg === 'OK') status = 'success';
      if (msg === 'DUPLICATE') status = 'duplicate';

      if (status === 'duplicate') {
        alert('File sudah ada di server');
      } else if (status === 'success') {
        alert('File berhasil diupload');
      } else {
        alert('Gagal mengupload file');
      }

      loadFilesFromServer();
    })
    .catch(error => {
      console.error('Error uploading file:', error);
      alert('Gagal mengupload file');
    })
    .finally(() => {
      // Reset upload button
      uploadBtn.textContent = 'Upload File';
      uploadBtn.disabled = false;
      this.value = '';
    });
  });
}

// Drag and drop handlers
if (dropzone) {
  dropzone.addEventListener('dragover', e => {
    e.preventDefault();
    dropzone.style.borderColor = '#8B2E2E';
    dropzone.style.backgroundColor = '#f9f9f9';
  });

  dropzone.addEventListener('dragleave', e => {
    e.preventDefault();
    dropzone.style.borderColor = '#ccc';
    dropzone.style.backgroundColor = 'transparent';
  });

  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.style.borderColor = '#ccc';
    dropzone.style.backgroundColor = 'transparent';
    
    const file = e.dataTransfer.files[0];
    if (!file) return;

    // Validate file type
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx') {
      alert('File harus berformat CSV atau XLSX');
      return;
    }

    // Trigger file upload
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
      method: 'POST',
      body: formData
    })
    .then(res => res.text())
    .then(msg => {
      if (msg === 'OK') {
        alert('File berhasil diupload');
        loadFilesFromServer();
      } else if (msg === 'DUPLICATE') {
        alert('File sudah ada di server');
      } else {
        alert('Gagal mengupload file');
      }
    })
    .catch(error => {
      console.error('Error uploading file:', error);
      alert('Gagal mengupload file');
    });
  });

  // Make dropzone clickable
  dropzone.addEventListener('click', () => {
    if (fileInput) {
      fileInput.click();
    }
  });
}

// ===================
// Analisis & Plot Handling
// ===================
function showAnalisisSlide(mode) {
  // Hide all analysis slides
  document.querySelectorAll('#analisisPage .analisis-slide').forEach(el => {
    el.classList.remove('active');
  });
  
  // Show selected slide
  const slideId = `analisis${mode.charAt(0).toUpperCase() + mode.slice(1)}`;
  const target = document.getElementById(slideId);
  if (target) {
    target.classList.add('active');
  }
}

// Initialize with default slide
showAnalisisSlide('default');

// Run Analysis Button Handler
const runAnalysisBtn = document.getElementById("runAnalysisBtn");
if (runAnalysisBtn) {
  runAnalysisBtn.addEventListener("click", function() {
    // Check if files are uploaded
    if (uploadedFiles.length === 0) {
      alert("Silakan unggah file terlebih dahulu.");
      return;
    }

    // Get analysis method
    const metodeSelect = document.getElementById("metodeAnalisis");
    const metode = metodeSelect ? metodeSelect.value : null;

    if (!metode) {
      alert("Silakan pilih metode analisis.");
      return;
    }

    // Get first uploaded file name
    const namaFile = uploadedFiles[0].name;

    // Navigate to analysis page
    showPage('analisis');
    
    // Show appropriate analysis slide
    showAnalisisSlide(metode);

    // Run analysis based on method
    if (metode === "bertopic") {
      jalankanAnalisisBertopic(namaFile);
    } else if (metode === "keyword") {
      jalankanAnalisisKeyword(namaFile);
    } else {
      alert("Metode analisis belum didukung.");
    }
  });
}

// ===================
// Analysis Functions
// ===================
// Fungsi untuk menyisipkan HTML berisi <script> dan mengeksekusinya
function setInnerHTMLWithScripts(el, html) {
  // Kosongkan elemen terlebih dahulu
  el.innerHTML = "";

  // Buat elemen sementara untuk parsing
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = html;

  // Pindahkan semua elemen non-script terlebih dahulu
  const scripts = [];
  const nodes = Array.from(tempDiv.childNodes);
  
  nodes.forEach(node => {
    if (node.tagName === "SCRIPT") {
      scripts.push(node);
    } else {
      el.appendChild(node.cloneNode(true));
    }
  });

  // Eksekusi script setelah DOM siap
  scripts.forEach(oldScript => {
    const newScript = document.createElement("script");
    
    // Copy semua atribut
    Array.from(oldScript.attributes).forEach(attr => {
      newScript.setAttribute(attr.name, attr.value);
    });
    
    // Set content
    if (oldScript.src) {
      newScript.src = oldScript.src;
      newScript.onload = () => {
        console.log("External script loaded:", oldScript.src);
      };
    } else {
      newScript.textContent = oldScript.textContent;
    }
    
    // Append ke head atau body untuk eksekusi
    document.head.appendChild(newScript);
    
    // Log untuk debugging
    console.log("Script executed:", newScript.src || "inline script");
  });
}

// Fungsi utama untuk menjalankan analisis BERTopic
function jalankanAnalisisBertopic(namaFile) {
  const hasilDiv = document.getElementById("hasilBertopic");
  const paramDiv = document.getElementById("parameterTerbaik");
  const containerDiv = document.getElementById("analisisBertopic");

  // Tampilkan loading
  hasilDiv.innerHTML = `
    <div style="text-align:center;padding:20px;">
      <p>Memproses analisis BERTopic...</p>
      <div class="loader"></div>
    </div>
  `;

  fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `filename=${encodeURIComponent(namaFile)}&metode=bertopic`,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        hasilDiv.innerHTML = `<p>Error: ${data.error}</p>`;
        return;
      }

      console.log("Received data:", data);

      // METODE SEDERHANA: Langsung masukkan HTML tanpa parsing kompleks
      hasilDiv.innerHTML = data.plot_html;

      // Cari semua script di dalam HTML yang baru dimasukkan
      const scripts = hasilDiv.querySelectorAll('script');
      console.log("Found scripts:", scripts.length);

      // Eksekusi setiap script
      scripts.forEach((oldScript, index) => {
        const newScript = document.createElement('script');
        
        if (oldScript.src) {
          newScript.src = oldScript.src;
          console.log(`Loading external script ${index}:`, oldScript.src);
        } else {
          newScript.textContent = oldScript.textContent;
          console.log(`Executing inline script ${index}`);
        }

        // Replace script lama dengan yang baru
        oldScript.parentNode.replaceChild(newScript, oldScript);
      });

      // Tampilkan parameter
      if (data.best_params) {
        paramDiv.innerHTML = `
          <p><strong>min_cluster_size terbaik:</strong> ${data.best_params.min_cluster_size}</p>
          <p><strong>Coherence Score:</strong> ${parseFloat(data.best_params.coherence_score).toFixed(4)}</p>
        `;
      }

      containerDiv.classList.add("active");

      // Debug check setelah 2 detik
      setTimeout(() => {
        const plotDivs = hasilDiv.querySelectorAll('.plotly-graph-div');
        console.log("Plot divs found:", plotDivs.length);
        
        if (plotDivs.length > 0) {
          plotDivs.forEach((div, i) => {
            console.log(`Plot div ${i}:`, div.id, div.style.width, div.style.height);
          });
        } else {
          console.error("No plot divs found after script execution!");
        }
      }, 2000);
    })
    .catch((error) => {
      console.error("Error:", error);
      hasilDiv.innerHTML = `<p>Terjadi kesalahan: ${error.message}</p>`;
    });
}

function jalankanAnalisisKeyword(namaFile) {
  const hasilDiv = document.getElementById("hasilKeyword");
  if (!hasilDiv) return;

  // Show loading state
  hasilDiv.innerHTML = `
    <div style="text-align:center;padding:20px;">
      <p>Sedang memproses analisis Keyword Matching...</p>
      <div style="border:4px solid #f3f3f3; border-top:4px solid #3498db; border-radius:50%; width:30px; height:30px; animation:spin 2s linear infinite; margin:0 auto;"></div>
    </div>
    <style>@keyframes spin {0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}</style>
  `;

  // Send analysis request
  fetch("/analyze", {
    method: "POST",
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ 
      filename: namaFile, 
      metode: "keyword" 
    })
  })
  .then(res => {
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return res.json();
  })
  .then(data => {
    if (data.error) {
      hasilDiv.innerHTML = `
        <div style="color:red;padding:10px;border:1px solid red;border-radius:5px;">
          <strong>Error:</strong> ${data.error}
        </div>
      `;
      return;
    }

    // Handle keyword analysis results
    if (data.results) {
      let resultsHtml = '<h4>Hasil Matching Keywords:</h4>';
      resultsHtml += '<div style="margin-top:15px;">';
      
      if (Array.isArray(data.results)) {
        data.results.forEach((result, idx) => {
          resultsHtml += `
            <div style="margin-bottom:10px;padding:10px;border:1px solid #ddd;border-radius:5px;">
              <strong>Match ${idx + 1}:</strong> ${result.keyword || result.text || result}
              ${result.score ? `<span style="float:right;color:#666;">Score: ${result.score}</span>` : ''}
            </div>
          `;
        });
      } else {
        resultsHtml += `<pre>${JSON.stringify(data.results, null, 2)}</pre>`;
      }
      
      resultsHtml += '</div>';
      hasilDiv.innerHTML = resultsHtml;
    } else {
      hasilDiv.innerHTML = `
        <div style="color:orange;padding:10px;border:1px solid orange;border-radius:5px;">
          <strong>Warning:</strong> Tidak ada hasil keyword matching yang ditemukan.
        </div>
      `;
    }
  })
  .catch(err => {
    console.error('Analysis error:', err);
    hasilDiv.innerHTML = `
      <div style="color:red;padding:10px;border:1px solid red;border-radius:5px;">
        <strong>Error:</strong> ${err.message || 'Terjadi kesalahan saat analisis'}
      </div>
    `;
  });
}

// ===================
// Utility Functions
// ===================
function backToHome() {
  showPage('home');
}

// Handle back buttons if they exist
const backBtns = document.querySelectorAll('[id^="backBtn"]');
backBtns.forEach(btn => {
  btn.addEventListener('click', backToHome);
});

// ===================
// Initialize Application
// ===================
document.addEventListener("DOMContentLoaded", function() {
  console.log("Research Intelligence App initialized");
  
  // Load files if on upload page
  if (pages.upload && pages.upload.style.display !== 'none') {
    loadFilesFromServer();
  }
  
  // Initialize default analysis slide
  showAnalisisSlide('default');
});