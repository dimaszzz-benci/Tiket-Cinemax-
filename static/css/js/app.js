document.addEventListener('DOMContentLoaded',()=>{
  const grid=document.getElementById('seatGrid');if(!grid)return;
  const taken=['A3','B5','C2','D7','E4'];
  grid.querySelectorAll('.seat').forEach(s=>{
    if(taken.includes(s.dataset.id))s.classList.add('taken');
    s.onclick=()=>{if(s.classList.contains('taken'))return;s.classList.toggle('selected');updateSummary()}
  });
  function updateSummary(){
    const sel=[...grid.querySelectorAll('.seat.selected')].map(s=>s.dataset.id);
    document.getElementById('selSeats').textContent=sel.length?sel.join(', '):'-';
    const price=parseInt(document.getElementById('priceVal').value)||0;
    const total=sel.length*price;
    document.getElementById('totalPrice').textContent=`Rp ${total.toLocaleString('id-ID')}`;
    if(sel.length<3||sel.length>8)document.getElementById('bkForm').querySelector('button').disabled=true;
    else document.getElementById('bkForm').querySelector('button').disabled=false;
  }
  // Auto-fill hidden seats for form submission
  document.getElementById('bkForm').onsubmit=e=>{
    const sel=[...document.querySelectorAll('.seat.selected')].map(s=>s.dataset.id);
    if(sel.length<3||sel.length>8){e.preventDefault();alert('Wajib pilih 3-8 kursi!')}
    // Append inputs dynamically
    sel.forEach(id=>{const i=document.createElement('input');i.type='hidden';i.name='seats';i.value=id;e.target.appendChild(i)});
  };
});
