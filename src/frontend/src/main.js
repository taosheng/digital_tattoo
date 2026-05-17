import './style.css';

document.querySelector('#app').innerHTML = `
  <div class="container">
    <div class="header-nav" style="position: absolute; top: 20px; right: 20px; z-index: 10; display: flex; align-items: center; gap: 15px;">
      <div class="static-links" style="display: flex; gap: 15px; font-size: 0.85em;">
        <a id="lnk-privacy" href="/privacy.html" style="color: #003366; font-weight: 600; text-decoration: none;">隱私權政策</a>
        <a id="lnk-terms-static" href="/terms.html" style="color: #003366; font-weight: 600; text-decoration: none;">服務條款</a>
        <a id="lnk-deletion" href="/deletion.html" style="color: #003366; font-weight: 600; text-decoration: none;">資料刪除</a>
      </div>
      <div class="lang-selector">
        <select id="lang-select" style="padding: 5px 10px; border-radius: 5px; background: rgba(255,255,255,0.7); color: #003366; font-weight: 600; border: 1px solid #003366; outline: none; cursor: pointer;">
          <option value="zh" style="color: black;" selected>正體中文</option>
          <option value="en" style="color: black;">English</option>
        </select>
      </div>
    </div>
    <div id="login-view" class="glass-panel" style="margin-top: 40px; text-align: center;">
      <img src="/icon.svg" alt="Digital Tool Logo" style="width: 80px; height: 80px; margin-bottom: 10px; filter: drop-shadow(0 0 10px rgba(138,43,226,0.5));" />
      <h1 id="main-title" style="margin-top: 0;">數位小工具</h1>
      <p id="main-subtitle" style="text-align: center; color: var(--text-secondary); margin-bottom: 2rem;">
        實用的區塊鏈與 AI 工具集合！
      </p>
      <div id="google-login-btn-container" style="display: flex; justify-content: center; min-height: 44px; margin-bottom: 1rem;"></div>
      <div id="line-login-btn-container" style="display: flex; justify-content: center; min-height: 44px;">
        <button id="btn-line-login" onclick="handleLineLogin()" style="background-color: #06C755; color: white; border: none; border-radius: 22px; padding: 0 24px; height: 40px; font-weight: bold; display: flex; align-items: center; gap: 8px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M24 10.304c0-5.369-5.383-9.738-12-9.738S0 4.935 0 10.304c0 4.814 4.269 8.846 10.036 9.608.391.084.922.258 1.057.592.121.298.079.76.038 1.054-.04.288-.242 1.458-.295 1.748-.09.493-.424 2.11 1.854 1.155 2.278-.955 12.28-7.227 12.28-14.157zm-14.887 2.196h-2.22V8.406c0-.435.352-.787.787-.787s.787.352.787.787v3.307h1.434c.435 0 .787.352.787.787s-.352.787-.787.787zm3.178 0h-1.574c-.435 0-.787-.352-.787-.787V8.406c0-.435.352-.787.787-.787s.787.352.787.787v3.307c0 .435-.352.787-.787.787zm5.556 0h-1.554l-1.92-2.58v2.58c0 .435-.352.787-.787.787s-.787-.352-.787-.787V8.406c0-.435.352-.787.787-.787.322 0 .61.194.728.49l1.96 2.628V8.406c0-.435.352-.787.787-.787s.787.352.787.787v3.307c0 .435-.352.787-.787.787zm4.275-3.307h-2.22v.72h2.22c.435 0 .787.352.787.787s-.352.787-.787.787h-2.22v.998h2.22c.435 0 .787.352.787.787s-.352.787-.787.787h-3.007c-.435 0-.787-.352-.787-.787V8.406c0-.435.352-.787.787-.787h3.007c.435 0 .787.352.787.787s-.352.787-.787.787z"/></svg>
          <span id="lbl-line-login">LINE 登入</span>
        </button>
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
            </div>
          </div>
          <div class="points-badge">
            <span id="user-points">0</span> Points
          </div>
        </div>
      </div>
      
      <div class="tabs-nav" style="display: flex; gap: 10px; margin-bottom: 2rem;">
        <button id="tab-btn-tattoo" class="tab-btn active" onclick="switchTab('tattoo')">數位刺青 (Digital Tattoo)</button>
        <button id="tab-btn-merge" class="tab-btn" onclick="switchTab('merge')">超級合體 (Super Merge)</button>
      </div>

      <div id="tab-content-tattoo">
        <div style="margin-bottom: 1.5rem; text-align: center; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px;">
          <a id="lnk-what-is" href="https://www.5233.space/2026/05/tattoo.html" target="_blank" style="font-size: 0.9em; display: inline-block;">什麼是數位刺青</a>
          <span style="font-size: 0.9em; color: var(--text-secondary); margin: 0 8px;">|</span>
          <a id="lnk-operate" href="https://github.com/taosheng/digital_tattoo/blob/main/find_your_tattoo_zh_TW.md" target="_blank" style="font-size: 0.9em; display: inline-block;">自己操作區塊鏈</a>
          <span style="font-size: 0.9em; color: var(--text-secondary); margin: 0 8px;">|</span>
          <a id="lnk-add-points" href="#" onclick="showPointsInfo(event)" style="font-size: 0.9em; display: inline-block;">如何增加點數?</a>
          <span style="font-size: 0.9em; color: var(--text-secondary); margin: 0 8px;">|</span>
          <a id="lnk-terms" href="#" onclick="showTerms(event)" style="font-size: 0.9em; display: inline-block; color: #ef4444;">服務條款 (Terms)</a>
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
      </div> <!-- End tab-content-tattoo -->

      <!-- Super Merge Tab -->
      <div id="tab-content-merge" class="hidden">
        <div class="glass-panel" style="text-align: center;">
          <h2 id="lbl-super-merge">超級合體</h2>
          <p id="lbl-merge-desc" style="color: var(--text-secondary); margin-bottom: 1rem;">上傳兩張圖片，產生全新合體角色！每次消耗 1 點。</p>
          
          <div style="display: flex; gap: 20px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 250px; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
              <h3 id="lbl-merge-left" style="margin-top: 0;">左邊圖片</h3>
              <input type="file" id="merge-file-1" accept="image/*" style="width: 100%; margin-bottom: 10px;" onchange="checkMergeFiles(1)" />
              <img id="merge-preview-1" class="hidden" style="max-width: 100%; max-height: 200px; border-radius: 8px; object-fit: contain;" />
            </div>
            <div style="flex: 1; min-width: 250px; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;">
              <h3 id="lbl-merge-right" style="margin-top: 0;">右邊圖片</h3>
              <input type="file" id="merge-file-2" accept="image/*" style="width: 100%; margin-bottom: 10px;" onchange="checkMergeFiles(2)" />
              <img id="merge-preview-2" class="hidden" style="max-width: 100%; max-height: 200px; border-radius: 8px; object-fit: contain;" />
            </div>
          </div>
          
          <button id="btn-trigger-merge" class="hidden" onclick="triggerSuperMerge()" style="padding: 10px 30px; font-size: 1.2rem; border-radius: 8px; border: none; background: linear-gradient(135deg, #ff007f, #8a2be2); color: white; cursor: pointer; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">超級合體！(消耗 1 點)</button>
          
          <div id="merge-result-container" class="hidden" style="margin-top: 2rem;">
             <h3 id="lbl-merge-result">合體結果</h3>
             <img id="merge-result-img" src="" style="max-width: 100%; max-height: 400px; border-radius: 12px; border: 3px solid #8a2be2; margin-top: 10px;" />
             <div style="margin-top: 10px; display: flex; justify-content: center; gap: 10px;">
                <button id="btn-download-merge" onclick="downloadMergeResult()" style="padding: 8px 20px; background: var(--secondary); border: none; border-radius: 6px; cursor: pointer; font-weight: bold; color: #000;">下載圖片</button>
                <button id="btn-share-merge" class="hidden" onclick="shareMergeResult()" style="padding: 8px 20px; background: #3b82f6; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; color: #fff;">分享 (Share)</button>
             </div>
             <p id="lbl-merge-vaultsage" style="margin-top: 10px; color: var(--text-secondary); font-size: 0.85em;">結果已備份至 Vaultsage (加密儲存)</p>
          </div>

          <div id="merge-history-container" class="hidden" style="margin-top: 2rem; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 2rem;">
            <h3 id="lbl-merge-history">合體歷史紀錄</h3>
            <div id="merge-history-list" style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;"></div>
          </div>
        </div>
      </div> <!-- End tab-content-merge -->

    </div>
  </div>

  <div id="overlay" class="hidden">
    <div class="loader" style="width: 50px; height: 50px; border-width: 5px; margin-bottom: 1rem;"></div>
    <h3 id="overlay-text">Processing on Blockchain... Please wait.</h3>
  </div>

  <!-- Shared Merge View -->
  <div id="shared-merge-view" class="hidden" style="width: 100%; min-height: 100vh; padding: 2rem; box-sizing: border-box; text-align: center;">
    <h1 style="margin-top:0;">超級合體分享 (Super Merge)</h1>
    <h3 id="shared-merge-owner" style="color: var(--secondary); margin-bottom: 2rem;">Shared by ...</h3>
    
    <div id="shared-password-section" class="glass-panel hidden" style="max-width: 400px; margin: 0 auto;">
       <h3>This merge is password protected</h3>
       <input type="password" id="shared-merge-password" placeholder="Password" style="width:100%; margin-bottom: 1rem; padding: 10px;" />
       <button onclick="loadSharedMerge()" style="padding: 8px 20px; background: var(--secondary); border: none; border-radius: 6px; font-weight: bold;">Unlock</button>
    </div>

    <div id="shared-merge-content" class="hidden">
        <div style="display: flex; gap: 20px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px;">
              <h4>Left Image (Body/Style)</h4>
              <img id="shared-img-left" style="max-width: 100%; max-height: 300px; border-radius: 8px; object-fit: contain;" />
            </div>
            <div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px;">
              <h4>Right Image (Face)</h4>
              <img id="shared-img-right" style="max-width: 100%; max-height: 300px; border-radius: 8px; object-fit: contain;" />
            </div>
        </div>
        <div style="margin-top: 2rem; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px; display: inline-block; max-width: 100%;">
            <h2 style="margin-top: 0; color: #ff007f;">Fusion Result</h2>
            <img id="shared-img-result" style="max-width: 100%; max-height: 500px; border-radius: 12px; border: 3px solid #8a2be2;" />
        </div>
        <div style="margin-top: 2rem;">
            <a href="/" style="color: white; text-decoration: underline;">Make your own Super Merge!</a>
        </div>
    </div>
  </div>
`;

