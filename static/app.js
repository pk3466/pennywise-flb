let currentKind = "expense";
let spendingChart = null;
let dashboardData = null;
let predictionTimer = null;
let showAllTransactions = false;

const $ = (id) => document.getElementById(id);
const money = (value) => new Intl.NumberFormat("en-IN", {style:"currency", currency:"INR", maximumFractionDigits:0}).format(value || 0);
const monthPicker = $("monthPicker");
const today = new Date();
monthPicker.value = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}`;

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}
async function api(url, options={}) {
  const response = await fetch(url, {headers:{"Content-Type":"application/json"}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}
async function loadDashboard() {
  const month = monthPicker.value;
  $("exportBtn").href = `/api/export?month=${encodeURIComponent(month)}`;
  dashboardData = await api(`/api/dashboard?month=${encodeURIComponent(month)}`);
  renderDashboard(dashboardData);
}
function renderDashboard(data) {
  $("incomeValue").textContent = money(data.income);
  $("expenseValue").textContent = money(data.expenses);
  $("balanceValue").textContent = money(data.balance);
  $("balanceValue").style.color = data.balance < 0 ? "#c96e66" : "";
  $("savingsValue").textContent = `${data.savings_rate}%`;
  renderChart(data.by_category);
  renderRecommendations(data.recommendations);
  renderTransactions(data.transactions);
  renderBudgets(data);
}
const chartColors = ["#2d8063","#e0a16c","#8295c4","#c77c70","#a9a06d","#8b83b9","#6ca5a1","#c28da9"];
function renderChart(categories) {
  const labels = Object.keys(categories);
  const values = Object.values(categories);
  $("chartEmpty").style.display = labels.length ? "none" : "block";
  if (spendingChart) spendingChart.destroy();
  spendingChart = new Chart($("spendingChart"), {
    type:"doughnut",
    data:{labels, datasets:[{data:values, backgroundColor:chartColors, borderWidth:3, borderColor:"#fff", hoverOffset:5}]},
    options:{responsive:true, maintainAspectRatio:false, cutout:"72%", plugins:{legend:{display:false}, tooltip:{callbacks:{label:(ctx)=>`${ctx.label}: ${money(ctx.raw)}`}}}}
  });
  $("legend").innerHTML = labels.map((label,i)=>`<span class="legend-item"><i class="legend-dot" style="background:${chartColors[i%chartColors.length]}"></i>${label}</span>`).join("");
}
function renderRecommendations(items) {
  $("recommendations").innerHTML = items.map(item=>`<div class="recommendation"><span class="rec-bullet">✦</span><p>${escapeHtml(item)}</p></div>`).join("");
}
function renderTransactions(rows) {
  const visible = showAllTransactions ? rows : rows.slice(0,5);
  if (!visible.length) {
    $("transactionRows").innerHTML = '<tr><td colspan="5" class="empty-row">No transactions yet. Add your first one!</td></tr>';
    return;
  }
  $("transactionRows").innerHTML = visible.map(r=>`
    <tr><td>${escapeHtml(r.description)}</td><td><span class="category-pill">${escapeHtml(r.category)}</span></td>
    <td>${new Date(r.tx_date+"T00:00:00").toLocaleDateString("en-IN",{day:"numeric",month:"short"})}</td>
    <td class="${r.kind==="income"?"amount-income":"amount-expense"}">${r.kind==="income"?"+":"−"}${money(r.amount)}</td>
    <td><button class="delete-btn" title="Delete transaction" data-delete="${r.id}">×</button></td></tr>`).join("");
  document.querySelectorAll("[data-delete]").forEach(btn=>btn.addEventListener("click", async ()=>{
    if (!confirm("Delete this transaction?")) return;
    try { await api(`/api/transactions/${btn.dataset.delete}`, {method:"DELETE"}); toast("Transaction deleted"); await loadDashboard(); }
    catch(e){toast(e.message);}
  }));
}
function renderBudgets(data) {
  const entries = Object.entries(data.budgets || {});
  if (!entries.length) {
    $("budgetProgress").innerHTML = '<p class="muted-empty">Set a category limit to track your budget.</p>';
    return;
  }
  $("budgetProgress").innerHTML = entries.map(([category,limit])=>{
    const spent = data.by_category[category] || 0;
    const percent = limit > 0 ? spent/limit*100 : 0;
    return `<div class="budget-item"><div class="budget-meta"><span>${escapeHtml(category)}</span><strong>${money(spent)} / ${money(limit)}</strong></div><div class="progress-track"><div class="progress-fill ${percent>100?"over":""}" style="width:${Math.min(percent,100)}%"></div></div></div>`;
  }).join("");
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
}
function openModal() {$("transactionModal").classList.add("show");$("description").focus();}
function closeModal() {$("transactionModal").classList.remove("show");$("transactionForm").reset();$("formError").textContent="";$("predictionText").textContent="AI category suggestion will appear as you type.";currentKind="expense";setKind("expense");}
function setKind(kind) {
  currentKind=kind;
  document.querySelectorAll(".type-btn").forEach(btn=>btn.classList.toggle("selected",btn.dataset.kind===kind));
  $("categoryLabel").style.display=kind==="expense"?"flex":"none";
  $("predictionBox").style.display=kind==="expense"?"flex":"none";
}
$("openTransaction").addEventListener("click",openModal);
$("closeModal").addEventListener("click",closeModal);
$("cancelModal").addEventListener("click",closeModal);
$("transactionModal").addEventListener("click",e=>{if(e.target===$("transactionModal"))closeModal();});
document.querySelectorAll(".type-btn").forEach(btn=>btn.addEventListener("click",()=>setKind(btn.dataset.kind)));
$("description").addEventListener("input",()=>{
  clearTimeout(predictionTimer);
  const description=$("description").value.trim();
  if(description.length<3){$("predictionText").textContent="AI category suggestion will appear as you type.";return;}
  predictionTimer=setTimeout(async()=>{
    try {
      const result=await api("/api/predict",{method:"POST",body:JSON.stringify({description})});
      $("category").value=result.category;
      $("predictionText").textContent=`Suggested: ${result.category} · ${result.confidence}% model confidence`;
    } catch(e) {$("predictionText").textContent="AI suggestion unavailable right now.";}
  },450);
});
$("transactionForm").addEventListener("submit",async e=>{
  e.preventDefault();$("formError").textContent="";
  const payload={description:$("description").value.trim(),amount:$("amount").value,kind:currentKind,category:$("category").value,tx_date:$("txDate").value};
  try {
    await api("/api/transactions",{method:"POST",body:JSON.stringify(payload)});
    closeModal();toast("Transaction saved successfully");await loadDashboard();
  } catch(err){$("formError").textContent=err.message;}
});
$("budgetForm").addEventListener("submit",async e=>{
  e.preventDefault();
  try {
    await api("/api/budgets",{method:"POST",body:JSON.stringify({category:$("budgetCategory").value,monthly_limit:$("budgetLimit").value})});
    $("budgetLimit").value="";toast("Monthly budget saved");await loadDashboard();
  } catch(err){toast(err.message);}
});
monthPicker.addEventListener("change",loadDashboard);
$("viewAll").addEventListener("click",()=>{showAllTransactions=!showAllTransactions;$("viewAll").textContent=showAllTransactions?"Show less":"View all";if(dashboardData)renderTransactions(dashboardData.transactions);});
loadDashboard().catch(e=>toast(e.message));
