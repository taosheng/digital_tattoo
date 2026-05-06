import './style.css';

document.querySelector('#app').innerHTML = `
  <div class="container">
    <div class="lang-selector" style="position: absolute; top: 20px; right: 20px; z-index: 10;">
      <select id="lang-select" style="padding: 5px 10px; border-radius: 5px; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); outline: none; cursor: pointer;">
        <option value="zh" style="color: black;" selected>正體中文</option>
        <option value="en" style="color: black;">English</option>
      </select>
    </div>
    <div id="login-view" class="glass-panel" style="margin-top: 40px;">
      <h1 id="main-title">數位刺青</h1>
      <p id="main-subtitle" style="text-align: center; color: var(--text-secondary); margin-bottom: 2rem;">
        你的資料刺進區塊鏈 永遠不會消失在！
      </p>
      <div id="google-login-btn-container" style="display: flex; justify-content: center; min-height: 44px;"></div>
    </div>

    <div id="dashboard-view" class="hidden">
      <div class="glass-panel" style="margin-bottom: 2rem;">
        <div class="user-info">
          <div>
            <h2 id="user-name">Welcome!</h2>
            <p id="user-email" style="color: var(--text-secondary);"></p>
            <a id="lnk-what-is" href="https://www.5233.space/2026/05/tattoo.html" target="_blank" style="font-size: 0.9em; display: inline-block; margin-top: 5px;">什麼是數位刺青</a>
            <span style="font-size: 0.9em; color: var(--text-secondary); margin: 0 8px;">|</span>
            <a id="lnk-operate" href="https://github.com/taosheng/digital_tattoo/blob/main/find_your_tattoo_zh_TW.md" target="_blank" style="font-size: 0.9em; display: inline-block; margin-top: 5px;">自己操作區塊鏈</a>
          </div>
          <div class="points-badge">
            <span id="user-points">0</span> Points
          </div>
        </div>
      </div>
      
      <div class="dashboard-grid">
        <!-- String Tattoo -->
        <div class="glass-panel">
          <h2 id="lbl-create-string">建立字串刺青</h2>
          <form id="string-form">
            <div class="form-group">
              <label id="lbl-string-msg">訊息 (最多 500 字元)</label>
              <textarea id="string-input" rows="4" maxlength="500" required></textarea>
            </div>
            <button type="submit" id="btn-string">刺進區塊鏈</button>
          </form>
        </div>

        <!-- File Tattoo -->
        <div class="glass-panel">
          <h2 id="lbl-create-file">建立檔案刺青</h2>
          <form id="file-form">
            <div class="form-group">
              <label id="lbl-file-msg">檔案 (最大 2MB。圖片將自動壓縮)</label>
              <input type="file" id="file-input" required />
            </div>
            <button type="submit" id="btn-file">刺進區塊鏈</button>
          </form>
        </div>
      </div>

      <div class="glass-panel">
         <h2 id="lbl-tattoos">你的刺青</h2>
         <div id="tattoo-list" class="tattoo-list">
            <p id="lbl-loading" style="color: var(--text-secondary)">載入中...</p>
         </div>
      </div>
    </div>
  </div>

  <div id="overlay" class="hidden">
    <div class="loader" style="width: 50px; height: 50px; border-width: 5px; margin-bottom: 1rem;"></div>
    <h3 id="overlay-text">Processing on Blockchain... Please wait.</h3>
  </div>
`;

window.sessionToken = null;

window.handleCredentialResponse = async (response) => {
  const jwt = response.credential;
  showOverlay("Authenticating...");
  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: jwt })
    });
    const data = await res.json();
    if (res.ok) {
      window.sessionToken = data.session_token; // we'll use simple bearer for state
      initDashboard(data.user);
    } else {
      alert("Authentication Failed: " + data.detail);
    }
  } catch (err) {
    alert("Network error.");
  } finally {
    hideOverlay();
  }
};

async function initDashboard(user) {
  document.getElementById('login-view').classList.add('hidden');
  document.getElementById('dashboard-view').classList.remove('hidden');
  document.getElementById('user-name').innerText = `Welcome ${user.name}!`;
  document.getElementById('user-email').innerText = user.email;
  document.getElementById('user-points').innerText = user.points;
  
  loadTattoos();
}

