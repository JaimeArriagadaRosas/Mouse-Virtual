'use strict';
/*
 * A tab-group workspace INSIDE the user's already-open Chrome browser.
 * No new browser process/profile. No foreground tab activation.
 * Only tabs created by the workspace are managed by workspace operations.
 * An explicitly requested tab.select_id may choose another inactive tab.
 */
const WORKSPACE_KEY='mouse_virtual_workspace_v1';
const WORKSPACE_TITLE='Mouse Virtual';
function workspaceURL(value){
  if(typeof value!=='string'||value.length>4096||!isWebPage(value))
    throw Error('An HTTP(S) URL is required');
  return new URL(value).href;
}
function publicTab(tab){
  return {
    tabId:tab.id,windowId:tab.windowId,
    groupId:tab.groupId??-1,
    title:(tab.title||'').slice(0,160),
    url:(tab.url||'').slice(0,1024),
    active:!!tab.active,
    controllable:!tab.active && isWebPage(tab.url),
    incognito:!!tab.incognito
  };
}
async function groupState(){
  const raw=await chrome.storage.local.get(WORKSPACE_KEY);
  const state=raw[WORKSPACE_KEY];
  if(!state||!Number.isInteger(state.groupId))return null;
  let group=null;
  try {
    group=await chrome.tabGroups.get(state.groupId);
    if(group.title!==WORKSPACE_TITLE)group=null;
  }catch(_){}
  if(!group){
    // Chrome can reassign group IDs when restoring a browser session.
    // Recover only an unambiguous group with our dedicated title.
    const matches=await chrome.tabGroups.query({title:WORKSPACE_TITLE});
    const regular=matches.filter(g=>!g.incognito);
    if(regular.length!==1)return null;
    group=regular[0];
    await chrome.storage.local.set({[WORKSPACE_KEY]:{
      groupId:group.id,windowId:group.windowId
    }});
  }
  const tabs=await chrome.tabs.query({groupId:group.id});
  const regular=tabs.filter(t=>!t.incognito);
  if(regular.length===0)return null;
  return {
    groupId:group.id,windowId:group.windowId,
    title:group.title,tabs:regular.map(publicTab)
  };
}
async function listAllTabs(){
  const tabs=await chrome.tabs.query({});
  // Show every regular tab, even when Chrome's internal pages cannot be controlled.
  const regular=tabs.filter(t=>!t.incognito && t.id);
  const state=await groupState();
  return {
    tabs:regular.map(publicTab),
    workspace:state,
    selectedTabId:targetId
  };
}
async function createWorkspace(url){
  if(!initialized)throw Error('Pair a Chrome tab before creating a workspace');
  const current=await groupState();
  if(current)throw Error('A workspace group already exists: use workspace.open');
  const pairing=await storedPairing();
  if(!pairing)throw Error('No paired browser window');
  const original=await chrome.tabs.get(pairing.tabId);
  if(original.incognito)throw Error('Incognito browser tabs are not supported');
  const tab=await chrome.tabs.create({
    windowId:original.windowId,url:workspaceURL(url),active:false
  });
  let groupId;
  try{
    groupId=await chrome.tabs.group({tabIds:tab.id});
    await chrome.tabGroups.update(groupId,{
      title:WORKSPACE_TITLE,color:'blue',collapsed:true
    });
    await chrome.storage.local.set({[WORKSPACE_KEY]:{
      groupId,windowId:tab.windowId
    }});
    await changeTab(tab);
    return {created:true,tab:publicTab(await chrome.tabs.get(tab.id)),
      groupId};
  }catch(e){
    if(groupId!==undefined){
      try{await chrome.tabs.ungroup(tab.id);}catch(_){}
    }
    try{await chrome.tabs.remove(tab.id);}catch(_){}
    throw e;
  }
}
async function openInWorkspace(url){
  if(!initialized)throw Error('Pair a Chrome tab first');
  const group=await groupState();
  if(!group)throw Error('No workspace group: create it first');
  const tab=await chrome.tabs.create({
    windowId:group.windowId,url:workspaceURL(url),active:false
  });
  try{
    await chrome.tabs.group({tabIds:tab.id,groupId:group.groupId});
    await changeTab(tab);
    return {opened:true,groupId:group.groupId,
      tab:publicTab(await chrome.tabs.get(tab.id))};
  }catch(e){
    try{await chrome.tabs.remove(tab.id);}catch(_){}
    throw e;
  }
}
async function selectWorkspaceTab(tabId){
  const group=await groupState();
  if(!group)throw Error('No workspace group');
  if(!Number.isInteger(tabId))throw Error('Invalid tab ID');
  const tab=await chrome.tabs.get(tabId);
  if(tab.incognito||tab.active||tab.groupId!==group.groupId)
    throw Error('Target must be an inactive tab in the workspace group');
  await changeTab(tab);
  return {selected:true,tab:publicTab(tab)};
}
async function selectExistingTabById(tabId,host){
  if(!initialized)throw Error('Pair Chrome first');
  if(!Number.isInteger(tabId)||typeof host!=='string')
    throw Error('An explicit tab ID and host are required');
  const tab=await chrome.tabs.get(tabId);
  if(tab.active||tab.incognito||hostOf(tab.url)!==host.toLowerCase())
    throw Error('Target must be an inactive regular tab on the authorized host');
  await changeTab(tab);
  return {selected:true,tab:publicTab(tab)};
}
async function closeWorkspaceTab(tabId){
  const group=await groupState();
  if(!group)throw Error('No workspace group');
  const tab=await chrome.tabs.get(tabId);
  if(tab.incognito||tab.active||tab.groupId!==group.groupId)
    throw Error('Only an inactive workspace tab may be closed');
  if(tabId===targetId){
    // Disconnect before removing the current debugger target.
    await detachDebugger();
  }
  await chrome.tabs.remove(tabId);
  const other=await chrome.tabs.query({groupId:group.groupId});
  if(other.length){
    const next=other.find(t=>!t.active&&!t.incognito);
    if(next)await changeTab(next);
  }
  return {closed:true,tabId,remaining:other.length};
}
