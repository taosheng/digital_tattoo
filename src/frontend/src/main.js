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
              <label id="lbl-string-msg">訊息 (最多 1000 字元)</label>
              <textarea id="string-input" rows="4" maxlength="1000" required></textarea>
            </div>
            <button type="submit" id="btn-string">刺進區塊鏈</button>
          </form>
        </div>

        <!-- File Tattoo -->
        <div class="glass-panel">
          <h2 id="lbl-create-file">建立圖像刺青</h2>
          <form id="file-form">
            <div class="form-group">
              <label id="lbl-file-msg">圖檔 (最大 10MB。圖片將自動壓縮)</label>
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
           ? '<span class="badge string">文字</span>' 
           : '<span class="badge file">圖檔</span>';
           
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
           
         let actionButtons = '';
         const langText = document.getElementById('lang-select').value;
         
         const txBtnText = langText === 'zh' ? "想要自己從區塊鏈下載" : "Download from Blockchain yourself";
         const sigsJson = t.signatures ? JSON.stringify(t.signatures).replace(/'/g, "\\'").replace(/"/g, "&quot;") : '[]';
         const blockchain = t.blockchain || 'solana';
         const txButton = (t.signatures && t.signatures.length > 0 && (!t.uploading_status || t.uploading_status === 'done'))
           ? `<button class="action-btn" onclick="showTransactions(${sigsJson}, event, '${blockchain}')" style="padding: 4px 8px; font-size: 0.8rem; background: rgba(139, 92, 246, 0.2); border: 1px solid rgba(139, 92, 246, 0.4); color: white; border-radius: 4px; cursor: pointer;">${txBtnText}</button>`
           : '';

         if (t.type === 'string') {
             const btnText = langText === 'zh' ? "查看文字" : "View String";
             actionButtons = `
               <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                   <button class="action-btn" onclick="downloadTattoo('${t.tattoo_id}', false, event)" style="padding: 4px 8px; font-size: 0.8rem; background: rgba(255,255,255,0.85); border: 1px solid var(--glass-border); color: #111; border-radius: 4px; cursor: pointer; font-weight: 500;">${btnText}</button>
                   ${txButton}
               </div>
             `;
         } else {
             const cacheBtnText = langText === 'zh' ? "下載檔案" : "Download File";
             actionButtons = `
               <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                   <button class="action-btn" onclick="downloadTattoo('${t.tattoo_id}', false, event)" style="padding: 4px 8px; font-size: 0.8rem; background: rgba(255,255,255,0.85); border: 1px solid var(--glass-border); color: #111; border-radius: 4px; cursor: pointer; font-weight: 500;">${cacheBtnText}</button>
                   ${txButton}
               </div>
             `;
         }

         item.innerHTML = `
           <div style="width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 12px;">
             <div style="flex: 1; min-width: 0;">
               ${typeBadge} 
               <strong style="margin-left: 0.5rem;">${displayTitle}</strong>
               ${statusHtml}
               <br/>
               <small style="color: var(--text-secondary)">${new Date(t.timestamp).toLocaleString()}</small>
             </div>
             ${actionButtons}
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

window.downloadTattoo = async (id, forceFallback = false, e = null) => {
  if(e) e.stopPropagation();
  const lang = document.getElementById('lang-select').value;
  if (forceFallback) {
    showOverlay(lang === 'zh' ? "正在從區塊鏈收集資料中，請耐心等候..." : "Gathering data from blockchain, please wait...");
  } else {
    showOverlay(lang === 'zh' ? "取得刺青資料中..." : "Retrieving tattoo data...");
  }
  
  try {
    const url = forceFallback ? `/api/tattoo/read/${id}?fallback_solana=true` : `/api/tattoo/read/${id}`;
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${window.sessionToken}` }
    });
    
    if (res.status === 202) {
       const data = await res.json();
       if (data.fallback_needed) {
           hideOverlay();
           const msg = lang === 'zh' 
             ? "這需要數十分鐘的時間，確定要繼續嗎？"
             : "This will take several minutes. Are you sure you want to continue?";
           if (confirm(msg)) {
               return window.downloadTattoo(id, true);
           } else {
               return;
           }
       }
    }
    
    const contentType = res.headers.get("Content-Type");
    if (contentType && contentType.includes("application/json")) {
         const data = await res.json();
         if (res.ok && data.type === 'string') {
             if (data.pending) {
                 const lang = document.getElementById('lang-select').value;
                 const pendingMsg = lang === 'zh'
                   ? "交易尚未完成，請稍候幾分鐘後再試。"
                   : "Transaction is still being confirmed. Please try again in a few minutes.";
                 alert(pendingMsg);
             } else {
                 alert("Tattoo String: \n\n" + data.content);
             }
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
            const blobUrl = window.URL.createObjectURL(blob);
            const lang = document.getElementById('lang-select').value;
            const closeText = lang === 'zh' ? '關閉' : 'Close';
            const saveText = lang === 'zh' ? '儲存檔案' : 'Save File';
            
            const modal = document.createElement('div');
            modal.id = 'img-preview-modal';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:1000;display:flex;align-items:center;justify-content:center;';
            modal.innerHTML = `
              <div style="background: var(--bg-dark, #1a1a2e); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 24px; max-width: 90vw; max-height: 90vh; display: flex; flex-direction: column; align-items: center; gap: 16px;">
                <img src="${blobUrl}" style="max-width: 80vw; max-height: 65vh; object-fit: contain; border-radius: 8px;" alt="${filename}" />
                <div style="color: var(--text-secondary, #999); font-size: 0.85rem;">${filename}</div>
                <div style="display: flex; gap: 12px;">
                  <a href="${blobUrl}" download="${filename}" style="padding: 6px 16px; background: rgba(139,92,246,0.3); border: 1px solid rgba(139,92,246,0.5); color: white; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.9rem;">${saveText}</a>
                  <button onclick="document.getElementById('img-preview-modal').remove()" style="padding: 6px 16px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; border-radius: 6px; cursor: pointer;">${closeText}</button>
                </div>
              </div>
            `;
            document.body.appendChild(modal);
            modal.addEventListener('click', (ev) => { if(ev.target === modal) modal.remove(); });
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

window.showTransactions = (sigs, e = null, bc = 'solana') => {
  if(e) e.stopPropagation();
  const lang = document.getElementById('lang-select').value;
  const title = lang === 'zh' ? '區塊鏈交易紀錄' : 'Blockchain Transactions';
  const closeText = lang === 'zh' ? '關閉' : 'Close';
  const tutorialText = lang === 'zh' ? '如何在區塊鏈組合出自己的刺青檔案' : 'How to assemble your tattoo file from blockchain';
  const parsed = typeof sigs === 'string' ? JSON.parse(sigs) : sigs;
  const blockchain = typeof bc !== 'undefined' ? bc : 'solana';
  
  const linksHtml = parsed.map((sig, i) => {
    const shortSig = sig.substring(0, 16) + '...' + sig.substring(sig.length - 8);
    const explorerUrl = blockchain === 'arweave'
      ? `https://viewblock.io/arweave/tx/${sig}`
      : `https://explorer.solana.com/tx/${sig}?cluster=devnet`;
    return `<div style="margin: 6px 0;">
      <span style="color: var(--text-secondary); font-size: 0.85rem;">#${i+1}</span>
      <a href="${explorerUrl}" target="_blank" 
         style="margin-left: 8px; color: #8b5cf6; word-break: break-all; font-size: 0.85rem;">${shortSig}</a>
    </div>`;
  }).join('');
  
  const modal = document.createElement('div');
  modal.id = 'tx-modal';
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000;display:flex;align-items:center;justify-content:center;';
  modal.innerHTML = `
    <div style="background: var(--bg-dark, #1a1a2e); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 24px; max-width: 500px; width: 90%; max-height: 70vh; overflow-y: auto;">
      <h3 style="color: white; margin: 0 0 16px 0;">${title} (${parsed.length})</h3>
      <div style="margin-bottom: 16px;">
        <a href="https://github.com/taosheng/digital_tattoo/blob/main/find_your_tattoo_zh_TW.md" target="_blank" style="color: #8b5cf6; font-size: 0.9rem;">${tutorialText}</a>
      </div>
      ${linksHtml}
      <div style="margin-top: 16px; text-align: right;">
        <button onclick="document.getElementById('tx-modal').remove()" style="padding: 6px 16px; background: rgba(139,92,246,0.3); border: 1px solid rgba(139,92,246,0.5); color: white; border-radius: 6px; cursor: pointer;">${closeText}</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (ev) => { if(ev.target === modal) modal.remove(); });
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
    if(document.getElementById('lbl-string-msg')) document.getElementById('lbl-string-msg').innerText = "訊息 (最多 1000 字元)";
    if(document.getElementById('btn-string')) document.getElementById('btn-string').innerText = "刺進區塊鏈";
    
    if(document.getElementById('lbl-create-file')) document.getElementById('lbl-create-file').innerText = "建立圖像刺青";
    if(document.getElementById('lbl-file-msg')) document.getElementById('lbl-file-msg').innerText = "圖檔 (最大 10MB。圖片將自動壓縮)";
    if(document.getElementById('btn-file')) document.getElementById('btn-file').innerText = "刺進區塊鏈";
    
    if(document.getElementById('lbl-tattoos')) document.getElementById('lbl-tattoos').innerText = "你的刺青";
    if(document.getElementById('lbl-loading')) document.getElementById('lbl-loading').innerText = "載入中...";
  } else {
    document.getElementById('main-title').innerText = "Digital Tattoo";
    document.getElementById('main-subtitle').innerText = "Permanently immortalize your data on the Blockchain.";
    if(document.getElementById('lnk-what-is')) document.getElementById('lnk-what-is').innerText = "what is digital tattoo";
    if(document.getElementById('lnk-operate')) document.getElementById('lnk-operate').innerText = "operate Blockchain";
    
    if(document.getElementById('lbl-create-string')) document.getElementById('lbl-create-string').innerText = "Create String Tattoo";
    if(document.getElementById('lbl-string-msg')) document.getElementById('lbl-string-msg').innerText = "Message (Max 1000 characters)";
    if(document.getElementById('btn-string')) document.getElementById('btn-string').innerText = "Tattoo to Blockchain";
    
    if(document.getElementById('lbl-create-file')) document.getElementById('lbl-create-file').innerText = "Create File Tattoo";
    if(document.getElementById('lbl-file-msg')) document.getElementById('lbl-file-msg').innerText = "File (Max 10MB. Images auto-compressed)";
    if(document.getElementById('btn-file')) document.getElementById('btn-file').innerText = "Tattoo to Blockchain";
    
    if(document.getElementById('lbl-tattoos')) document.getElementById('lbl-tattoos').innerText = "Your Tattoos";
    if(document.getElementById('lbl-loading')) document.getElementById('lbl-loading').innerText = "Loading tattoos...";
  }
});