async function loadTattoos() {
  const listEl = document.getElementById('tattoo-list');
  try {
    const res = await fetch('/api/tattoo/list', {
      headers: { 'Authorization': `Bearer ${window.sessionToken}` }
    });
    const data = await res.json();
    if (res.ok) {
       listEl.innerHTML = '';
       if (data.tattoos.length === 0) {
         listEl.innerHTML = '<p style="color: var(--text-secondary)">No tattoos found.</p>';
       }
       let hasActiveUpload = false;
       data.tattoos.forEach(t => {
         const item = document.createElement('div');
         item.className = 'tattoo-item';
         const typeBadge = t.type === 'string' 
           ? '<span class="badge string">STRING</span>' 
           : '<span class="badge file">FILE</span>';
           
         const displayTitle = t.type === 'string' 
           ? (t.preview || "String Tattoo " + t.tattoo_id)
           : (t.original_filename || t.filename || "File Tattoo " + t.tattoo_id);
           
         let statusHtml = '';
         if (t.uploading_status && t.uploading_status !== 'done') {
             if (!t.uploading_status.startsWith('error')) {
                 hasActiveUpload = true;
                 statusHtml = `<br/><span style="color: #d97706; font-size: 0.85rem; font-weight: bold;">Status: ${t.uploading_status}...</span>`;
             } else {
                 statusHtml = `<br/><span style="color: #ef4444; font-size: 0.85rem; font-weight: bold;">Failed: ${t.uploading_status}</span>`;
             }
         }
           
         item.innerHTML = `
           <div style="cursor: pointer; width: 100%;" onclick="downloadTattoo('${t.tattoo_id}')">
             ${typeBadge} 
             <strong style="margin-left: 0.5rem;">${displayTitle}</strong>
             ${statusHtml}
             <br/>
             <small style="color: var(--text-secondary)">${new Date(t.timestamp).toLocaleString()}</small>
           </div>
         `;
         listEl.appendChild(item);
       });
       
       const fileInput = document.getElementById('file-input');
       const btnFile = document.getElementById('btn-file');
       const lang = document.getElementById('lang-select').value;
       if (hasActiveUpload) {
           fileInput.disabled = true;
           btnFile.disabled = true;
           btnFile.innerText = lang === 'zh' ? "上傳中... 請查看下方進度" : "Uploading... Check list below";
           if (!window.pollInterval) {
               window.pollInterval = setInterval(loadTattoos, 5000);
           }
       } else {
           fileInput.disabled = false;
           btnFile.disabled = false;
           btnFile.innerText = lang === 'zh' ? "刺進區塊鏈" : "Tattoo to Blockchain";
           if (window.pollInterval) {
               clearInterval(window.pollInterval);
               window.pollInterval = null;
           }
       }
    }
  } catch (e) {
    console.error(e);
  }
}

window.downloadTattoo = async (id, forceFallback = false) => {
  if (forceFallback) {
    showOverlay("Gathering from blockchain... This will take a few minutes.");
  } else {
    showOverlay("Retrieving tattoo data...");
  }
  
  try {
    const url = forceFallback ? `/api/tattoo/read/${id}?fallback_solana=true` : `/api/tattoo/read/${id}`;
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${window.sessionToken}` }
    });
    
    if (res.status === 202) {
       const data = await res.json();
       if (data.fallback_needed) {
           const lang = document.getElementById('lang-select').value;
           const msg = lang === 'zh' 
             ? "VaultSage 備份不存在。將從 Solana 區塊鏈上收集所有資料，這可能需要幾分鐘的時間。確定要繼續嗎？"
             : "VaultSage backup not found. The system will gather all chunks directly from the Solana blockchain. This may take a few minutes. Continue?";
           if (confirm(msg)) {
               return window.downloadTattoo(id, true);
           } else {
               hideOverlay();
               return;
           }
       }
    }
    
    const contentType = res.headers.get("Content-Type");
    if (contentType && contentType.includes("application/json")) {
        const data = await res.json();
        if (res.ok && data.type === 'string') {
            alert("Tattoo String: \n\n" + data.content);
        } else {
            alert("Error: " + data.detail);
        }
    } else {
        if (res.ok) {
            const blob = await res.blob();
            const disposition = res.headers.get("content-disposition");
            let filename = "downloaded_tattoo";
            if (disposition && disposition.indexOf('filename=') !== -1) {
                const parts = disposition.split('filename=');
                filename = parts[1].replace(/["']/g, ""); 
            }
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } else {
            alert("File retrieval failed.");
        }
    }
  } catch(e) {
    alert("Network error.");
  } finally {
    hideOverlay();
  }
};

// Event Listeners
document.getElementById('string-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const lang = document.getElementById('lang-select').value;
  const msg = lang === 'zh' 
    ? "你確定嗎？一旦確認，刺青將永遠存在於區塊鏈上，且無法消失！" 
    : "Are you sure? Once you confirm, the tattoo will NEVER disappear! It will be there forever.";
  if (!confirm(msg)) return;

  const text = document.getElementById('string-input').value;
  
  showOverlay("Submitting String Tattoo...");
  try {
    const res = await fetch('/api/tattoo/string', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${window.sessionToken}`
      },
      body: JSON.stringify({ string_data: text })
    });
    const data = await res.json();
    if (res.ok) {
      alert("String Tattoo uploaded successfully!");
      document.getElementById('user-points').innerText = data.new_points;
      document.getElementById('string-form').reset();
      loadTattoos();
    } else {
      alert("Error: " + data.detail);
    }
  } catch (err) {
    alert("Network error.");
  } finally {
    hideOverlay();
  }
});

