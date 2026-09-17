from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

if 'function checkoutModal()' in s:
    print('Admin controls patch already applied')
    raise SystemExit(0)

def rep(old, new, label, count=1):
    global s
    if old not in s:
        raise SystemExit(f'{label} marker not found')
    s = s.replace(old, new, count)

def sub(pattern, replacement, label):
    global s
    s, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'{label} marker not found')

rep(
    "let S={profile:null,products:[],cart:[],sales:[],staffs:[],invites:[],tab:'POS',search:'',productCategory:'All Products',recentProductIds:[],pages:{POS:1,Products:1,Sales:1,Reports:1,Quotation:1,Accounts:1}};",
    "let S={profile:null,products:[],cart:[],sales:[],customers:[],staffs:[],invites:[],actionPasswordInfo:null,tab:'POS',search:'',productCategory:'All Products',recentProductIds:[],pages:{POS:1,Products:1,Sales:1,Reports:1,Quotation:1,Customers:1,Accounts:1}};",
    'state'
)

rep(
    '.disabled{opacity:.55}.subnavWrap',
    '.disabled{opacity:.55}.formGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.formGrid .full{grid-column:1/-1}.actionRow{display:flex;gap:6px;flex-wrap:wrap}.miniBtn{padding:6px 9px;border-radius:7px;font-size:10px;font-weight:900}.productActions{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px}.productActions .secondary{background:#fff;color:#087bbb;border:1px solid #1499e4}.productActions .danger{background:#fff;color:#b42318;border:1px solid #fecaca}.settingsBox{margin:0 14px 14px;padding:12px;border:1px solid #d7e9f3;border-radius:10px;background:#f8fcff}.settingsBox b{display:block;margin-bottom:3px}.subnavWrap',
    'css'
)
s = s.replace('@media(max-width:760px){.clock', '@media(max-width:760px){.formGrid{grid-template-columns:1fr}.formGrid .full{grid-column:auto}.clock', 1)
s = s.replace("function categoryOf(p){const x=", "function categoryOf(p){if(p?.category)return p.category;const x=", 1)
s = s.replace("const PAGE_SIZE={POS:12,Products:24,Sales:20,Reports:20,Quotation:20,Accounts:15};", "const PAGE_SIZE={POS:12,Products:24,Sales:20,Reports:20,Quotation:20,Customers:20,Accounts:15};", 1)

sub(
    r"async function products\(\)\{.*?\n\}\nasync function staff\(\)",
    r'''async function products(){
 try{
  const tok=localStorage.getItem(TOKEN_KEY)||'';
  const {data,error}=await sb.rpc('kzies_get_products_local',{p_token:tok});
  if(error||!data?.ok) throw new Error(data?.error||error?.message||'Unable to load products.');
  const rows=Array.isArray(data.products)?data.products:[];
  S.products=rows.map((x,i)=>{const retail=x.retail==null?null:Number(x.retail),wholesale=x.wholesale==null?null:Number(x.wholesale),selling=retail?Math.round(retail*1.3):null;return{id:x.id??i+1,brand:x.brand||'',name:x.name||'',retail,wholesale,notes:x.notes||'',category:x.category||'',selling,income:selling!=null&&wholesale!=null?selling-wholesale:null}}).filter(x=>x.name);
  if(!S.products.length) throw new Error('No products are available yet.');
 }catch(e){console.error('Unable to load products',e);S.products=[]}
}
async function businessData(){await Promise.all([loadSales(),loadCustomers()])}
async function loadSales(){try{const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_list_sales_local',{p_token:tok});if(error||!data?.ok)throw new Error(data?.error||error?.message);S.sales=(data.sales||[]).map(x=>({...x,subtotal:Number(x.subtotal||0),delivery_fee:Number(x.delivery_fee||0),payment_fee:Number(x.payment_fee||0),total:Number(x.total||0),wholesale_total:Number(x.wholesale_total||0),income:Number(x.income||0)}))}catch(e){console.error('Unable to load sales',e);S.sales=[]}}
async function loadCustomers(){try{const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_list_customers_local',{p_token:tok});if(error||!data?.ok)throw new Error(data?.error||error?.message);S.customers=data.customers||[]}catch(e){console.error('Unable to load customers',e);S.customers=[]}}
async function actionPasswordInfo(){try{const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_action_password_info_local',{p_token:tok});if(error||!data?.ok)throw new Error(data?.error||error?.message);S.actionPasswordInfo=data}catch(e){S.actionPasswordInfo={configured:false}}}
async function staff()''',
    'products loader'
)