window.sessionToken = null;
window.currentShareKey = null;

window.loadSharedMerge = async () => {
    const pwdInput = document.getElementById('shared-merge-password');
    const pwd = pwdInput ? pwdInput.value : '';
    
    let url = `/api/merge/share_info/${window.currentShareKey}`;
    if (pwd) url += `?password=${encodeURIComponent(pwd)}`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (res.ok) {
            if (data.requires_password) {
                document.getElementById('shared-password-section').classList.remove('hidden');
                document.getElementById('shared-merge-content').classList.add('hidden');
                if (pwd) alert("Incorrect password");
            } else {
                document.getElementById('shared-password-section').classList.add('hidden');
                document.getElementById('shared-merge-owner').innerText = `Shared by ${data.owner_name}`;
                
                // Load images
                let pwdQuery = pwd ? `?password=${encodeURIComponent(pwd)}` : '';
                document.getElementById('shared-img-left').src = `/api/merge/share_image/${window.currentShareKey}/left${pwdQuery}`;
                document.getElementById('shared-img-right').src = `/api/merge/share_image/${window.currentShareKey}/right${pwdQuery}`;
                document.getElementById('shared-img-result').src = `/api/merge/share_image/${window.currentShareKey}/result${pwdQuery}`;
                
                document.getElementById('shared-merge-content').classList.remove('hidden');
            }
        } else {
            alert(data.detail || "Share link not found");
        }
    } catch(e) {
        alert("Network error");
    }
};

