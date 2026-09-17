from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

if 'function categoryOf(p)' in s:
    print('UX patch already applied')
    raise SystemExit(0)

old = "let S={profile:null,products:[],cart:[],sales:[],staffs:[],invites:[],tab:'POS',search:''};"
new = "let S={profile:null,products:[],cart:[],sales:[],staffs:[],invites:[],tab:'POS',search:'',productCategory:'All Products',recentProductIds:[],pages:{POS:1,Products:1,Sales:1,Reports:1,Quotation:1,Accounts:1}};"
if old not in s:
    raise SystemExit('State marker not found')
s = s.replace(old, new, 1)

css_old = '.disabled{opacity:.55}@media(max-width:1050px)'
css_new = '.disabled{opacity:.55}.subnavWrap{margin:-2px 0 8px 42px;display:grid;gap:3px}.subnav{display:flex;align-items:center;justify-content:space-between;gap:8px;width:100%;padding:6px 8px;border:0;border-radius:8px;background:transparent;color:#7f9bb3;font-size:10px;font-weight:800;text-align:left}.subnav:hover,.subnav.active{background:#0e2b43;color:#ffcc28}.subnav span{font-size:9px;color:#69c9ff}.pager{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;margin:16px 0 4px}.pager button{padding:7px 11px;border:1px solid #2b6f97;border-radius:8px;background:#0e2235;color:#dff4ff;font-weight:800}.pager button:disabled{opacity:.35}.pageInfo{font-size:11px;color:#94a3b8}@media(max-width:1050px)'
if css_old not in s:
    raise SystemExit('CSS marker not found')
s = s.replace(css_old, css_new, 1)

toast_marker = "function toast(m){const x=document.createElement('div');x.className='toast';x.textContent=m;document.body.append(x);setTimeout(()=>x.remove(),2300)}"
helpers = r'''function toast(m){const x=document.createElement('div');x.className='toast';x.textContent=m;document.body.append(x);setTimeout(()=>x.remove(),2300)}
const PAGE_SIZE={POS:12,Products:24,Sales:20,Reports:20,Quotation:20,Accounts:15};
function categoryOf(p){const x=((p?.name||'')+' '+(p?.brand||'')).toLowerCase();if(/mouse pad/.test(x))return 'Mouse Pads';if(/keyboard|keycap|switch puller/.test(x))return 'Keyboards';if(/headset|headphone|earphone/.test(x))return 'Headsets';if(/mouse/.test(x))return 'Mice';if(/thermal paste/.test(x))return 'Thermal Paste';if(/cpu fan|case fan|fan hub|cooler|air cooler|argb.*fan|reverse.*fan|forward.*fan|interstellar|prism|meteor|starlink|transwarp|galaxy v2|infinite|star trails/.test(x))return 'Cooling & Fans';if(/cable|hub|controller/.test(x))return 'Accessories';return 'Other'}
function productCategories(){const order=['All Products','Keyboards','Mice','Headsets','Mouse Pads','Cooling & Fans','Thermal Paste','Accessories','Other'];return order.map(name=>({name,count:name==='All Products'?S.products.length:S.products.filter(p=>categoryOf(p)===name).length})).filter(x=>x.name==='All Products'||x.count>0)}
function pageSlice(list,key){const size=PAGE_SIZE[key]||20,total=Math.max(1,Math.ceil(list.length/size));S.pages[key]=Math.min(Math.max(1,S.pages[key]||1),total);const start=(S.pages[key]-1)*size;return list.slice(start,start+size)}
function pager(list,key){const size=PAGE_SIZE[key]||20,total=Math.max(1,Math.ceil(list.length/size)),page=Math.min(Math.max(1,S.pages[key]||1),total);if(list.length<=size)return '';return `<div class="pager"><button data-page-key="${key}" data-page-dir="-1" ${page<=1?'disabled':''}>‹ Previous</button><span class="pageInfo">Page ${page} of ${total} • ${list.length} items</span><button data-page-key="${key}" data-page-dir="1" ${page>=total?'disabled':''}>Next ›</button></div>`}
function bindPager(){document.querySelectorAll('[data-page-key]').forEach(b=>b.onclick=()=>{const key=b.dataset.pageKey,dir=Number(b.dataset.pageDir||0);S.pages[key]=Math.max(1,(S.pages[key]||1)+dir);key==='Accounts'?staffView():render()})}
function rememberRecent(list){for(const p of list.slice(0,12)){S.recentProductIds=[p.id,...S.recentProductIds.filter(id=>id!==p.id)].slice(0,24)}}
function navHtml(n){return n.map(x=>{const main=`<button class="nav ${S.tab===x?'active':''}" data-tab="${x}"><span class="ico">${icons[x]}</span><span>${x}</span></button>`;if(x!=='Products'||S.tab!=='Products')return main;const subs=productCategories().map(cat=>`<button class="subnav ${S.productCategory===cat.name?'active':''}" data-category="${esc(cat.name)}"><span>${esc(cat.name)}</span><span>${cat.count}</span></button>`).join('');return main+`<div class="subnavWrap">${subs}</div>`}).join('')}
'''
if toast_marker not in s:
    raise SystemExit('Toast marker not found')