s = s.replace('await products();shell()', 'await products();await businessData();shell()')

sub(
    r"function cards\(list\)\{.*?\nfunction render\(\)",
    r'''function cards(list,adminActions=false){return `<div class="grid">${list.map(p=>`<article class="product"><div class="thumb">⌨️</div><div class="body"><div class="brandName">${esc(p.brand)}</div><h3>${esc(p.name)}</h3><div class="price">${p.selling?money(p.selling):'Contact us'}</div><div class="cost">Retail: ${p.retail?money(p.retail):'Contact us'}<br>Wholesale: ${p.wholesale?money(p.wholesale):'Contact us'}</div>${p.income!=null?`<div class="income">Income: ${money(p.income)}</div>`:''}<button data-add="${p.id}" ${!p.selling?'disabled':''}>Add to cart</button>${adminActions&&S.profile?.app_role==='Admin'?`<div class="productActions"><button class="secondary" data-edit-product="${p.id}">Edit</button><button class="danger" data-delete-product="${p.id}">Delete</button></div>`:''}</div></article>`).join('')}</div>`}
function bindAdd(){document.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>{const p=S.products.find(x=>x.id==b.dataset.add),q=S.cart.find(x=>x.id===p.id);rememberRecent([p]);q?q.qty++:S.cart.push({...p,qty:1});render()})}
function bindProductAdminActions(){document.querySelectorAll('[data-edit-product]').forEach(b=>b.onclick=()=>editProductModal(Number(b.dataset.editProduct)));document.querySelectorAll('[data-delete-product]').forEach(b=>b.onclick=()=>deleteProduct(Number(b.dataset.deleteProduct)))}
async function deleteProduct(id){if(S.profile?.app_role!=='Admin')return;const p=S.products.find(x=>x.id===id);if(!confirm(`Delete ${p?.name||'this product'} from Kzie’s product list?`))return;const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_delete_product_local',{p_token:tok,p_product_id:id});if(error||!data?.ok){toast(data?.error||error?.message||'Unable to delete product.');return}await products();toast('Product deleted.');shell()}
function editProductModal(id){const p=S.products.find(x=>x.id===id);if(!p||S.profile?.app_role!=='Admin')return;const cats=['Keyboards','Mice','Headsets','Mouse Pads','Cooling & Fans','Thermal Paste','Accessories','Other'];const current=p.category||categoryOf(p);const m=document.createElement('div');m.className='modalBg';m.innerHTML=`<div class="modal"><div class="modalHead"><h2>Edit Product</h2><button class="close">×</button></div><div class="formGrid"><label>Brand<input id="epBrand" value="${esc(p.brand)}"></label><label>Category<select id="epCat">${cats.map(x=>`<option ${x===current?'selected':''}>${x}</option>`).join('')}</select></label><label class="full">Product name<input id="epName" value="${esc(p.name)}"></label><label>Retail price<input id="epRetail" type="number" min="0" step="0.01" value="${p.retail??''}"></label><label>Wholesale price<input id="epWholesale" type="number" min="0" step="0.01" value="${p.wholesale??''}"></label><label class="full">Notes<input id="epNotes" value="${esc(p.notes||'')}"></label></div><p id="epMsg" class="error"></p><button id="epSave" class="primary wide">Save Product</button></div>`;document.body.append(m);m.querySelector('.close').onclick=()=>m.remove();epSave.onclick=async()=>{if(!epName.value.trim()){epMsg.textContent='Product name is required.';return}epSave.disabled=true;epSave.textContent='Saving…';const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_update_product_local',{p_token:tok,p_product_id:id,p_brand:epBrand.value.trim(),p_name:epName.value.trim(),p_retail:epRetail.value===''?null:Number(epRetail.value),p_wholesale:epWholesale.value===''?null:Number(epWholesale.value),p_notes:epNotes.value.trim(),p_category:epCat.value});if(error||!data?.ok){epMsg.textContent=data?.error||error?.message||'Unable to save product.';epSave.disabled=false;epSave.textContent='Save Product';return}m.remove();await products();toast('Product updated.');shell()}}
function render()''',
    'cards/render'
)