// Check if it's a shared link view
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('merge_share')) {
    window.currentShareKey = urlParams.get('merge_share');
    const appContainer = document.querySelector('.container');
    if (appContainer) appContainer.classList.add('hidden'); // Hide normal app
    document.getElementById('shared-merge-view').classList.remove('hidden');
    window.loadSharedMerge();
}

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

window.handleLineLogin = () => {
  const lineClientId = import.meta.env.VITE_LINE_CLIENT_ID;
  if (!lineClientId) {
    alert("LINE Client ID is missing.");
    return;
  }
  const redirectUri = encodeURIComponent(window.location.origin);
  const state = Math.random().toString(36).substring(7); // Basic CSRF protection
  // Store state in session storage to verify upon return
  sessionStorage.setItem('line_auth_state', state);
  
  const lineAuthUrl = `https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id=${lineClientId}&redirect_uri=${redirectUri}&state=${state}&scope=profile%20openid%20email`;
  window.location.href = lineAuthUrl;
};

// Check for LINE auth callback on load
window.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  
  if (code && state) {
    const savedState = sessionStorage.getItem('line_auth_state');
    if (state === savedState) {
      sessionStorage.removeItem('line_auth_state');
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      showOverlay("Authenticating with LINE...");
      try {
        const res = await fetch('/api/auth/line', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            code: code,
            redirect_uri: window.location.origin
          })
        });
        const data = await res.json();
        if (res.ok) {
          window.sessionToken = data.session_token;
          initDashboard(data.user);
        } else {
          alert("LINE Authentication Failed: " + data.detail);
        }
      } catch (err) {
        alert("Network error.");
      } finally {
        hideOverlay();
      }
    } else {
      console.warn("LINE state mismatch. Potential CSRF.");
    }
  }
});

