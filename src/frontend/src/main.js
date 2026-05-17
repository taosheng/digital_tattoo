import './style.css';

document.querySelector('#app').innerHTML = `
  <div class="container">
    <div class="header-nav" style="position: absolute; top: 20px; right: 20px; z-index: 10; display: flex; align-items: center; gap: 15px;">
      <div class="static-links" style="display: flex; gap: 15px; font-size: 0.85em;">
        <a id="lnk-privacy" href="/privacy.html" style="color: rgba(255,255,255,0.6); text-decoration: none;">隱私權政策</a>
        <a id="lnk-terms-static" href="/terms.html" style="color: rgba(255,255,255,0.6); text-decoration: none;">服務條款</a>
        <a id="lnk-deletion" href="/deletion.html" style="color: rgba(255,255,255,0.6); text-decoration: none;">資料刪除</a>
      </div>
      <div class="lang-selector">
        <select id="lang-select" style="padding: 5px 10px; border-radius: 5px; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); outline: none; cursor: pointer;">
          <option value="zh" style="color: black;" selected>正體中文</option>
          <option value="en" style="color: black;">English</option>
        </select>
      </div>
    </div>
    <div id="login-view" class="glass-panel" style="margin-top: 40px; text-align: center;">
      <img src="/icon.svg" alt="Digital Tattoo Logo" style="width: 80px; height: 80px; margin-bottom: 10px; filter: drop-shadow(0 0 10px rgba(138,43,226,0.5));" />
      <h1 id="main-title" style="margin-top: 0;">數位刺青</h1>
      <p id="main-subtitle" style="text-align: center; color: var(--text-secondary); margin-bottom: 2rem;">
        你的資料刺進區塊鏈 永遠不會消失！
      </p>
      <div id="google-login-btn-container" style="display: flex; justify-content: center; min-height: 44px; margin-bottom: 1rem;"></div>
      <div id="fb-login-btn-container" style="display: flex; justify-content: center; min-height: 44px;">
        <button id="btn-fb-login" onclick="handleFacebookLogin()" style="background-color: #1877F2; color: white; border: none; border-radius: 22px; padding: 0 24px; height: 40px; font-weight: bold; display: flex; align-items: center; gap: 8px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
          <span id="lbl-fb-login">Facebook 登入</span>
        </button>
      </div>
      <div style="text-align: center; margin-top: 2rem;">
        <a id="lnk-terms-login" href="#" onclick="showTerms(event)" style="font-size: 0.85em; color: #ef4444;">服務條款 (Terms)</a>
      </div>
    </div>

    <div id="dashboard-view" class="hidden">
      <div class="glass-panel" style="margin-bottom: 2rem;">
        <div class="user-info" style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 15px;">
            <img src="/icon.svg" alt="Digital Tattoo Logo" style="width: 50px; height: 50px; filter: drop-shadow(0 0 5px rgba(138,43,226,0.5));" id="dashboard-logo" />
            <div>
              <h2 id="user-name" style="margin-top: 0;">Welcome!</h2>
            <p id="user-email" style="color: var(--text-secondary);"></p>
            <a id="lnk-what-is" href="https://www.5233.space/2026/05/tattoo.html" target="_blank" style="font-size: 0.9em; display: inline-block; margin-top: 5px;">什麼是數位刺青</a>
            <span style="font-size: 0.9em; color: var(--text-secondary); margin: 0 8px;">|</span>
            <a id="lnk-operate" href="https://github.com/taosheng/digital_tattoo/blob/main/find_your_tattoo_zh_TW.md" target="_blank" style="font-size: 0.9em; display: inline-block; margin-top: 5px;">自己操作區塊鏈</a>
            <span style="font-size: 0.9em; color: var(--text-secondary); margin: 0 8px;">|</span>
            <a id="lnk-add-points" href="#" onclick="showPointsInfo(event)" style="font-size: 0.9em; display: inline-block; margin-top: 5px;">如何增加點數?</a>
            <span style="font-size: 0.9em; color: var(--text-secondary); margin: 0 8px;">|</span>
            <a id="lnk-terms" href="#" onclick="showTerms(event)" style="font-size: 0.9em; display: inline-block; margin-top: 5px; color: #ef4444;">服務條款 (Terms)</a>
            </div>
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
            <div class="form-group" style="margin-bottom: 8px;">
              <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                <input type="checkbox" id="string-encrypt" />
                <span id="lbl-string-encrypt">加密刺青</span>
              </label>
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
            <div class="form-group" style="margin-bottom: 8px;">
              <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                <input type="checkbox" id="file-encrypt" />
                <span id="lbl-file-encrypt">加密刺青</span>
              </label>
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
         const langText = document.getElementById('lang-select').value;
         const typeBadgeText = langText === 'zh' ? '文字' : 'String';
         const fileBadgeText = langText === 'zh' ? '圖檔' : 'File';
         const typeBadge = t.type === 'string' 
           ? `<span class="badge string">${typeBadgeText}</span>` 
           : `<span class="badge file">${fileBadgeText}</span>`;
           
         const displayTitle = (t.type === 'string' 
           ? (t.preview || "String Tattoo " + t.tattoo_id)
           : (t.original_filename || t.filename || "File Tattoo " + t.tattoo_id)) + (t.is_encrypted ? " 🔒" : "");
           
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
         
         const txBtnText = langText === 'zh' ? "想要自己從區塊鏈下載" : "Download from Blockchain yourself";
         const sigsJson = t.signatures ? JSON.stringify(t.signatures).replace(/'/g, "\\'").replace(/"/g, "&quot;") : '[]';
         const blockchain = t.blockchain || 'solana';
         const txButton = (t.signatures && t.signatures.length > 0 && (!t.uploading_status || t.uploading_status === 'done'))
           ? `<button class="action-btn" onclick="showTransactions(${sigsJson}, event, '${blockchain}')" style="padding: 4px 8px; font-size: 0.8rem; background: rgba(139, 92, 246, 0.2); border: 1px solid rgba(139, 92, 246, 0.4); color: #111; border-radius: 4px; cursor: pointer;">${txBtnText}</button>`
           : '';

         const shareBtnText = langText === 'zh' ? "分享" : "Share";
         const shareButton = (!t.uploading_status || t.uploading_status === 'done')
           ? `<button class="action-btn" onclick="shareTattoo('${t.tattoo_id}', event)" style="padding: 4px 8px; font-size: 0.8rem; background: rgba(0, 210, 255, 0.2); border: 1px solid rgba(0, 210, 255, 0.4); color: #111; border-radius: 4px; cursor: pointer;">${shareBtnText}</button>`
           : '';

         if (t.type === 'string') {
             const btnText = langText === 'zh' ? "查看文字" : "View String";
             actionButtons = `
               <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; justify-content: flex-end;">
                   <button class="action-btn" onclick="downloadTattoo('${t.tattoo_id}', ${!!t.is_encrypted}, false, event)" style="padding: 4px 8px; font-size: 0.8rem; background: rgba(255,255,255,0.85); border: 1px solid var(--glass-border); color: #111; border-radius: 4px; cursor: pointer; font-weight: 500;">${btnText}</button>
                   ${txButton}
                   ${shareButton}
               </div>
             `;
         } else {
             const cacheBtnText = langText === 'zh' ? "下載檔案" : "Download File";
             actionButtons = `
               <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; justify-content: flex-end;">
                   <button class="action-btn" onclick="downloadTattoo('${t.tattoo_id}', ${!!t.is_encrypted}, false, event)" style="padding: 4px 8px; font-size: 0.8rem; background: rgba(255,255,255,0.85); border: 1px solid var(--glass-border); color: #111; border-radius: 4px; cursor: pointer; font-weight: 500;">${cacheBtnText}</button>
                   ${txButton}
                   ${shareButton}
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