rep(
    "${cards(list)}${pager(base,'Products')}`;q.oninput=e=>{S.search=e.target.value;S.pages.Products=1;render()};bindAdd();bindPager();return}",
    "${cards(list,true)}${pager(base,'Products')}`;q.oninput=e=>{S.search=e.target.value;S.pages.Products=1;render()};bindAdd();bindProductAdminActions();bindPager();return}",
    'products render'
)

sub(
    r"pay\.onclick=\(\)=>\{const w=S\.cart\.reduce\(.*?;render\(\)\};return\}",
    "pay.onclick=checkoutModal;return}",
    'payment handler'
)

sub(
    r"if\(t==='Sales'\|\|t==='Reports'\)\{.*?;return\}if\(t==='Accounts'\)",
    r'''if(t==='Sales'||t==='Reports'){const g=S.sales.reduce((a,s)=>a+s.total,0),w=S.sales.reduce((a,s)=>a+s.wholesale_total,0),i=S.sales.reduce((a,s)=>a+s.income,0),list=pageSlice(S.sales,t);c.innerHTML=`<h2>${t}</h2>${t==='Reports'?`<div class="metricGrid"><div class="metric">Sales<b>${S.sales.length}</b></div><div class="metric">Revenue<b>${money(g)}</b></div><div class="metric">Wholesale<b>${money(w)}</b></div><div class="metric">Income<b>${money(i)}</b></div></div>`:''}<div class="light tableWrap"><table class="tbl"><thead><tr><th>Sale</th><th>Customer</th><th>Contact</th><th>Payment</th><th>Date/Time</th><th>Subtotal</th><th>Delivery</th><th>Fee</th><th>Total</th><th>Income</th><th>Actions</th></tr></thead><tbody>${list.length?list.map(x=>`<tr><td>#${x.id}</td><td>${esc(x.customer_name)}</td><td>${esc(x.contact_number)}</td><td>${esc(x.payment_method)}</td><td>${new Date(x.created_at).toLocaleString('en-PH',{timeZone:'Asia/Manila'})}</td><td>${money(x.subtotal)}</td><td>${money(x.delivery_fee)}</td><td>${money(x.payment_fee)}</td><td><b>${money(x.total)}</b></td><td>${money(x.income)}</td><td><div class="actionRow">${S.profile?.app_role==='Admin'?`<button class="secondary miniBtn" data-edit-sale="${x.id}">Edit</button>`:''}<button class="danger miniBtn" data-delete-sale="${x.id}">${S.profile?.app_role==='Admin'?'Delete':'Delete 🔒'}</button></div></td></tr>`).join(''):'<tr><td colspan="11" class="empty">No completed sales yet.</td></tr>'}</tbody></table></div>${pager(S.sales,t)}`;bindPager();bindSaleActions();return}if(t==='Customers'){const list=pageSlice(S.customers,'Customers');c.innerHTML=`<h2>Customers</h2><div class="light tableWrap"><table class="tbl"><thead><tr><th>Name</th><th>Contact</th><th>Home No. / Street / Subdivision</th><th>Barangay</th><th>City</th><th>Province</th><th>ZIP</th><th>Actions</th></tr></thead><tbody>${list.length?list.map(x=>`<tr><td><b>${esc(x.full_name)}</b></td><td>${esc(x.contact_number)}</td><td>${esc(x.address_line)}</td><td>${esc(x.barangay)}</td><td>${esc(x.city)}</td><td>${esc(x.province)}</td><td>${esc(x.zip_code)}</td><td>${S.profile?.app_role==='Admin'?`<div class="actionRow"><button class="secondary miniBtn" data-edit-customer="${x.id}">Edit</button><button class="danger miniBtn" data-delete-customer="${x.id}">Delete</button></div>`:'Admin only'}</td></tr>`).join(''):'<tr><td colspan="8" class="empty">Customer records will appear after completed sales.</td></tr>'}</tbody></table></div>${pager(S.customers,'Customers')}`;bindPager();bindCustomerActions();return}if(t==='Accounts')''',
    'sales/customers'
)