renderGoogleButton();

// Language Selector Logic

window.switchTab = (tab) => {
  if (tab === 'tattoo') {
    document.getElementById('tab-btn-tattoo').classList.add('active');
    document.getElementById('tab-btn-merge').classList.remove('active');
    document.getElementById('tab-content-tattoo').classList.remove('hidden');
    document.getElementById('tab-content-merge').classList.add('hidden');
  } else {
    document.getElementById('tab-btn-tattoo').classList.remove('active');
    document.getElementById('tab-btn-merge').classList.add('active');
    document.getElementById('tab-content-tattoo').classList.add('hidden');
    document.getElementById('tab-content-merge').classList.remove('hidden');
  }
};

window.mergeHistory = [];

window.checkMergeFiles = (index) => {
  const fileInput = document.getElementById(`merge-file-${index}`);
  const previewImg = document.getElementById(`merge-preview-${index}`);
  
  if (fileInput && fileInput.files && fileInput.files[0]) {
    const file = fileInput.files[0];
    const objectUrl = URL.createObjectURL(file);
    previewImg.src = objectUrl;
    previewImg.classList.remove('hidden');
    // Store the object URL on the element so we can reuse it in history
    previewImg.dataset.originalUrl = objectUrl;
  } else if (previewImg) {
    previewImg.classList.add('hidden');
    previewImg.src = '';
  }

  const file1 = document.getElementById('merge-file-1').files.length > 0;
  const file2 = document.getElementById('merge-file-2').files.length > 0;
  const btn = document.getElementById('btn-trigger-merge');
  if (file1 && file2) {
    btn.classList.remove('hidden');
  } else {
    btn.classList.add('hidden');
  }
};