s = s.replace(toast_marker, helpers, 1)

nav_old = "${n.map(x=>`<button class=\"nav ${S.tab===x?'active':''}\" data-tab=\"${x}\"><span class=\"ico\">${icons[x]}</span><span>${x}</span></button>`).join('')}"
if nav_old not in s:
    raise SystemExit('Sidebar HTML marker not found')
s = s.replace(nav_old, "${navHtml(n)}", 1)

old_bind = "document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{S.tab=b.dataset.tab;shell()});out.onclick=logoutLocal;render();"
new_bind = "document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{S.tab=b.dataset.tab;if(S.tab==='Products')S.pages.Products=1;shell()});document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>{S.tab='Products';S.productCategory=b.dataset.category;S.search='';S.pages.Products=1;shell()});out.onclick=logoutLocal;render();"
if old_bind not in s:
    raise SystemExit('Sidebar bind marker not found')
s = s.replace(old_bind, new_bind, 1)

old_bindadd = "function bindAdd(){document.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>{const p=S.products.find(x=>x.id==b.dataset.add),q=S.cart.find(x=>x.id===p.id);q?q.qty++:S.cart.push({...p,qty:1});render()})}"
new_bindadd = "function bindAdd(){document.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>{const p=S.products.find(x=>x.id==b.dataset.add),q=S.cart.find(x=>x.id===p.id);rememberRecent([p]);q?q.qty++:S.cart.push({...p,qty:1});render()})}"
if old_bindadd not in s:
    raise SystemExit('bindAdd marker not found')
s = s.replace(old_bindadd, new_bindadd, 1)

pos_old = "if(t==='POS'){const list=(S.search?S.products.filter(p=>(p.name+' '+p.brand).toLowerCase().includes(S.search.toLowerCase())):S.products.slice(0,8)).slice(0,24),total=S.cart.reduce((a,p)=>a+p.selling*p.qty,0);"
pos_new = "if(t==='POS'){const searched=S.search.trim()?S.products.filter(p=>(p.name+' '+p.brand).toLowerCase().includes(S.search.toLowerCase())):[];if(S.search.trim())rememberRecent(searched);const recent=S.recentProductIds.map(id=>S.products.find(p=>p.id===id)).filter(Boolean),base=S.search.trim()?searched:recent,list=pageSlice(base,'POS'),total=S.cart.reduce((a,p)=>a+p.selling*p.qty,0);"
if pos_old not in s:
    raise SystemExit('POS marker not found')
s = s.replace(pos_old, pos_new, 1)

pos_cards = "<div class=\"label\">${S.search?'SEARCH RESULTS':'RECENTLY ORDERED'}</div>${cards(list)}</section>"
pos_cards_new = "<div class=\"label\">${S.search?'SEARCH RESULTS':'RECENTLY SEARCHED'}</div>${list.length?cards(list):'<div class=\"empty\">Search for a product to start. Recently searched products will stay here.</div>'}${pager(base,'POS')}</section>"
if pos_cards not in s:
    raise SystemExit('POS cards marker not found')
s = s.replace(pos_cards, pos_cards_new, 1)

pos_input = "q.oninput=e=>{S.search=e.target.value;render()};bindAdd();document.querySelectorAll('[data-m]')"
pos_input_new = "q.oninput=e=>{S.search=e.target.value;S.pages.POS=1;render()};bindAdd();bindPager();document.querySelectorAll('[data-m]')"
if pos_input not in s:
    raise SystemExit('POS input marker not found')
s = s.replace(pos_input, pos_input_new, 1)

