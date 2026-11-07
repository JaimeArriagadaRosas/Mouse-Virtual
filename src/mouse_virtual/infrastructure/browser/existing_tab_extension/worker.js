'use strict';
importScripts('workspace.js');
// Controls only an explicitly paired browser tab. Never moves the Windows cursor,
// extracts cookies, creates browser profiles, or activates a tab.
const BRIDGE = 'ws://127.0.0.1:8765';
const SETTINGS_KEY = 'mouse_virtual_pairing_v2';
const ALARM_NAME = 'mouse-virtual-connection-watchdog';
const VALID_KEYS = {
  Enter:13,Tab:9,Escape:27,Backspace:8,Delete:46,
  ArrowDown:40,ArrowUp:38,ArrowLeft:37,ArrowRight:39
};
const ACTIONS = new Set([
  'inspect','screenshot','move','click','type','key','navigate',
  'dom.click','dom.fill','file','tab.select',
  'tab.list','tab.select_id',
  'workspace.create','workspace.open','workspace.select','workspace.close'
]);
let socket = null;
let targetId = null;
let initialized = false;
let connecting = false;
let busy = false;
let reconnectTimer = null;
let heartbeatTimer = null;
let consecutiveFailures = 0;
let intentionalDetach = false;

function isToken(value) {
  return typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
}
function isWebPage(url) {
  try {
    const parsed = new URL(url);
    return (parsed.protocol === 'https:' || parsed.protocol === 'http:') &&
      !parsed.username && !parsed.password;
  } catch (_) { return false; }
}
function hostOf(url) {
  if (!isWebPage(url)) return null;
  return new URL(url).hostname.toLowerCase();
}
async function storedPairing() {
  const obj = await chrome.storage.local.get(SETTINGS_KEY);
  return obj[SETTINGS_KEY] || null;
}
async function savePairing(pairing) {
  await chrome.storage.local.set({[SETTINGS_KEY]:pairing});
}
function stopReconnectTimer() {
  if (reconnectTimer !== null) clearTimeout(reconnectTimer);
  reconnectTimer = null;
}
function closeSocket() {
  if (heartbeatTimer !== null) clearInterval(heartbeatTimer);
  heartbeatTimer = null;
  const ws = socket;
  socket = null;
  initialized = false;
  if (ws && ws.readyState < WebSocket.CLOSING) {
    try { ws.close(1000, 'Disconnected'); } catch (_) {}
  }
}
function planReconnect(delay=null) {
  if (reconnectTimer !== null) return;
  const backoff = Math.min(30000, 1500 * Math.pow(2, Math.min(consecutiveFailures, 5)));
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    restoreConnection().catch(() => planReconnect());
  }, delay === null ? backoff : delay);
}
async function detachDebugger() {
  const old = targetId;
  targetId = null;
  if (old === null) return;
  intentionalDetach = true;
  try {
    await chrome.debugger.sendCommand({tabId:old},'Runtime.evaluate',{
      expression:"document.getElementById('__mv_independent_cursor__')?.remove()"
    });
  } catch (_) {}
  try { await chrome.debugger.detach({tabId:old}); } catch (_) {}
  intentionalDetach = false;
}
async function disconnect() {
  stopReconnectTimer();
  closeSocket();
  await chrome.storage.local.remove(SETTINGS_KEY);
  await detachDebugger();
}
function cdp(method,params={}) {
  if (targetId === null) throw Error('No tab attached');
  return chrome.debugger.sendCommand({tabId:targetId},method,params);
}
function coord(value) {
  if (!Number.isFinite(value) || value < 0 || value > 16384)
    throw Error('Invalid coordinate');
  return value;
}
async function pointer(x,y) {
  const expression = [
    "(()=>{let el=document.getElementById('__mv_independent_cursor__');",
    "if(!el){el=document.createElement('div');el.id='__mv_independent_cursor__';",
    "Object.assign(el.style,{position:'fixed',zIndex:'2147483647',pointerEvents:'none',",
    "width:'16px',height:'23px',background:'#111827',",
    "clipPath:'polygon(0 0,0 100%,4px 80%,8px 100%,11px 97%,7px 77%,16px 76%)',",
    "filter:'drop-shadow(1px 1px 1px white)'});",
    "(document.documentElement||document.body).appendChild(el);}",
    "el.style.left=",JSON.stringify(x+'px'),";",
    "el.style.top=",JSON.stringify(y+'px'),";return true;})()"
  ].join('');
  await cdp('Runtime.evaluate',{expression,returnByValue:true});
}
function mouse(x,y,type) {
  return cdp('Input.dispatchMouseEvent',{
    type,x,y,button:type==='mouseMoved'?'none':'left',
    clickCount:type==='mouseMoved'?0:1
  });
}
async function click(x,y) {
  await pointer(x,y);
  await mouse(x,y,'mouseMoved');
  await mouse(x,y,'mousePressed');
  await mouse(x,y,'mouseReleased');
  return {clicked:true,x,y};
}
async function key(name) {
  const vk = VALID_KEYS[name];
  if (vk === undefined) throw Error('Unsupported key');
  await cdp('Input.dispatchKeyEvent',{
    type:'keyDown',key:name,code:name,
    windowsVirtualKeyCode:vk,nativeVirtualKeyCode:vk
  });
  await cdp('Input.dispatchKeyEvent',{
    type:'keyUp',key:name,code:name,
    windowsVirtualKeyCode:vk,nativeVirtualKeyCode:vk
  });
  return {pressed:name};
}
async function nodeFor(selector) {
  if (typeof selector !== 'string' || !selector || selector.length > 300)
    throw Error('Invalid CSS selector');
  const doc = await cdp('DOM.getDocument',{depth:0});
  const result = await cdp('DOM.querySelector',{
    nodeId:doc.root.nodeId,selector
  });
  if (!result.nodeId) throw Error('Element not found');
  return result.nodeId;
}
async function center(nodeId) {
  const {model} = await cdp('DOM.getBoxModel',{nodeId});
  const v = model.content;
  return {x:(v[0]+v[2]+v[4]+v[6])/4,y:(v[1]+v[3]+v[5]+v[7])/4};
}
async function fill(selector,text) {
  const nodeId = await nodeFor(selector);
  await cdp('DOM.focus',{nodeId});
  await cdp('Input.dispatchKeyEvent',{
    type:'keyDown',key:'a',code:'KeyA',modifiers:2,
    windowsVirtualKeyCode:65
  });
  await cdp('Input.dispatchKeyEvent',{
    type:'keyUp',key:'a',code:'KeyA',windowsVirtualKeyCode:65
  });
  await cdp('Input.insertText',{text});
  return {filled:true,length:text.length};
}
async function inspect() {
  // Fixed expression. Never includes password values, cookies or token storage.
  const expression = [
    "(()=>({url:location.href,title:document.title,",
    "interactive:[...document.querySelectorAll('button,a,input,textarea,select,[role=button]')]",
    ".filter(el=>el.getClientRects().length>0&&!el.matches('input[type=password]'))",
    ".slice(0,50).map(el=>({tag:el.tagName.toLowerCase(),",
    "role:el.getAttribute('role')||'',",
    "label:(el.getAttribute('aria-label')||el.innerText||el.getAttribute('placeholder')||'').trim().slice(0,100),",
    "id:(el.id||'').slice(0,100),type:(el.getAttribute('type')||'').slice(0,20)}))}))()"
  ].join('');
  const response = await cdp('Runtime.evaluate',{expression,returnByValue:true});
  return response.result?.value || {ready:false};
}
async function findUniqueInactiveTab(pairing, host, prefix='') {
  if (!host) throw Error('The target tab host is required');
  const tabs = await chrome.tabs.query({windowId:pairing.windowId});
  const matches = tabs.filter(t=>t.id && !t.active &&
    hostOf(t.url) === host && (!prefix || t.url.startsWith(prefix)));
  if (matches.length !== 1) {
    throw Error('Expected exactly one inactive matching tab; found '+matches.length);
  }
  return matches[0];
}
async function changeTab(tab) {
  if (targetId !== null && targetId !== tab.id) await detachDebugger();
  if (targetId === null) {
    await chrome.debugger.attach({tabId:tab.id},'1.3');
    targetId = tab.id;
  }
  const saved = await storedPairing();
  if (saved) {
    saved.tabId = tab.id;
    saved.windowId = tab.windowId;
    saved.host = hostOf(tab.url)||saved.host;
    await savePairing(saved);
  }
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({kind:'tab_changed',tabId:tab.id}));
  }
}
async function switchTab(host,prefix='') {
  const saved = await storedPairing();
  if (!saved || !initialized) throw Error('Bridge not paired');
  if (typeof host !== 'string' || !host ||
      (prefix && (typeof prefix !== 'string' ||
        hostOf(prefix) !== host.toLowerCase()))) {
    throw Error('Invalid approved tab host or URL prefix');
  }
  const tab = await findUniqueInactiveTab(saved,host.toLowerCase(),prefix);
  await changeTab(tab);
  return {selected:true,tab_id:tab.id};
}
async function execute(req) {
  if (!ACTIONS.has(req.action)) throw Error('Unsupported action');
  switch (req.action) {
    case 'inspect': return inspect();
    case 'screenshot': {
      const image = await cdp('Page.captureScreenshot',{format:'png',fromSurface:true});
      return {data:image.data};
    }
    case 'move': {
      const x=coord(req.x),y=coord(req.y);
      await pointer(x,y);
      await mouse(x,y,'mouseMoved');
      return {moved:true,x,y};
    }
    case 'click': return click(coord(req.x),coord(req.y));
    case 'type': {
      if (typeof req.text !== 'string' || req.text.length > 5000)
        throw Error('Invalid text');
      await cdp('Input.insertText',{text:req.text});
      return {typed:true,length:req.text.length};
    }
    case 'key': return key(req.key);
    case 'navigate': {
      const url = new URL(req.url);
      if (!isWebPage(url.href)) throw Error('Invalid navigation URL');
      const result=await cdp('Page.navigate',{url:url.href});
      return {navigated:true,frameId:result.frameId||null};
    }
    case 'dom.click': {
      const pt=await center(await nodeFor(req.selector));
      return click(pt.x,pt.y);
    }
    case 'dom.fill': {
      if (typeof req.text !== 'string' || req.text.length > 5000)
        throw Error('Invalid text');
      return fill(req.selector,req.text);
    }
    case 'file': {
      const nodeId=await nodeFor(req.selector);
      await cdp('DOM.setFileInputFiles',{nodeId,files:[req.path]});
      return {file_attached:true};
    }
    case 'tab.select':
      return switchTab(req.host,req.urlPrefix||'');
    case 'tab.list':
      return listAllTabs();
    case 'tab.select_id':
      return selectExistingTabById(req.tabId,req.host);
    case 'workspace.create':
      return createWorkspace(req.url);
    case 'workspace.open':
      return openInWorkspace(req.url);
    case 'workspace.select':
      return selectWorkspaceTab(req.tabId);
    case 'workspace.close':
      return closeWorkspaceTab(req.tabId);
  }
}
async function connectSocket(pairing) {
  return new Promise((resolve,reject) => {
    const ws = new WebSocket(BRIDGE);
    let ready=false;
    const timeout=setTimeout(() => {
      if (!ready) {
        try { ws.close(); } catch (_) {}
        reject(Error('Local bridge timeout'));
      }
    },6000);
    ws.onopen=()=>ws.send(JSON.stringify({
      role:'extension',token:pairing.token,tabId:pairing.tabId
    }));
    ws.onerror=()=>{if(!ready){clearTimeout(timeout);reject(Error('Local bridge unavailable'));}};
    ws.onmessage=e=>{
      let message;
      try {message=JSON.parse(e.data);} catch (_) {return;}
      if (!ready) {
        if (!message.ok) {
          clearTimeout(timeout);
          reject(Error('Pairing rejected by local service'));
          return;
        }
        ready=true;
        socket=ws;
        initialized=true;
        consecutiveFailures=0;
        stopReconnectTimer();
        clearTimeout(timeout);
        heartbeatTimer=setInterval(()=>{
          if (socket === ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({kind:'heartbeat'}));
          }
        },18000);
        resolve({ok:true,connected:true,tabId:pairing.tabId});
      } else if(message.kind === 'heartbeat_ack') {
        // Keep-alive acknowledgement: no user command.
      } else {
        receive(message);
      }
    };
    ws.onclose=()=>{
      clearTimeout(timeout);
      if (socket===ws) {
        closeSocket();
        consecutiveFailures++;
        planReconnect();
      } else if(!ready) {
        reject(Error('Local bridge closed before pairing'));
      }
    };
  });
}
async function attach(tabId,token,remember=true) {
  if (typeof tabId !== 'number' || !isToken(token))
    throw Error('Invalid selected tab or pairing code');
  if (connecting) return {ok:false,error:'Connection in progress'};
  connecting=true;
  try {
    const tab=await chrome.tabs.get(tabId);
    const host=hostOf(tab.url);
    if (!host) throw Error('Select a normal HTTP(S) browser tab');
    const existing=await storedPairing();
    if (remember && targetId !== null && targetId !== tabId)
      await detachDebugger();
    if (targetId === null) {
      await chrome.debugger.attach({tabId},'1.3');
      targetId=tabId;
    }
    const pairing={
      tabId,windowId:tab.windowId,host,token,
      autoFollow:existing?.autoFollow ?? true
    };
    if (remember) await savePairing(pairing);
    if (initialized && socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({kind:'tab_changed',tabId}));
      return {ok:true,connected:true,tabId};
    }
    closeSocket();
    return await connectSocket(pairing);
  } catch(e) {
    closeSocket();
    consecutiveFailures++;
    planReconnect();
    return {ok:false,error:String(e.message||e)};
  } finally {
    connecting=false;
  }
}
async function restoreConnection() {
  if (initialized || connecting) return;
  const pairing=await storedPairing();
  if (!pairing || !isToken(pairing.token)) return;
  try {
    let tab;
    try {tab=await chrome.tabs.get(pairing.tabId);} catch (_) {}
    if (!tab || !isWebPage(tab.url) ||
        hostOf(tab.url)!==pairing.host ||
        tab.windowId!==pairing.windowId) {
      if (!pairing.autoFollow) return;
      try {
        tab=await findUniqueInactiveTab(pairing,pairing.host);
      }catch (_) {
        // A Chrome restart can allocate different window IDs.
        const all=await chrome.tabs.query({});
        const candidates=all.filter(t=>t.id && !t.active &&
          hostOf(t.url)===pairing.host);
        if(candidates.length!==1)throw Error('Ambiguous or absent replacement tab');
        tab=candidates[0];
      }
    }
    if (pairing.tabId !== tab.id) {
      pairing.tabId=tab.id;
      pairing.windowId=tab.windowId;
      await savePairing(pairing);
    }
    await attach(tab.id,pairing.token,false);
  } catch (_) {
    consecutiveFailures++;
    planReconnect();
  }
}
async function receive(req) {
  if (!initialized || !socket || socket.readyState !== WebSocket.OPEN) return;
  const ws=socket;
  if (busy) {
    ws.send(JSON.stringify({kind:'reply',id:req.id,ok:false,error:'Tab busy'}));
    return;
  }
  busy=true;
  try {
    const result=await execute(req);
    ws.send(JSON.stringify({kind:'reply',id:req.id,ok:true,...result}));
  } catch(e) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        kind:'reply',id:req.id,ok:false,error:String(e.message||e).slice(0,250)
      }));
    }
  } finally {busy=false;}
}
chrome.runtime.onMessage.addListener((msg,sender,respond)=>{
  (async()=>{
    if(msg.kind==='attach') return attach(msg.tabId,msg.token,true);
    if(msg.kind==='detach') {
      await disconnect();
      return {ok:true,connected:false};
    }
    if(msg.kind==='switch') {
      const saved=await storedPairing();
      if(!saved)throw Error('Pair the browser once before changing tabs');
      return attach(msg.tabId,saved.token,true);
    }
    if(msg.kind==='status') {
      const pairing=await storedPairing();
      return {ok:true,connected:initialized,tabId:targetId,
              remembered:!!pairing,autoFollow:!!pairing?.autoFollow};
    }
    if(msg.kind==='auto-follow') {
      const pairing=await storedPairing();
      if (!pairing) throw Error('Pair a tab before changing settings');
      pairing.autoFollow=msg.enabled===true;
      await savePairing(pairing);
      return {ok:true,autoFollow:pairing.autoFollow};
    }
    if(msg.kind==='reconnect') {
      await restoreConnection();
      return {ok:true,connected:initialized};
    }
    return {ok:false,error:'Unsupported popup action'};
  })().then(respond,e=>respond({ok:false,error:String(e.message||e)}));
  return true;
});
chrome.debugger.onDetach.addListener((source,reason)=>{
  if(source.tabId !== targetId || intentionalDetach) return;
  targetId=null;
  closeSocket();
  if(reason==='canceled_by_user' || reason==='replaced_with_devtools') {
    chrome.storage.local.remove(SETTINGS_KEY);
    stopReconnectTimer();
  } else planReconnect();
});
chrome.tabs.onRemoved.addListener(id=>{
  if(id!==targetId) return;
  targetId=null;
  closeSocket();
  planReconnect(1500);
});
chrome.alarms.onAlarm.addListener(alarm=>{
  if(alarm.name===ALARM_NAME) restoreConnection().catch(()=>{});
});
chrome.runtime.onStartup.addListener(()=>restoreConnection().catch(()=>{}));
chrome.runtime.onInstalled.addListener(()=>restoreConnection().catch(()=>{}));
// Periodic fallback for suspended MV3 service workers; no visible windows.
chrome.alarms.create(ALARM_NAME,{periodInMinutes:1});
restoreConnection().catch(()=>{});