window.triggerSuperMerge = async () => {
  let f1 = document.getElementById('merge-file-1').files[0];
  let f2 = document.getElementById('merge-file-2').files[0];
  
  const textEl = document.getElementById('overlay-text');
  showOverlay("Initializing merge process...");
  
  let progressInterval = setInterval(() => {
    if (!textEl) return;
    const currentText = textEl.innerText;
    if (currentText.includes("Initializing")) {
      textEl.innerText = "[Step 1] AI is extracting features from your images...";
    } else if (currentText.includes("Step 1")) {
      textEl.innerText = "[Step 2] AI is designing the fusion prompt...";
    } else if (currentText.includes("Step 2")) {
      textEl.innerText = "[Step 3] AI is painting your new realistic avatar... (Almost done!)";
    }
  }, 6000);

  try {
    // If files are not in the input (e.g. loaded from history), recover them from preview URLs
    if (!f1) {
      const p1 = document.getElementById('merge-preview-1').dataset.originalUrl;
      if (p1) {
        const r = await fetch(p1);
        const b = await r.blob();
        f1 = new File([b], "history1.jpg", { type: b.type });
      }
    }
    if (!f2) {
      const p2 = document.getElementById('merge-preview-2').dataset.originalUrl;
      if (p2) {
        const r = await fetch(p2);
        const b = await r.blob();
        f2 = new File([b], "history2.jpg", { type: b.type });
      }
    }

    if (!f1 || !f2) {
      hideOverlay();
      return;
    }
    
    // Validate sizes
    if (f1.size > 10 * 1024 * 1024 || f2.size > 10 * 1024 * 1024) {
      alert("Files must be smaller than 10MB");
      hideOverlay();
      return;
    }
    
    const formData = new FormData();
    formData.append("file1", f1);
    formData.append("file2", f2);
    
    const res = await fetch('/api/merge/super_merge', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${window.sessionToken}`
      },
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById('user-points').innerText = data.new_points;
      
      const resContainer = document.getElementById('merge-result-container');
      const resImg = document.getElementById('merge-result-img');
      resImg.src = data.merged_image_url;
      resImg.dataset.downloadUrl = data.merged_image_url; // store to download
      if (data.merge_id) {
          resImg.dataset.mergeId = data.merge_id;
          document.getElementById('btn-share-merge').classList.remove('hidden');
      } else {
          resImg.dataset.mergeId = "";
          document.getElementById('btn-share-merge').classList.add('hidden');
      }
      resContainer.classList.remove('hidden');
      
      // Add to history
      const prev1 = document.getElementById('merge-preview-1').dataset.originalUrl;
      const prev2 = document.getElementById('merge-preview-2').dataset.originalUrl;
      window.mergeHistory.push({
        merge_id: data.merge_id,
        left: prev1,
        right: prev2,
        result: data.merged_image_url,
        timestamp: new Date().toLocaleString()
      });
      renderMergeHistory();
      
    } else {
      alert("Merge Failed: " + data.detail);
    }
  } catch (err) {
    alert("Network error.");
  } finally {
    clearInterval(progressInterval);
    hideOverlay();
  }
};

window.downloadMergeResult = async () => {
  const url = document.getElementById('merge-result-img').dataset.downloadUrl;
  if (!url) return;
  try {
    // If CORS prevents direct download, we fetch and create a blob URL
    const response = await fetch(url);
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = "super_merge_result.jpg";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blobUrl);
  } catch (err) {
    // Fallback if fetch fails due to CORS
    window.open(url, '_blank');
  }
};

window.shareMergeResult = async () => {
  const mergeId = document.getElementById('merge-result-img').dataset.mergeId;
  if (!mergeId) return;

  const lang = document.getElementById('lang-select') ? document.getElementById('lang-select').value : 'zh';
  const wantPassword = confirm(lang === 'zh' ? "是否要為此分享連結設定密碼保護？" : "Do you want to set a password for this shared link?");
  
  let password = "";
  if (wantPassword) {
      password = prompt(lang === 'zh' ? "請輸入分享密碼：" : "Please enter a password:");
      if (password === null) return; // User cancelled
  }

  showOverlay(lang === 'zh' ? "產生分享連結中..." : "Generating share link...");
  try {
      const res = await fetch(`/api/merge/share/${mergeId}`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${window.sessionToken}`
          },
          body: JSON.stringify({ password: password })
      });
      const data = await res.json();
      if (res.ok) {
          const shareUrl = window.location.origin + "/?merge_share=" + data.share_key;
          prompt(lang === 'zh' ? "分享連結已建立！請複製以下網址：" : "Share link created! Copy the URL below:", shareUrl);
      } else {
          alert("Error: " + data.detail);
      }
  } catch(e) {
      alert("Network error");
  } finally {
      hideOverlay();
  }
};