rep(
    "async function staffView(){const c=document.getElementById('content');try{await staff()}catch(e){",
    "async function staffView(){const c=document.getElementById('content');try{await staff();await actionPasswordInfo()}catch(e){",
    'staff view start'
)
rep(
    '<button id="copyReg" class="secondary">Copy Registration Link</button><button id="changeMine" class="primary">Change My Password</button><button id="refreshStaff" class="secondary">↻ Refresh</button>',
    '''<button id="copyReg" class="secondary">Copy Registration Link</button><button id="changeMine" class="primary">Change My Password</button><button id="actionPass" class="secondary">${S.actionPasswordInfo?.configured?'Change Admin Action Password':'Set Admin Action Password'}</button><button id="refreshStaff" class="secondary">↻ Refresh</button>''',
    'accounts toolbar'
)
rep(
    '<div class="staffSummary">',
    '''<div class="settingsBox"><b>Admin Action Password</b><span class="hint">${S.actionPasswordInfo?.configured?'Configured. Staff can use this separate password only when an order/entry must be deleted.':'Not configured yet. Set a password different from your Admin login password.'}</span></div><div class="staffSummary">''',
    'accounts password box'
)
rep(
    "document.getElementById('changeMine').onclick=changeMyPassword;",
    "document.getElementById('changeMine').onclick=changeMyPassword;document.getElementById('actionPass').onclick=setActionPassword;",
    'accounts handlers'
)