document.getElementById('file-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const lang = document.getElementById('lang-select').value;
  const msg = lang === 'zh' 
    ? "你確定嗎？一旦確認，刺青將永遠存在於區塊鏈上，且無法消失！" 
    : "Are you sure? Once you confirm, the tattoo will NEVER disappear! It will be there forever.";
  if (!confirm(msg)) return;

  const fileInput = document.getElementById('file-input');
  if (fileInput.files.length === 0) return;
  
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  
  showOverlay("Starting File Upload...");
  try {
    const res = await fetch('/api/tattoo/file', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${window.sessionToken}`
      },
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById('user-points').innerText = data.new_points;
      document.getElementById('file-form').reset();
      loadTattoos();
    } else {
      alert("Error: " + data.detail);
    }
  } catch (err) {
    alert("Network error.");
  } finally {
    hideOverlay();
  }
});

function showOverlay(text) {
  document.getElementById('overlay-text').innerText = text;
  document.getElementById('overlay').classList.remove('hidden');
}

function hideOverlay() {
  document.getElementById('overlay').classList.add('hidden');
}

// Initialize Google Sign-in Button using JS API
function renderGoogleButton() {
  if (window.google && window.google.accounts) {
    google.accounts.id.initialize({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || 'MISSING_CLIENT_ID',
      callback: window.handleCredentialResponse
    });
    google.accounts.id.renderButton(
      document.getElementById("google-login-btn-container"),
      { theme: "outline", size: "large", shape: "pill", type: "standard" }
    );
  } else {
    // If google script is not loaded yet, retry in 100ms
    setTimeout(renderGoogleButton, 100);
  }
}

renderGoogleButton();

// Language Selector Logic
document.getElementById('lang-select').addEventListener('change', (e) => {
  const lang = e.target.value;
  if (lang === 'zh') {
    document.getElementById('main-title').innerText = "數位刺青";
    document.getElementById('main-subtitle').innerText = "你的資料刺進區塊鏈 永遠不會消失在！";
    if(document.getElementById('lnk-what-is')) document.getElementById('lnk-what-is').innerText = "什麼是數位刺青";
    if(document.getElementById('lnk-operate')) document.getElementById('lnk-operate').innerText = "自己操作區塊鏈";
    
    if(document.getElementById('lbl-create-string')) document.getElementById('lbl-create-string').innerText = "建立字串刺青";
    if(document.getElementById('lbl-string-msg')) document.getElementById('lbl-string-msg').innerText = "訊息 (最多 500 字元)";
    if(document.getElementById('btn-string')) document.getElementById('btn-string').innerText = "刺進區塊鏈";
    
    if(document.getElementById('lbl-create-file')) document.getElementById('lbl-create-file').innerText = "建立檔案刺青";
    if(document.getElementById('lbl-file-msg')) document.getElementById('lbl-file-msg').innerText = "檔案 (最大 2MB。圖片將自動壓縮)";
    if(document.getElementById('btn-file')) document.getElementById('btn-file').innerText = "刺進區塊鏈";
    
    if(document.getElementById('lbl-tattoos')) document.getElementById('lbl-tattoos').innerText = "你的刺青";
    if(document.getElementById('lbl-loading')) document.getElementById('lbl-loading').innerText = "載入中...";
  } else {
    document.getElementById('main-title').innerText = "Digital Tattoo";
    document.getElementById('main-subtitle').innerText = "Permanently immortalize your data on the Blockchain.";
    if(document.getElementById('lnk-what-is')) document.getElementById('lnk-what-is').innerText = "what is digital tattoo";
    if(document.getElementById('lnk-operate')) document.getElementById('lnk-operate').innerText = "operate Blockchain";
    
    if(document.getElementById('lbl-create-string')) document.getElementById('lbl-create-string').innerText = "Create String Tattoo";
    if(document.getElementById('lbl-string-msg')) document.getElementById('lbl-string-msg').innerText = "Message (Max 500 characters)";
    if(document.getElementById('btn-string')) document.getElementById('btn-string').innerText = "Tattoo to Blockchain";
    
    if(document.getElementById('lbl-create-file')) document.getElementById('lbl-create-file').innerText = "Create File Tattoo";
    if(document.getElementById('lbl-file-msg')) document.getElementById('lbl-file-msg').innerText = "File (Max 2MB. Images auto-compressed)";
    if(document.getElementById('btn-file')) document.getElementById('btn-file').innerText = "Tattoo to Blockchain";
    
    if(document.getElementById('lbl-tattoos')) document.getElementById('lbl-tattoos').innerText = "Your Tattoos";
    if(document.getElementById('lbl-loading')) document.getElementById('lbl-loading').innerText = "Loading tattoos...";
  }
});
