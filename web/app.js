const qs=new URLSearchParams(location.search),session=qs.get("session"),tg=window.Telegram?.WebApp;
if(tg){tg.ready();tg.expand();tg.setHeaderColor("#020718");tg.setBackgroundColor("#020718")}
const screen=document.getElementById("screen"),conn=document.getElementById("conn");
let data=null,status=null,poll=null;
const esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
async function get(path){const r=await fetch(path);return r.json()}
async function loadSession(){if(!session){conn.textContent="Нет сессии";return}const r=await get("/api/session?session="+encodeURIComponent(session));if(r.ok){conn.textContent="Сессия готова";data=r}else conn.textContent="Сессия недоступна"}
async function start(){const r=await fetch("/api/test/start?session="+encodeURIComponent(session),{method:"POST"});if(!r.ok)return;clearInterval(poll);poll=setInterval(refresh,700);await refresh()}
async function refresh(){status=await get("/api/test/status?session="+encodeURIComponent(session));render("home");if(status.status==="completed"||status.status==="failed"){clearInterval(poll);if(status.status==="completed"){const r=await get("/api/test/report?session="+encodeURIComponent(session));if(r.ok)data={...data,report:r.report};render("results")}}}
function badge(s){return "<span class='badge "+(s==="PASS"?"pass":s==="WARNING"?"warning":s==="FAIL"?"failure":"not")+"'>"+esc(s)+"</span>"}
function render(name){document.querySelectorAll(".nav button").forEach(b=>b.classList.toggle("active",b.dataset.screen===name));({home,results,errors,infra,historyScreen}[name]||home)()}
function quick(){return "<div class='quick'>"+
"<button onclick='render("results")'><span class='ico'>▥</span><small>Результаты</small></button>"+
"<button onclick='render("errors")'><span class='ico'>⚠</span><small>Ошибки</small></button>"+
"<button onclick='render("infra")'><span class='ico'>◉</span><small>GitHub</small></button>"+
"<button onclick='render("infra")'><span class='ico'>☁</span><small>Render</small></button></div>"}
function home(){
const t=data?.target||{},running=status?.status==="running",p=status?.progress||0;
if(running){const total=status.total||41,current=status.current||Math.round(total*p/100);screen.innerHTML="<div class='screen'><div class='hero'><div class='process-title'>Идёт полная проверка...</div><div class='process-sub'>Проверяем все 41 категорию проекта.</div><div class='ring' style='--p:"+p+"%'><b>"+current+"/"+total+"</b></div><div class='center'><b>"+p+"%</b><p class='mini'>"+esc(status.current_name||"Подготовка...")+"</p></div><div class='progress'><i style='width:"+p+"%'></i></div><div class='list'><div class='card'><div class='row'><span>Текущая категория</span><b>"+current+" / "+total+"</b></div><div class='mini'>Тестировщик читает GitHub и Render без изменений.</div></div></div></div></div>";return}
screen.innerHTML="<div class='screen'><div class='hero'><div class='logo'>⌕</div><h1>PMProTest Bot</h1><div class='subtitle'>Полная read-only проверка проекта</div><span class='readonly'>READ-ONLY</span><div class='info-line'>◉ Только чтение · Ничего не изменяет</div><div class='target'><div class='mini'>Тестируемый бот</div><strong>"+esc(t.name||"—")+"</strong><span>"+esc(t.username||"—")+"</span><button class='edit' onclick='alert("Изменение сессии пока недоступно")'>✎</button></div><button class='test-btn' onclick='start()'>⌕<br>ТЕСТИРОВАТЬ<small>Полная проверка · 41 категория</small></button>"+quick()+"<div class='grid'><div class='card'><h3>Категории</h3><div class='stat'>41</div><div class='mini'>полная проверка</div></div><div class='card'><h3>Режим</h3><div class='stat'>READ</div><div class='mini'>без изменений</div></div></div></div></div>"
}
function results(){
const r=data?.report;if(!r){screen.innerHTML="<div class='screen'><div class='section-title'>Результаты</div><div class='card'>Нажмите «ТЕСТИРОВАТЬ», чтобы получить полный отчёт.</div></div>";return}
const c={PASS:0,WARNING:0,FAIL:0,"NOT TESTED":0};(r.categories||[]).forEach(x=>c[x.status]++);
screen.innerHTML="<div class='screen'><div class='section-title'>Полный отчёт</div><div class='section-sub'>Результаты проверки всех 41 категории</div><div class='summary'><div class='card'><span class='sum-ico ok'>✓</span><div><b>"+c.PASS+"</b><div class='mini'>PASS</div></div></div><div class='card'><span class='sum-ico warn'>!</span><div><b>"+c.WARNING+"</b><div class='mini'>WARNING</div></div></div><div class='card'><span class='sum-ico fail'>×</span><div><b>"+c.FAIL+"</b><div class='mini'>FAIL</div></div></div><div class='card'><span class='sum-ico not'>○</span><div><b>"+c["NOT TESTED"]+"</b><div class='mini'>NOT TESTED</div></div></div></div><div class='card' style='margin-top:10px'><div class='row'><span>Всего категорий</span><b>41</b></div><div class='row'><span>Режим</span><b class='ok'>READ-ONLY</b></div><div class='row'><span>GitHub</span><b class='ok'>Проверен</b></div><div class='row'><span>Render</span><b class='ok'>Проверен</b></div></div><div class='list'>"+(r.categories||[]).map(x=>"<div class='card category-row' onclick='categoryDetail("+Number(x.category)+")'><div class='row'><span>"+esc(x.category)+". "+esc(x.name)+"</span>"+badge(x.status)+"</div><div class='mini'>"+esc(x.detail||"")+"</div></div>").join("")+"</div></div>"
}
function categoryDetail(n){
const x=(data?.report?.categories||[]).find(v=>Number(v.category)===n);if(!x)return;
screen.innerHTML="<div class='screen'><div class='section-title'>Категория "+esc(x.category)+": "+esc(x.name)+"</div><div class='card'><div class='row'><b>Статус</b>"+badge(x.status)+"</div><p>"+esc(x.detail||"")+"</p><div class='mini'>Что проверено:</div>"+(x.evidence||[]).map(v=>"<div class='row'><span>"+esc(v.path||"Источник")+"</span><span class='ok'>✓</span></div>").join("")+"</div><button class='button secondary' style='margin-top:10px' onclick='render("results")'>← Вернуться к отчёту</button></div>"
}
function errors(){
const r=data?.report;if(!r){screen.innerHTML="<div class='screen'><div class='section-title'>Ошибки</div><div class='card'>После проверки здесь появится список проблем.</div></div>";return}
const e=(r.categories||[]).filter(x=>x.status==="FAIL"||x.status==="WARNING");
screen.innerHTML="<div class='screen'><div class='section-title'>Список ошибок</div><div class='section-sub'>Найдено проблем: "+e.length+"</div>"+(e.length?e.map((x,i)=>"<div class='card error'><div class='row'><b>"+(i+1)+". "+esc(x.name)+"</b>"+badge(x.status)+"</div><p>"+esc(x.detail||"")+"</p>"+(x.evidence||[]).map(v=>"<div class='mini'>"+esc(v.path||"")+"</div>").join("")+"</div>").join(""):"<div class='card'><span class='ok'>Ошибок не обнаружено.</span></div>")+"</div>"
}
function infra(){
const r=data?.report;if(!r){screen.innerHTML="<div class='screen'><div class='section-title'>GitHub и Render</div><div class='card'>Данные появятся после проверки.</div></div>";return}
const rd=r.render||{},d=rd.last_deploy||{};
screen.innerHTML="<div class='screen'><div class='section-title'>GitHub и Render</div><div class='card'><h3>GitHub</h3><div class='row'><span>Репозиторий</span>"+badge(r.repository?.status||"NOT TESTED")+"</div><div class='mini'>"+esc(r.target_repo||"—")+"</div><div class='row'><span>Файлов</span><b>"+esc(r.repository?.file_count||0)+"</b></div></div><div class='card'><h3>Render</h3><div class='row'><span>Сервис</span>"+badge(rd.status||"NOT TESTED")+"</div><div class='mini'>"+esc(rd.detail||"—")+"</div><div class='row'><span>Последний запуск</span><b>"+esc(d.status||"NOT TESTED")+"</b></div></div><div class='card'><h3>HTTP</h3><div class='row'><span>/health</span>"+badge(r.http?.status||"NOT TESTED")+"</div><div class='mini'>"+esc(r.http?.detail||"—")+"</div></div></div>"
}
async function historyScreen(){const r=await get("/api/test/history");screen.innerHTML="<div class='screen'><div class='section-title'>История проверок</div><div class='section-sub'>Последние результаты</div>"+((r.history||[]).length?(r.history||[]).map(h=>"<div class='card'><div class='row'><b>"+esc(h.target?.name||"Тест")+"</b><span class='ok'>✓</span></div><div class='mini'>PASS: "+h.summary.PASS+" · WARN: "+h.summary.WARNING+" · FAIL: "+h.summary.FAIL+"</div></div>").join(""):"<div class='card'>История пока пустая.</div>")+"</div>"}
document.querySelectorAll(".nav button").forEach(b=>b.onclick=()=>render(b.dataset.screen));
loadSession().then(()=>render("home"));