helpers = r'''function checkoutModal(){if(!S.cart.length)return;const subtotal=S.cart.reduce((a,p)=>a+p.selling*p.qty,0),m=document.createElement('div');m.className='modalBg';m.innerHTML=`<div class="modal"><div class="modalHead"><h2>Customer & Payment</h2><button class="close">×</button></div><div class="welcome">Complete customer details before saving this sale. Products subtotal: <b>${money(subtotal)}</b></div><div class="formGrid"><label class="full">Customer name<input id="coName" required></label><label>Contact number<input id="coContact" required></label><label>ZIP code<input id="coZip" required></label><label class="full">Home No. / Street / Subdivision<input id="coAddress" required></label><label>Barangay<input id="coBarangay" required></label><label>City<input id="coCity" required></label><label>Province<input id="coProvince" required></label><label>Payment method<select id="coPayment"><option>Cash</option><option>E-Wallet</option><option>Online Banking</option><option>Credit Card</option></select></label><label>Delivery fee<input id="coDelivery" type="number" min="0" step="0.01" placeholder="Leave blank for now"></label><label id="ccFeeWrap" style="display:none">Credit card fee<input id="coCardFee" type="number" min="0" step="0.01" placeholder="Leave blank until fee is set"></label></div><p id="coMsg" class="error"></p><button id="coSave" class="primary wide">Complete Sale</button></div>`;document.body.append(m);m.querySelector('.close').onclick=()=>m.remove();coPayment.onchange=()=>{ccFeeWrap.style.display=coPayment.value==='Credit Card'?'block':'none';if(coPayment.value!=='Credit Card')coCardFee.value=''};coSave.onclick=async()=>{const vals=[coName,coContact,coAddress,coBarangay,coCity,coProvince,coZip];if(vals.some(x=>!x.value.trim())){coMsg.textContent='Please complete the customer name, contact number, and all address fields.';return}coSave.disabled=true;coSave.textContent='Saving sale…';const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_create_sale_local',{p_token:tok,p_customer_name:coName.value.trim(),p_contact_number:coContact.value.trim(),p_address_line:coAddress.value.trim(),p_barangay:coBarangay.value.trim(),p_city:coCity.value.trim(),p_province:coProvince.value.trim(),p_zip_code:coZip.value.trim(),p_payment_method:coPayment.value,p_delivery_fee:coDelivery.value===''?0:Number(coDelivery.value),p_payment_fee:coPayment.value==='Credit Card'&&coCardFee.value!==''?Number(coCardFee.value):0,p_items:S.cart.map(x=>({id:x.id,qty:x.qty}))});if(error||!data?.ok){coMsg.textContent=data?.error||error?.message||'Unable to complete sale.';coSave.disabled=false;coSave.textContent='Complete Sale';return}S.cart=[];m.remove();await businessData();toast(`Sale #${data.sale_id} completed.`);render()}}
function bindSaleActions(){document.querySelectorAll('[data-edit-sale]').forEach(b=>b.onclick=()=>editSaleModal(Number(b.dataset.editSale)));document.querySelectorAll('[data-delete-sale]').forEach(b=>b.onclick=()=>deleteSale(Number(b.dataset.deleteSale)))}
function editSaleModal(id){if(S.profile?.app_role!=='Admin')return;const x=S.sales.find(s=>Number(s.id)===id);if(!x)return;const methods=['Cash','E-Wallet','Online Banking','Credit Card'];const m=document.createElement('div');m.className='modalBg';m.innerHTML=`<div class="modal"><div class="modalHead"><h2>Edit Sale #${id}</h2><button class="close">×</button></div><div class="hint">Product items are preserved. You can correct customer, payment, and delivery details here.</div><div class="formGrid"><label class="full">Customer name<input id="esName" value="${esc(x.customer_name)}"></label><label>Contact number<input id="esContact" value="${esc(x.contact_number)}"></label><label>ZIP code<input id="esZip" value="${esc(x.zip_code)}"></label><label class="full">Home No. / Street / Subdivision<input id="esAddress" value="${esc(x.address_line)}"></label><label>Barangay<input id="esBarangay" value="${esc(x.barangay)}"></label><label>City<input id="esCity" value="${esc(x.city)}"></label><label>Province<input id="esProvince" value="${esc(x.province)}"></label><label>Payment method<select id="esPayment">${methods.map(v=>`<option ${v===x.payment_method?'selected':''}>${v}</option>`).join('')}</select></label><label>Delivery fee<input id="esDelivery" type="number" min="0" step="0.01" value="${x.delivery_fee||''}"></label><label>Payment/Card fee<input id="esFee" type="number" min="0" step="0.01" value="${x.payment_fee||''}"></label></div><p id="esMsg" class="error"></p><button id="esSave" class="primary wide">Save Changes</button></div>`;document.body.append(m);m.querySelector('.close').onclick=()=>m.remove();esSave.onclick=async()=>{esSave.disabled=true;const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_update_sale_local',{p_token:tok,p_sale_id:id,p_customer_name:esName.value.trim(),p_contact_number:esContact.value.trim(),p_address_line:esAddress.value.trim(),p_barangay:esBarangay.value.trim(),p_city:esCity.value.trim(),p_province:esProvince.value.trim(),p_zip_code:esZip.value.trim(),p_payment_method:esPayment.value,p_delivery_fee:esDelivery.value===''?0:Number(esDelivery.value),p_payment_fee:esFee.value===''?0:Number(esFee.value)});if(error||!data?.ok){esMsg.textContent=data?.error||error?.message||'Unable to update sale.';esSave.disabled=false;return}m.remove();await businessData();toast('Sale updated.');render()}}
async function deleteSale(id){if(S.profile?.app_role==='Admin'){if(!confirm(`Delete sale #${id}?`))return;return runDeleteSale(id,null)}const m=document.createElement('div');m.className='modalBg';m.innerHTML=`<div class="modal"><div class="modalHead"><h2>Admin Approval Required</h2><button class="close">×</button></div><div class="welcome">Staff deletion of sale #${id} requires the separate Admin Action Password.</div><label>Admin Action Password<input id="dap" type="password"></label><p id="dam" class="error"></p><button id="daGo" class="danger wide">Delete Sale</button></div>`;document.body.append(m);m.querySelector('.close').onclick=()=>m.remove();daGo.onclick=async()=>{daGo.disabled=true;const ok=await runDeleteSale(id,dap.value,dam);if(ok)m.remove();else daGo.disabled=false}}
async function runDeleteSale(id,password,msgEl){const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_delete_sale_local',{p_token:tok,p_sale_id:id,p_action_password:password});if(error||!data?.ok){const msg=data?.error||error?.message||'Unable to delete sale.';if(msgEl)msgEl.textContent=msg;else toast(msg);return false}await businessData();toast(`Sale #${id} deleted.`);render();return true}
function bindCustomerActions(){document.querySelectorAll('[data-edit-customer]').forEach(b=>b.onclick=()=>editCustomerModal(b.dataset.editCustomer));document.querySelectorAll('[data-delete-customer]').forEach(b=>b.onclick=()=>deleteCustomer(b.dataset.deleteCustomer))}
function editCustomerModal(id){if(S.profile?.app_role!=='Admin')return;const x=S.customers.find(c=>c.id===id);if(!x)return;const m=document.createElement('div');m.className='modalBg';m.innerHTML=`<div class="modal"><div class="modalHead"><h2>Edit Customer</h2><button class="close">×</button></div><div class="formGrid"><label class="full">Customer name<input id="ecName" value="${esc(x.full_name)}"></label><label>Contact number<input id="ecContact" value="${esc(x.contact_number)}"></label><label>ZIP code<input id="ecZip" value="${esc(x.zip_code)}"></label><label class="full">Home No. / Street / Subdivision<input id="ecAddress" value="${esc(x.address_line)}"></label><label>Barangay<input id="ecBarangay" value="${esc(x.barangay)}"></label><label>City<input id="ecCity" value="${esc(x.city)}"></label><label>Province<input id="ecProvince" value="${esc(x.province)}"></label></div><p id="ecMsg" class="error"></p><button id="ecSave" class="primary wide">Save Customer</button></div>`;document.body.append(m);m.querySelector('.close').onclick=()=>m.remove();ecSave.onclick=async()=>{ecSave.disabled=true;const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_update_customer_local',{p_token:tok,p_customer_id:id,p_full_name:ecName.value.trim(),p_contact_number:ecContact.value.trim(),p_address_line:ecAddress.value.trim(),p_barangay:ecBarangay.value.trim(),p_city:ecCity.value.trim(),p_province:ecProvince.value.trim(),p_zip_code:ecZip.value.trim()});if(error||!data?.ok){ecMsg.textContent=data?.error||error?.message||'Unable to update customer.';ecSave.disabled=false;return}m.remove();await loadCustomers();toast('Customer updated.');render()}}
async function deleteCustomer(id){if(S.profile?.app_role!=='Admin')return;const x=S.customers.find(c=>c.id===id);if(!confirm(`Delete customer ${x?.full_name||''}? Existing sales will keep their customer snapshot.`))return;const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_delete_customer_local',{p_token:tok,p_customer_id:id});if(error||!data?.ok){toast(data?.error||error?.message||'Unable to delete customer.');return}await loadCustomers();toast('Customer deleted.');render()}
function setActionPassword(){const m=document.createElement('div');m.className='modalBg';m.innerHTML=`<div class="modal"><div class="modalHead"><h2>${S.actionPasswordInfo?.configured?'Change':'Set'} Admin Action Password</h2><button class="close">×</button></div><div class="welcome">This is separate from your Admin login password. Staff will need it only to delete protected order entries.</div><label>Your current Admin login password<input id="apLogin" type="password"></label><label>New Admin Action Password<input id="ap1" type="password" minlength="8"></label><label>Confirm Action Password<input id="ap2" type="password" minlength="8"></label><p id="apMsg" class="error"></p><button id="apSave" class="primary wide">Save Action Password</button></div>`;document.body.append(m);m.querySelector('.close').onclick=()=>m.remove();apSave.onclick=async()=>{if(ap1.value.length<8){apMsg.textContent='Use at least 8 characters.';return}if(ap1.value!==ap2.value){apMsg.textContent='Passwords do not match.';return}apSave.disabled=true;const tok=localStorage.getItem(TOKEN_KEY)||'';const {data,error}=await sb.rpc('kzies_set_action_password_local',{p_token:tok,p_login_password:apLogin.value,p_new_action_password:ap1.value});if(error||!data?.ok){apMsg.textContent=data?.error||error?.message||'Unable to save action password.';apSave.disabled=false;return}m.remove();await actionPasswordInfo();toast('Admin Action Password saved.');staffView()}}
'''
rep('async function staffView()', helpers + 'async function staffView()', 'staff helpers')

p.write_text(s, encoding='utf-8')
print('Patched admin controls, protected deletes, customer checkout, payments, and delivery fee')
