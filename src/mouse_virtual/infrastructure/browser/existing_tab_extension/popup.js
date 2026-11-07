'use strict';
const status = document.getElementById('status');
const tokenInput = document.getElementById('token');
const automatic = document.getElementById('automatic');
function show(message){status.textContent=String(message);}
function request(payload){
  return new Promise(resolve=>{
    chrome.runtime.sendMessage(payload,result=>{
      if(chrome.runtime.lastError){
        resolve({ok:false,error:chrome.runtime.lastError.message});
      }else resolve(result||{ok:false,error:'Sin respuesta del motor'});
    });
  });
}
async function updateStatus(){
  const result=await request({kind:'status'});
  if(!result.ok){show(result.error||'Sin respuesta');return;}
  automatic.checked=result.remembered ? result.autoFollow : true;
  if(result.connected)show('Conectado. La reconexión se realizará automáticamente.');
  else if(result.remembered)show('Conexión guardada. Reconectando cuando esté disponible el servicio.');
  else show('Sin emparejar. El código solo se necesita la primera vez.');
}
document.getElementById('connect').addEventListener('click',async()=>{
  const token=tokenInput.value.trim();
  const tabs=await chrome.tabs.query({active:true,currentWindow:true});
  if(tabs.length!==1 || typeof tabs[0].id!=='number'){
    show('Selecciona una pestaña válida.');return;
  }
  const remembered=await request({kind:'status'});
  if(!token && !remembered.remembered){
    show('Introduce el código únicamente para la primera conexión.');return;
  }
  if(token && !/^[0-9a-f]{64}$/.test(token)){
    show('Código de emparejamiento inválido.');return;
  }
  show('Conectando la pestaña seleccionada...');
  const kind=token?'attach':'switch';
  const result=await request({kind,tabId:tabs[0].id,...(token?{token}:{})});
  tokenInput.value='';
  show(result.ok?'Pestaña vinculada. Reconexión automática activada.':
    'Error: '+(result.error||'Desconocido'));
  if(result.ok)await request({kind:'auto-follow',enabled:automatic.checked});
});
document.getElementById('reconnect').addEventListener('click',async()=>{
  show('Comprobando el servicio...');
  await request({kind:'reconnect'});
  await updateStatus();
});
document.getElementById('disconnect').addEventListener('click',async()=>{
  const result=await request({kind:'detach'});
  show(result.ok?'Conexión revocada.':'Error: '+result.error);
});
automatic.addEventListener('change',async()=>{
  const result=await request({kind:'auto-follow',enabled:automatic.checked});
  if(!result.ok)show(result.error||'Primero empareja una pestaña.');
});
updateStatus();