window.downloadTattoo = async (id, isEncrypted = false, forceFallback = false, e = null) => {
  if(e) e.stopPropagation();
  const lang = document.getElementById('lang-select').value;
  
  let decryptionKey = null;
  if (isEncrypted) {
      const msg = lang === 'zh' ? "請輸入您的解密密碼:" : "Please enter your decryption key:";
      decryptionKey = prompt(msg);
      if (!decryptionKey) return; // User cancelled
  }
  
  if (forceFallback) {
    showOverlay(lang === 'zh' ? "正在從區塊鏈收集資料中，請耐心等候..." : "Gathering data from blockchain, please wait...");
  } else {
    showOverlay(lang === 'zh' ? "取得刺青資料中..." : "Retrieving tattoo data...");
  }
  
  try {
    let url = forceFallback ? `/api/tattoo/read/${id}?fallback_solana=true` : `/api/tattoo/read/${id}`;
    if (decryptionKey) {
        url += (url.includes('?') ? '&' : '?') + `decryption_key=${encodeURIComponent(decryptionKey)}`;
    }
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
               return window.downloadTattoo(id, isEncrypted, true);
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
      <div style="margin-bottom: 16px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px; border-left: 3px solid #8b5cf6; color: #ccc; font-size: 0.85rem;">
        ${lang === 'zh' ? '區塊鏈紀錄需要10~20分鐘 如果是剛刺上的請等20再查。<br/>若您的刺青有加密，請記得使用您的解密密碼解密。' : 'Blockchain records take 10-20 minutes. If you just tattooed, please wait 20 mins before checking.<br/>If your tattoo is encrypted, remember to decrypt it using your key.'}
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
  const isEncrypt = document.getElementById('string-encrypt').checked;
  
  showOverlay("Submitting String Tattoo...");
  try {
    const res = await fetch('/api/tattoo/string', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${window.sessionToken}`
      },
      body: JSON.stringify({ string_data: text, encrypt: isEncrypt })
    });
    const data = await res.json();
    if (res.ok) {
      if (data.encryption_key) {
        const msgKey = lang === 'zh' 
          ? `刺青上傳成功！\n\n【重要】這是您的解密密碼：\n${data.encryption_key}\n\n請務必妥善保存，遺失後將無法解密！` 
          : `Tattoo uploaded successfully!\n\n[IMPORTANT] Here is your decryption key:\n${data.encryption_key}\n\nPlease keep it safe, if lost you will NOT be able to decrypt!`;
        prompt(msgKey, data.encryption_key);
      } else {
        alert("String Tattoo uploaded successfully!");
      }
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
  const isEncrypt = document.getElementById('file-encrypt').checked;
  
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("encrypt", isEncrypt ? "true" : "false");
  
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
      if (data.encryption_key) {
        const msgKey = lang === 'zh' 
          ? `刺青上傳開始！\n\n【重要】這是您的解密密碼：\n${data.encryption_key}\n\n請務必妥善保存，遺失後將無法解密！` 
          : `Tattoo upload started!\n\n[IMPORTANT] Here is your decryption key:\n${data.encryption_key}\n\nPlease keep it safe, if lost you will NOT be able to decrypt!`;
        prompt(msgKey, data.encryption_key);
      }
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

function initFacebook() {
  if (window.FB) {
    console.log("Initializing Facebook SDK...");
    FB.init({
      appId: import.meta.env.VITE_FB_APP_ID || 'MISSING_FB_ID',
      cookie: true,
      xfbml: true,
      version: 'v19.0'
    });
    window.FB_INITIALIZED = true;
  } else {
    setTimeout(initFacebook, 100);
  }
}

window.handleFacebookLogin = () => {
  if (!window.FB || !window.FB_INITIALIZED) {
    alert("Facebook SDK is still initializing. Please try again in a few seconds.");
    return;
  }
  FB.login((response) => {
    if (response.authResponse) {
      const accessToken = response.authResponse.accessToken;
      sendFacebookToken(accessToken);
    } else {
      console.log('User cancelled login or did not fully authorize.');
    }
  }, { scope: 'email,public_profile' });
};

async function sendFacebookToken(token) {
  showOverlay("Authenticating with Facebook...");
  try {
    const res = await fetch('/api/auth/facebook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: token })
    });
    const data = await res.json();
    if (res.ok) {
      window.sessionToken = data.session_token;
      initDashboard(data.user);
    } else {
      alert("Facebook Authentication Failed: " + data.detail);
    }
  } catch (err) {
    alert("Network error.");
  } finally {
    hideOverlay();
  }
}

renderGoogleButton();
initFacebook();

// Language Selector Logic
document.getElementById('lang-select').addEventListener('change', (e) => {
  const lang = e.target.value;
  if (lang === 'zh') {
    document.getElementById('main-title').innerText = "數位刺青";
    document.getElementById('main-subtitle').innerText = "你的資料刺進區塊鏈 永遠不會消失！";
    if(document.getElementById('lnk-what-is')) document.getElementById('lnk-what-is').innerText = "什麼是數位刺青";
    if(document.getElementById('lnk-operate')) document.getElementById('lnk-operate').innerText = "自己操作區塊鏈";
    
    if(document.getElementById('lbl-create-string')) document.getElementById('lbl-create-string').innerText = "建立字串刺青";
    if(document.getElementById('lbl-string-msg')) document.getElementById('lbl-string-msg').innerText = "訊息 (最多 1000 字元)";
    if(document.getElementById('btn-string')) document.getElementById('btn-string').innerText = "刺進區塊鏈";
    
    if(document.getElementById('lbl-create-file')) document.getElementById('lbl-create-file').innerText = "建立圖像刺青";
    if(document.getElementById('lbl-file-msg')) document.getElementById('lbl-file-msg').innerText = "圖檔 (最大 10MB。圖片將自動壓縮)";
    if(document.getElementById('btn-file')) document.getElementById('btn-file').innerText = "刺進區塊鏈";
    
    if(document.getElementById('lbl-string-encrypt')) document.getElementById('lbl-string-encrypt').innerText = "加密刺青 (我們將隨機產生密碼)";
    if(document.getElementById('lbl-file-encrypt')) document.getElementById('lbl-file-encrypt').innerText = "加密刺青 (我們將隨機產生密碼)";
    
    if(document.getElementById('lbl-tattoos')) document.getElementById('lbl-tattoos').innerText = "你的刺青";
    if(document.getElementById('lbl-loading')) document.getElementById('lbl-loading').innerText = "載入中...";
    if(document.getElementById('lnk-add-points')) document.getElementById('lnk-add-points').innerText = "如何增加點數?";
    if(document.getElementById('lnk-terms')) document.getElementById('lnk-terms').innerText = "服務條款 (Terms)";
    if(document.getElementById('lnk-terms-login')) document.getElementById('lnk-terms-login').innerText = "服務條款 (Terms)";
    if(document.getElementById('lnk-privacy')) document.getElementById('lnk-privacy').innerText = "隱私權政策";
    if(document.getElementById('lnk-terms-static')) document.getElementById('lnk-terms-static').innerText = "服務條款";
    if(document.getElementById('lnk-deletion')) document.getElementById('lnk-deletion').innerText = "資料刪除";
    if(document.getElementById('lbl-fb-login')) document.getElementById('lbl-fb-login').innerText = "Facebook 登入";
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
    
    if(document.getElementById('lbl-string-encrypt')) document.getElementById('lbl-string-encrypt').innerText = "Encrypt Tattoo (We will generate a secure key)";
    if(document.getElementById('lbl-file-encrypt')) document.getElementById('lbl-file-encrypt').innerText = "Encrypt Tattoo (We will generate a secure key)";

    if(document.getElementById('lbl-tattoos')) document.getElementById('lbl-tattoos').innerText = "Your Tattoos";
    if(document.getElementById('lbl-loading')) document.getElementById('lbl-loading').innerText = "Loading tattoos...";
    if(document.getElementById('lnk-add-points')) document.getElementById('lnk-add-points').innerText = "How to add points?";
    if(document.getElementById('lnk-terms')) document.getElementById('lnk-terms').innerText = "Terms of Service";
    if(document.getElementById('lnk-terms-login')) document.getElementById('lnk-terms-login').innerText = "Terms of Service";
    if(document.getElementById('lnk-privacy')) document.getElementById('lnk-privacy').innerText = "Privacy Policy";
    if(document.getElementById('lnk-terms-static')) document.getElementById('lnk-terms-static').innerText = "Terms of Service";
    if(document.getElementById('lnk-deletion')) document.getElementById('lnk-deletion').innerText = "Data Deletion";
    if(document.getElementById('lbl-fb-login')) document.getElementById('lbl-fb-login').innerText = "Login with Facebook";
  }
  
  if (window.sessionToken) {
    loadTattoos();
  }
});

window.shareTattoo = async (id, e = null) => {
  if(e) e.stopPropagation();
  const lang = document.getElementById('lang-select').value;
  showOverlay(lang === 'zh' ? "產生分享連結中..." : "Generating share link...");
  
  try {
    const res = await fetch(`/api/tattoo/share/${id}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${window.sessionToken}` }
    });
    const data = await res.json();
    if (res.ok) {
        const shareUrl = `${window.location.origin}/tattoo/${data.share_key}`;
        const titleText = lang === 'zh' ? '分享你的刺青' : 'Share Your Tattoo';
        const closeText = lang === 'zh' ? '關閉' : 'Close';
        const copyText = lang === 'zh' ? '複製連結' : 'Copy Link';
        
        const fbShareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
        const xShareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(titleText)}`;
        const liShareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
        
        const modal = document.createElement('div');
        modal.id = 'share-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000;display:flex;align-items:center;justify-content:center;';
        modal.innerHTML = `
          <div style="background: var(--bg-dark, #1a1a2e); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 24px; max-width: 500px; width: 90%;">
            <h3 style="color: white; margin: 0 0 16px 0;">${titleText}</h3>
            <div style="display: flex; gap: 8px; margin-bottom: 16px;">
               <input type="text" id="share-link-input" value="${shareUrl}" readonly style="flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #ccc; background: rgba(255,255,255,0.9); color: black;" />
               <button onclick="navigator.clipboard.writeText(document.getElementById('share-link-input').value); alert('${lang === 'zh' ? '已複製！' : 'Copied!'}');" style="padding: 8px 16px; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border: none; border-radius: 6px; cursor: pointer; white-space: nowrap;">${copyText}</button>
            </div>
            
            <div style="display: flex; gap: 8px; margin-bottom: 24px; justify-content: center; flex-wrap: wrap;">
                <a href="${fbShareUrl}" target="_blank" style="padding: 8px 16px; background: #1877F2; color: white; border-radius: 6px; text-decoration: none; font-weight: bold; flex: 1; text-align: center; min-width: 100px;">Facebook</a>
                <a href="${xShareUrl}" target="_blank" style="padding: 8px 16px; background: #000000; color: white; border-radius: 6px; text-decoration: none; font-weight: bold; flex: 1; text-align: center; min-width: 100px;">X (Twitter)</a>
                <a href="${liShareUrl}" target="_blank" style="padding: 8px 16px; background: #0A66C2; color: white; border-radius: 6px; text-decoration: none; font-weight: bold; flex: 1; text-align: center; min-width: 100px;">LinkedIn</a>
            </div>
            
            <div style="text-align: right;">
              <button onclick="document.getElementById('share-modal').remove()" style="padding: 6px 16px; background: rgba(139,92,246,0.3); border: 1px solid rgba(139,92,246,0.5); color: white; border-radius: 6px; cursor: pointer;">${closeText}</button>
            </div>
          </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (ev) => { if(ev.target === modal) modal.remove(); });
    } else {
        alert("Error: " + data.detail);
    }
  } catch (err) {
    alert("Network error.");
  } finally {
    hideOverlay();
  }
};

window.showPointsInfo = (e) => {
  if (e) e.preventDefault();
  const lang = document.getElementById('lang-select').value;
  const closeText = lang === 'zh' ? '關閉' : 'Close';
  const titleText = lang === 'zh' ? '如何增加點數?' : 'How to add points?';
  const descText = lang === 'zh' 
    ? '試營運期間 如果需要購買額外點數<br/>請 email 給' 
    : 'During the trial period, if you need to purchase extra points,<br/>please email to';

  const existing = document.getElementById('points-info-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'points-info-modal';
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000;display:flex;align-items:center;justify-content:center;';
  modal.innerHTML = `
    <div style="background: var(--bg-dark, #1a1a2e); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 28px; max-width: 420px; width: 90%;">
      <h3 style="color: white; margin: 0 0 16px 0;">${titleText}</h3>
      <p style="color: rgba(255,255,255,0.85); line-height: 1.8; margin: 0 0 20px 0;">
        ${descText}
        <br/>
        <a href="mailto:saltycatchen@gmail.com" style="color: #00d2ff; font-weight: bold;">saltycatchen@gmail.com</a>
      </p>
      <div style="text-align: right;">
        <button onclick="document.getElementById('points-info-modal').remove()" style="padding: 6px 16px; background: rgba(139,92,246,0.3); border: 1px solid rgba(139,92,246,0.5); color: white; border-radius: 6px; cursor: pointer;">${closeText}</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (ev) => { if (ev.target === modal) modal.remove(); });
};

window.showTerms = (e) => {
  if (e) e.preventDefault();
  const lang = document.getElementById('lang-select').value;
  const closeText = lang === 'zh' ? '關閉' : 'Close';
  const titleText = lang === 'zh' ? '服務條款與免責聲明' : 'Terms of Service & Disclaimer';
  const termsHtml = lang === 'zh' 
    ? `<ul style="padding-left: 20px; line-height: 1.8; color: rgba(255,255,255,0.85); font-size: 0.95rem;">
        <li style="margin-bottom: 12px;"><strong>資料所有權：</strong>本網站 (tt.saltycat.tw) <strong>不擁有</strong>您上傳的文字或檔案。所有資料一旦上傳，將永久寫入區塊鏈。</li>
        <li style="margin-bottom: 12px;"><strong>免責聲明：</strong>一旦資料寫入區塊鏈，本網站對該資料<strong>不承擔任何法律責任</strong>。使用者須為其上傳之內容負擔全責。</li>
        <li style="margin-bottom: 12px;"><strong>資料保管：</strong>我們<strong>不負責長期保存您的資料</strong>。本網站僅為一項工具服務，提供上傳、加密與產生分享連結的便利介面，協助您更方便地讀寫區塊鏈資料。</li>
        <li style="margin-bottom: 12px;"><strong>不可刪除性：</strong>區塊鏈具有不可篡改性，我們<strong>絕對無法協助您刪除或修改</strong>任何已上傳至區塊鏈的資料。請於上傳前謹慎確認。</li>
      </ul>`
    : `<ul style="padding-left: 20px; line-height: 1.8; color: rgba(255,255,255,0.85); font-size: 0.95rem;">
        <li style="margin-bottom: 12px;"><strong>Data Ownership:</strong> This website (tt.saltycat.tw) <strong>does NOT own</strong> your uploaded strings or files. All data is permanently written to the blockchain.</li>
        <li style="margin-bottom: 12px;"><strong>Disclaimer of Liability:</strong> We take <strong>NO legal responsibility</strong> for the content once it is uploaded to the blockchain. Users are solely responsible for their uploads.</li>
        <li style="margin-bottom: 12px;"><strong>Data Retention:</strong> We <strong>do NOT hold responsibility for keeping your data</strong>. We solely provide tools and an interface for uploading, encrypting, and sharing to help you easily interact with the blockchain.</li>
        <li style="margin-bottom: 12px;"><strong>Immutability:</strong> The blockchain is immutable. We <strong>CANNOT and WILL NOT help you remove or modify</strong> any data once it is on the blockchain. Please upload carefully.</li>
      </ul>`;

  const existing = document.getElementById('terms-info-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'terms-info-modal';
  modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.75);z-index:1000;display:flex;align-items:center;justify-content:center;';
  modal.innerHTML = `
    <div style="background: var(--bg-dark, #1a1a2e); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 28px; max-width: 550px; width: 90%; max-height: 85vh; overflow-y: auto;">
      <h3 style="color: #ef4444; margin: 0 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px;">${titleText}</h3>
      ${termsHtml}
      <div style="text-align: right; margin-top: 24px;">
        <button onclick="document.getElementById('terms-info-modal').remove()" style="padding: 8px 24px; background: rgba(139,92,246,0.3); border: 1px solid rgba(139,92,246,0.5); color: white; border-radius: 6px; cursor: pointer; font-weight: bold;">${closeText}</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', (ev) => { if (ev.target === modal) modal.remove(); });
};