prod_pattern = r"if\(t==='Products'\)\{.*?;return\}if\(t==='Quotation'\)"
prod_new = r'''if(t==='Products'){let base=S.products.filter(p=>S.productCategory==='All Products'||categoryOf(p)===S.productCategory);if(S.search.trim())base=base.filter(p=>(p.name+' '+p.brand).toLowerCase().includes(S.search.toLowerCase()));const list=pageSlice(base,'Products');c.innerHTML=`<h2>Products</h2><p class="muted">Selling Price = Retail + 30%, rounded to the nearest peso. Income = Selling − Wholesale.</p><input id="q" class="search" value="${esc(S.search)}" placeholder="Search all products…"><div class="label">${base.length} PRODUCTS</div>${cards(list)}${pager(base,'Products')}`;q.oninput=e=>{S.search=e.target.value;S.pages.Products=1;render()};bindAdd();bindPager();return}if(t==='Quotation')'''
s, n = re.subn(prod_pattern, prod_new, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Products branch not found')

quote_pattern = r"if\(t==='Quotation'\)\{.*?;return\}if\(t==='Sales'\|\|t==='Reports'\)"
quote_new = r'''if(t==='Quotation'){const total=S.cart.reduce((a,p)=>a+p.selling*p.qty,0),list=pageSlice(S.cart,'Quotation');c.innerHTML=`<h2>Quotation</h2><div class="light" style="padding:18px">${S.cart.length?list.map(x=>`<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #eee"><span>${x.qty} × ${esc(x.name)}</span><b>${money(x.qty*x.selling)}</b></div>`).join(''):'No products in quotation.'}${S.cart.length?`<div class="total"><span>Total</span><span>${money(total)}</span></div><button onclick="window.print()" class="primary">Print quotation</button>`:''}</div>${pager(S.cart,'Quotation')}`;bindPager();return}if(t==='Sales'||t==='Reports')'''
s, n = re.subn(quote_pattern, quote_new, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Quotation branch not found')

sales_pattern = r"if\(t==='Sales'\|\|t==='Reports'\)\{.*?;return\}if\(t==='Accounts'\)"
sales_new = r'''if(t==='Sales'||t==='Reports'){const g=S.sales.reduce((a,s)=>a+s.total,0),w=S.sales.reduce((a,s)=>a+s.wholesale,0),i=S.sales.reduce((a,s)=>a+s.income,0),list=pageSlice(S.sales,t);c.innerHTML=`<h2>${t}</h2>${t==='Reports'?`<div class="metricGrid"><div class="metric">Sales<b>${S.sales.length}</b></div><div class="metric">Revenue<b>${money(g)}</b></div><div class="metric">Wholesale<b>${money(w)}</b></div><div class="metric">Income<b>${money(i)}</b></div></div>`:''}<div class="light tableWrap"><table class="tbl"><thead><tr><th>Sale</th><th>Customer</th><th>Date/Time</th><th>Total</th><th>Wholesale</th><th>Income</th></tr></thead><tbody>${list.length?list.map(s=>`<tr><td>${s.id}</td><td>${s.customer}</td><td>${s.time}</td><td>${money(s.total)}</td><td>${money(s.wholesale)}</td><td>${money(s.income)}</td></tr>`).join(''):'<tr><td colspan="6" class="empty">No completed sales yet.</td></tr>'}</tbody></table></div>${pager(S.sales,t)}`;bindPager();return}if(t==='Accounts')'''
s, n = re.subn(sales_pattern, sales_new, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('Sales/Reports branch not found')

staff_counts = "const pending=S.staffs.filter(s=>s.status==='Pending').length,active=S.staffs.filter(s=>s.status==='Active').length,disabled=S.staffs.filter(s=>s.status==='Disabled').length;c.innerHTML="
staff_counts_new = "const pending=S.staffs.filter(s=>s.status==='Pending').length,active=S.staffs.filter(s=>s.status==='Active').length,disabled=S.staffs.filter(s=>s.status==='Disabled').length,staffPage=pageSlice(S.staffs,'Accounts');c.innerHTML="
if staff_counts not in s:
    raise SystemExit('Accounts count marker not found')
s = s.replace(staff_counts, staff_counts_new, 1)

staff_map = "${S.staffs.map(s=>{const self=s.id===S.profile.id;return `"
if staff_map not in s:
    raise SystemExit('Accounts map marker not found')
s = s.replace(staff_map, "${staffPage.map(s=>{const self=s.id===S.profile.id;return `", 1)

staff_end = "</tbody></table></div></div>`;document.getElementById('refreshStaff').onclick=staffView;"
staff_end_new = "</tbody></table></div>${pager(S.staffs,'Accounts')}</div>`;bindPager();document.getElementById('refreshStaff').onclick=staffView;"
if staff_end not in s:
    raise SystemExit('Accounts end marker not found')
s = s.replace(staff_end, staff_end_new, 1)

p.write_text(s, encoding='utf-8')
print('Patched Kzie product UX')
