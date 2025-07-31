const token = localStorage.getItem('accessToken');
if (!token) window.location.href='login.html';
function decode(t){try{return JSON.parse(atob(t.split('.')[1]));}catch(e){return{}}}
if(decode(token).user!=='admin'){window.location.href='index.html';}
const headers={Authorization:`Bearer ${token}`,'Content-Type':'application/json'};
const tbody=document.querySelector('#userTable tbody');
function loadUsers(){fetch('/api/users',{headers}).then(r=>r.json()).then(arr=>{tbody.innerHTML='';arr.forEach(u=>{const tr=document.createElement('tr');tr.innerHTML=`<td>${u}</td><td>${u==='admin'?'':`<button class='icon-btn' data-u='${u}' title='Delete'>&#128465;</button>`}</td>`;tbody.appendChild(tr);});});}
loadUsers();

document.getElementById('addBtn').addEventListener('click',()=>{
  const u=document.getElementById('newUser').value.trim();
  const p=document.getElementById('newPass').value.trim();
  if(!u||!p)return;
  fetch('/api/users',{method:'POST',headers,body:JSON.stringify({username:u,password:p})}).then(r=>r.json()).then(()=>{loadUsers();});
});

tbody.addEventListener('click',(e)=>{
  if(e.target.classList.contains('icon-btn')){
    const u=e.target.dataset.u;
    fetch(`/api/users/${u}`,{method:'DELETE',headers}).then(()=>loadUsers());
  }
});

document.getElementById('changePassBtn').addEventListener('click',()=>{
  const p=document.getElementById('newAdminPass').value.trim();
  if(!p) return;
  fetch('/api/users/admin',{method:'PUT',headers,body:JSON.stringify({password:p})}).then(r=>r.json()).then(()=>{
    alert('Password updated');
    document.getElementById('newAdminPass').value='';
  });
});

document.getElementById('logout').addEventListener('click',()=>{
  localStorage.removeItem('accessToken');
  window.location.href='login.html';
});

document.getElementById('backBtn').addEventListener('click',()=>{
  window.location.href='index.html';
}); 