window.renderMergeHistory = () => {
  const container = document.getElementById('merge-history-container');
  const listEl = document.getElementById('merge-history-list');
  
  if (window.mergeHistory.length > 0) {
    container.classList.remove('hidden');
  } else {
    container.classList.add('hidden');
    return;
  }
  
  listEl.innerHTML = '';
  window.mergeHistory.forEach((record, index) => {
    const item = document.createElement('div');
    item.style.cssText = "width: 150px; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; cursor: pointer; text-align: center; transition: background 0.2s;";
    item.onmouseover = () => item.style.background = "rgba(255,255,255,0.2)";
    item.onmouseout = () => item.style.background = "rgba(255,255,255,0.1)";
    item.onclick = () => loadMergeHistoryRecord(index);
    
    item.innerHTML = `
      <img src="${record.result}" style="width: 100%; height: 100px; object-fit: cover; border-radius: 6px; margin-bottom: 5px;" />
      <div style="font-size: 0.8em; color: var(--text-secondary);">${record.timestamp}</div>
    `;
    listEl.appendChild(item);
  });
};

window.loadMergeHistoryRecord = (index) => {
  const record = window.mergeHistory[index];
  if (!record) return;
  
  // Load left image
  const prev1 = document.getElementById('merge-preview-1');
  prev1.src = record.left;
  prev1.classList.remove('hidden');
  
  // Load right image
  const prev2 = document.getElementById('merge-preview-2');
  prev2.src = record.right;
  prev2.classList.remove('hidden');
  
  // Clear file inputs to avoid confusion with what is displayed
  document.getElementById('merge-file-1').value = "";
  document.getElementById('merge-file-2').value = "";
  document.getElementById('btn-trigger-merge').classList.add('hidden');
  
  // Load result image
  const resContainer = document.getElementById('merge-result-container');
  const resImg = document.getElementById('merge-result-img');
  resImg.src = record.result;
  resImg.dataset.downloadUrl = record.result;
  if (record.merge_id) {
     resImg.dataset.mergeId = record.merge_id;
     document.getElementById('btn-share-merge').classList.remove('hidden');
  } else {
     resImg.dataset.mergeId = "";
     document.getElementById('btn-share-merge').classList.add('hidden');
  }
  resContainer.classList.remove('hidden');
  
  // Scroll to top of the merge tab
  document.getElementById('tab-content-merge').scrollIntoView({ behavior: 'smooth' });
};

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
    if(document.getElementById('lnk-privacy')) document.getElementById('lnk-privacy').innerText = "隱私權政策";
    if(document.getElementById('lnk-terms-static')) document.getElementById('lnk-terms-static').innerText = "服務條款";
    if(document.getElementById('lnk-deletion')) document.getElementById('lnk-deletion').innerText = "資料刪除";
    if(document.getElementById('lbl-line-login')) document.getElementById('lbl-line-login').innerText = "LINE 登入";
    if(document.getElementById('tab-btn-tattoo')) document.getElementById('tab-btn-tattoo').innerText = "數位刺青 (Digital Tattoo)";
    if(document.getElementById('tab-btn-merge')) document.getElementById('tab-btn-merge').innerText = "超級合體 (Super Merge)";
    if(document.getElementById('lbl-super-merge')) document.getElementById('lbl-super-merge').innerText = "超級合體";
    if(document.getElementById('lbl-merge-desc')) document.getElementById('lbl-merge-desc').innerText = "上傳兩張圖片，產生全新合體角色！每次消耗 1 點。";
    if(document.getElementById('lbl-merge-left')) document.getElementById('lbl-merge-left').innerText = "左邊圖片";
    if(document.getElementById('lbl-merge-right')) document.getElementById('lbl-merge-right').innerText = "右邊圖片";
    if(document.getElementById('btn-trigger-merge')) document.getElementById('btn-trigger-merge').innerText = "超級合體！(消耗 1 點)";
    if(document.getElementById('lbl-merge-result')) document.getElementById('lbl-merge-result').innerText = "合體結果";
    if(document.getElementById('btn-download-merge')) document.getElementById('btn-download-merge').innerText = "下載圖片";
    if(document.getElementById('btn-share-merge')) document.getElementById('btn-share-merge').innerText = "分享 (Share)";
    if(document.getElementById('lbl-merge-vaultsage')) document.getElementById('lbl-merge-vaultsage').innerText = "結果已備份至 Vaultsage (加密儲存)";
  } else {
    document.getElementById('main-title').innerText = "Digital Tattoo";
    document.getElementById('main-subtitle').innerText = "Your data on the blockchain, forever.";
    if(document.getElementById('lnk-what-is')) document.getElementById('lnk-what-is').innerText = "What is Digital Tattoo";
    if(document.getElementById('lnk-operate')) document.getElementById('lnk-operate').innerText = "How to operate blockchain";
    
    if(document.getElementById('lbl-create-string')) document.getElementById('lbl-create-string').innerText = "Create String Tattoo";
    if(document.getElementById('lbl-string-msg')) document.getElementById('lbl-string-msg').innerText = "Message (Max 1000 chars)";
    if(document.getElementById('btn-string')) document.getElementById('btn-string').innerText = "Tattoo into Blockchain";
    
    if(document.getElementById('lbl-create-file')) document.getElementById('lbl-create-file').innerText = "Create File Tattoo";
    if(document.getElementById('lbl-file-msg')) document.getElementById('lbl-file-msg').innerText = "File (Max 10MB. Images auto-compressed)";
    if(document.getElementById('btn-file')) document.getElementById('btn-file').innerText = "Tattoo into Blockchain";
    
    if(document.getElementById('lbl-string-encrypt')) document.getElementById('lbl-string-encrypt').innerText = "Encrypt Tattoo (We auto-generate key)";
    if(document.getElementById('lbl-file-encrypt')) document.getElementById('lbl-file-encrypt').innerText = "Encrypt Tattoo (We auto-generate key)";
    
    if(document.getElementById('lbl-tattoos')) document.getElementById('lbl-tattoos').innerText = "Your Tattoos";
    if(document.getElementById('lbl-loading')) document.getElementById('lbl-loading').innerText = "Loading...";
    if(document.getElementById('lnk-add-points')) document.getElementById('lnk-add-points').innerText = "How to add points?";
    if(document.getElementById('lnk-terms')) document.getElementById('lnk-terms').innerText = "Terms of Service";
    if(document.getElementById('lnk-privacy')) document.getElementById('lnk-privacy').innerText = "Privacy Policy";
    if(document.getElementById('lnk-terms-static')) document.getElementById('lnk-terms-static').innerText = "Terms of Service";
    if(document.getElementById('lnk-deletion')) document.getElementById('lnk-deletion').innerText = "Data Deletion";
    if(document.getElementById('lbl-line-login')) document.getElementById('lbl-line-login').innerText = "LINE Login";
    if(document.getElementById('tab-btn-tattoo')) document.getElementById('tab-btn-tattoo').innerText = "Digital Tattoo";
    if(document.getElementById('tab-btn-merge')) document.getElementById('tab-btn-merge').innerText = "Super Merge";
    if(document.getElementById('lbl-super-merge')) document.getElementById('lbl-super-merge').innerText = "Super Merge";
    if(document.getElementById('lbl-merge-desc')) document.getElementById('lbl-merge-desc').innerText = "Upload 2 images and create a new fusion character! Cost 1 Point.";
    if(document.getElementById('lbl-merge-left')) document.getElementById('lbl-merge-left').innerText = "Left Image";
    if(document.getElementById('lbl-merge-right')) document.getElementById('lbl-merge-right').innerText = "Right Image";
    if(document.getElementById('btn-trigger-merge')) document.getElementById('btn-trigger-merge').innerText = "Super Merge! (Cost 1 Point)";
    if(document.getElementById('lbl-merge-result')) document.getElementById('lbl-merge-result').innerText = "Fusion Result";
    if(document.getElementById('btn-download-merge')) document.getElementById('btn-download-merge').innerText = "Download Image";
    if(document.getElementById('btn-share-merge')) document.getElementById('btn-share-merge').innerText = "Share";
    if(document.getElementById('lbl-merge-vaultsage')) document.getElementById('lbl-merge-vaultsage').innerText = "Result backed up to Vaultsage (Encrypted)";
  }
});

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

