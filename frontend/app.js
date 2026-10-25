const $ = (id) => document.getElementById(id);
let items = [];
const say = (message) => { $('status').textContent = message; };
async function request(path, options = {}) {
  const res = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } });
  if (!res.ok) throw new Error((await res.text()) || `Request failed (${res.status})`);
  return res.status === 204 ? null : res.json();
}
const cell = (row, value) => { const td=document.createElement('td'); td.textContent=String(value); row.appendChild(td); return td; };
async function refresh() {
  try {
    const [products, alerts] = await Promise.all([request('/api/products'), request('/api/alerts')]);
    items = products;
    $('productCount').textContent = products.length;
    $('alertCount').textContent = alerts.length;
    $('products').replaceChildren();
    for (const p of products) {
      const tr = document.createElement('tr');
      cell(tr, p.name); cell(tr, p.quantity); cell(tr, p.min_stock); cell(tr, p.price.toFixed(2));
      const status = cell(tr, p.quantity <= p.min_stock ? 'Low stock' : 'OK');
      status.className = p.quantity <= p.min_stock ? 'low' : 'ok';
      const actions = document.createElement('td');
      const edit = document.createElement('button'); edit.textContent='Edit'; edit.className='secondary';
      edit.addEventListener('click', () => editProduct(p));
      const remove = document.createElement('button'); remove.textContent='Delete'; remove.className='danger';
      remove.addEventListener('click', () => deleteProduct(p.id));
      actions.append(edit, remove); tr.appendChild(actions); $('products').appendChild(tr);
    }
    $('alerts').replaceChildren();
    if (!alerts.length) { const li=document.createElement('li'); li.textContent='No low-stock products.'; $('alerts').append(li); }
    for (const alert of alerts) { const li=document.createElement('li'); li.textContent=`${alert.product}: ${alert.quantity} remaining (minimum: ${alert.min_stock})`; $('alerts').append(li); }
    say('');
  } catch (err) { say(`Error: ${err.message}`); }
}
$('productForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const fd=new FormData(event.currentTarget);
  const item={ name:String(fd.get('name')).trim(), quantity:Number(fd.get('quantity')), min_stock:Number(fd.get('min_stock')), price:Number(fd.get('price')) };
  try { await request('/api/products', {method:'POST',body:JSON.stringify(item)}); event.currentTarget.reset(); await refresh(); }
  catch (err) { say(`Error: ${err.message}`); }
});
async function editProduct(p) {
  const value=prompt(`New quantity for ${p.name}:`,String(p.quantity));
  if (value === null) return;
  if (value.trim()==='' || !Number.isInteger(Number(value)) || Number(value)<0) { say('Quantity must be a nonnegative integer.'); return; }
  try { await request(`/api/products/${p.id}`,{method:'PUT',body:JSON.stringify({...p,quantity:Number(value)})}); await refresh(); }
  catch(err){say(`Error: ${err.message}`);}
}
async function deleteProduct(id) {
  if (!confirm('Delete this product?')) return;
  try {await request(`/api/products/${id}`,{method:'DELETE'});await refresh();}
  catch(err){say(`Error: ${err.message}`);}
}
refresh();

// Poll for changes made by other managers every 10 seconds.
setInterval(refresh, 10000);
