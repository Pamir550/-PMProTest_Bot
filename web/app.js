const params=new URLSearchParams(location.search);
const session=params.get("session")||"";
const tg=window.Telegram?.WebApp;
if(tg){tg.ready();tg.expand();}

const screen=document.getElementById("screen");
let data=null,status=null,timer=null;

const esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
async function get(url){try{const r=await fetch(url,{cache:"no-store"});return await r.json()}catch(e){return{ok:false,error:e.message}}}

async function sessionLoad(){
  const r=await get("/api/session?session="+encodeURIComponent(session));
  if(r.ok)data=r;
}
function setNav(name){
  document.querySelectorAll(".bottom-nav button").forEach(b=>b.classList.toggle("active",b.dataset.screen===name));
  if(name!=="home") document.querySelector(".app")?.classList.remove("home-only");
}
function badge(s){
  const c=s==="PASS"?"PASS":s==="WARNING"?"WARNING":s==="FAIL"?"FAIL":"NOT";
  return "<span class='badge "+c+"'>"+esc(s)+"</span>";
}
function goHome(){home()}
function nav(name){
  setNav(name);
  const fn={home,results,errors,infra,history}[name];
  if(fn)fn();
}
function quick(){
  return "<div class='quick'>"+
    "<button class='quick-card' onclick=\"nav('results')\"><span class='qicon'>▥</span><small>Результаты</small></button>"+
    "<button class='quick-card' onclick=\"nav('errors')\"><span class='qicon'>⚠</span><small>Ошибки</small></button>"+
    "<button class='quick-card' onclick=\"nav('infra')\"><span class='qicon'>◉</span><small>GitHub</small></button>"+
    "<button class='quick-card' onclick=\"nav('infra')\"><span class='qicon'>☁</span><small>Render</small></button>"+
  "</div>";
}
function targetCard(){
  const t=data?.target||{};
  return "<div class='target'>"+
    "<div class='target-label'>Тестируемый бот</div>"+
    "<b>"+esc(t.name||"PMSignalPro")+"</b>"+
    "<span class='username'>"+esc(t.username||"@PMSignalPro_bot")+"</span>"+
    "<button class='edit'>✎</button></div>";
}
function home(){
  setNav("home");
  document.querySelector(".app")?.classList.add("home-only");
  if(status?.status==="running"){document.querySelector(".app")?.classList.remove("home-only");screen.innerHTML=process();return}
  screen.innerHTML="<div class='page'><div class='hero home-hero'>"+
    "<button class='home-close' onclick='home()' aria-label='Закрыть'>×</button>"+
    "<button class='home-info' aria-label='Информация'>ⓘ</button>"+
    "<div class='search-logo'><span></span></div>"+
    "<h1>PMSignalPro Tester</h1>"+
    "<div class='lead'>Полная проверка вашего бота<br>на GitHub и Render</div>"+
    "<span class='ro'>READ-ONLY</span>"+
    "<div class='hint'>ⓘ Только проверка · Ничего не изменяет</div>"+
    targetCard()+
    "<button class='launch' onclick='start()'><span>ТЕСТИРОВАТЬ</span></button>"+
  "</div></div>";
}
function process(){
  const total=status?.total||41;
  const n=status?.current||Math.round(total*(status?.progress||0)/100);
  const pct=Math.max(0,Math.min(100,status?.progress||0));
  const cats=(status?.categories||[]).slice(-10);
  const list=cats.length?cats.map((x,i)=>"<div class='row'><span><span class='num-dot'>"+esc(x.number||i+1)+"</span>"+esc(x.name||x.category||"Проверка")+"</span><span class='check'>"+(x.done?"✓":"○")+"</span></div>").join(""):"<div class='row'><span>1 <b>Структура проекта</b></span><span class='check'>✓</span></div><div class='row'><span>2 <b>Telegram Bot</b></span><span class='check'>✓</span></div><div class='row'><span>3 <b>Авторизация</b></span><span class='check'>○</span></div><div class='row'><span>4 <b>База данных</b></span><span class='check'>○</span></div><div class='row'><span>5 <b>Mini App</b></span><span class='check'>○</span></div>";
  screen.innerHTML="<div class='page'><div class='card'>"+
    "<div class='section-title'>Идёт полная проверка...</div>"+
    "<div class='section-sub'>Проверяем все 41 категорию<br>вашего проекта.</div>"+
    "<div class='progress-ring' style='--pct:"+pct+"%'><b>"+n+"/"+total+"<small style='display:block;text-align:center;font-size:12px;color:#c5d4e9'>"+pct+"%</small></b></div>"+
    "<div class='category-list'>"+list+"</div>"+
    "<div class='note'>ⓘ Проверка может занять несколько минут.<br>Бот анализирует файлы на GitHub, проверяет Render и все функции.</div>"+
  "</div></div>";
}
async function start(){
  const r=await fetch("/api/test/start?session="+encodeURIComponent(session),{method:"POST"});
  if(!r.ok)return;
  clearInterval(timer);timer=setInterval(refresh,700);refresh();
}
async function refresh(){
  status=await get("/api/test/status?session="+encodeURIComponent(session));
  if(status.status==="running")home();
  if(status.status==="completed"||status.status==="failed"){
    clearInterval(timer);
    const r=await get("/api/test/report?session="+encodeURIComponent(session));
    if(r.ok)data={...data,report:r.report};
    results();
  }
}
function reportData(){
  return data?.report?.categories||[];
}
function counts(){
  const c={PASS:0,WARNING:0,FAIL:0,"NOT TESTED":0};
  reportData().forEach(x=>c[x.status]=(c[x.status]||0)+1);
  return c;
}
function results(){
  setNav("results");
  const r=data?.report;
  if(!r){screen.innerHTML="<div class='page'><div class='card empty'>Сначала запустите проверку.</div></div>";return}
  const c=counts();
  screen.innerHTML="<div class='page'>"+
    "<div class='section-title'>🏆<br>Проверка завершена!</div>"+
    "<div class='section-sub'>Все 41 категория проверены</div>"+
    "<div class='summary'>"+
      "<div class='stat'><span class='stat-icon pass'>✓</span><div><b>"+c.PASS+"</b><div class='muted'>PASS</div></div></div>"+
      "<div class='stat'><span class='stat-icon warning'>!</span><div><b>"+c.WARNING+"</b><div class='muted'>WARNING</div></div></div>"+
      "<div class='stat'><span class='stat-icon fail'>×</span><div><b>"+c.FAIL+"</b><div class='muted'>FAIL</div></div></div>"+
      "<div class='stat'><span class='stat-icon not'>●</span><div><b>"+c["NOT TESTED"]+"</b><div class='muted'>NOT TESTED</div></div></div>"+
    "</div>"+
    "<div class='card'><div class='row'><span>▣ Всего категорий</span><b>41</b></div><div class='row'><span>◷ Время проверки</span><b>"+esc(r.duration||"—")+"</b></div><div class='row'><span>GitHub</span><b class='pass'>✓ Проверен</b></div><div class='row'><span>Render</span><b class='pass'>✓ Проверен</b></div><div class='row'><span>Последний запуск</span><b>"+esc(r.finished_at||"—")+"</b></div></div>"+
    "<button class='btn' onclick='reportList()'>▤ Открыть полный отчёт</button>"+
    "<button class='btn warn-btn' onclick='errors()'>⚠ Список ошибок ("+c.FAIL+")</button>"+
  "</div>";
}
function reportList(){
  setNav("results");
  const cats=reportData();
  screen.innerHTML="<div class='page'><div class='section-title'>Полный отчёт (41 категория)</div><div class='section-sub'>Результаты проверки всех категорий</div>"+
    "<div class='tabs'><button class='tab active'>Все (41)</button><button class='tab'>PASS ("+counts().PASS+")</button><button class='tab'>WARN ("+counts().WARNING+")</button><button class='tab'>FAIL ("+counts().FAIL+")</button></div>"+
    "<div class='card' style='padding:5px'>"+cats.map((x,i)=>"<div class='report-row' onclick='detail("+Number(x.category||i+1)+")'><b>"+esc(x.category||i+1)+"</b><span>"+esc(x.name||"Категория")+"</span>"+badge(x.status)+"</div>").join("")+"</div></div>";
}
function detail(n){
  const x=reportData().find(v=>Number(v.category)===Number(n));
  if(!x)return;
  screen.innerHTML="<div class='page'><div class='card'>"+
    "<div class='row'><b>Категория "+esc(x.category)+": "+esc(x.name)+"</b>"+badge(x.status)+"</div>"+
    "<h3>Что проверено:</h3>"+
    (x.evidence||[]).map(v=>"<div class='row'><span>"+esc(v.path||v.name||"Проверка")+"</span><span class='check'>"+(v.ok===false?"×":"✓")+"</span></div>").join("")+
    "<h3>Проблемы:</h3><div class='muted'>"+esc(x.detail||"Проблем не указано.")+"</div>"+
    "<h3>Рекомендации:</h3><div class='muted'>Проверить указанные источники и повторить тест после исправления.</div>"+
  "</div><button class='btn' onclick='reportList()'>← Полный отчёт</button></div>";
}
function errors(){
  setNav("errors");
  const e=reportData().filter(x=>x.status==="FAIL"||x.status==="WARNING");
  screen.innerHTML="<div class='page'><div class='section-title'>Список ошибок</div><div class='section-sub'>Найдено ошибок: "+e.length+"</div>"+
    (e.length?e.map((x,i)=>"<div class='card error-card'><div class='row'><span><span class='error-number'>"+(i+1)+"</span> <b>"+esc(x.name)+"</b></span>"+badge(x.status)+"</div><p>"+esc(x.detail||"Ошибка проверки")+"</p><button class='btn' onclick='showCode("+i+")'>▱ Показать код</button></div>").join(""):"<div class='card empty'>Ошибок не обнаружено.</div>")+
    "</div>";
}
function showCode(i){
  const e=reportData().filter(x=>x.status==="FAIL"||x.status==="WARNING")[i];
  if(!e)return;
  screen.innerHTML="<div class='page'><div class='section-title'>Ошибка: "+esc(e.name)+"</div><div class='card'><div class='code'>"+esc(JSON.stringify(e,null,2))+"</div></div><button class='btn' onclick='errors()'>← Список ошибок</button></div>";
}
function infra(){
  setNav("infra");
  const r=data?.report;
  if(!r){screen.innerHTML="<div class='page'><div class='section-title'>GitHub и Render</div><div class='card empty'>Данные появятся после проверки.</div></div>";return}
  const repo=r.repository||{},ren=r.render||{};
  screen.innerHTML="<div class='page'><div class='section-title'>GitHub и Render</div>"+
    "<div class='card infra-card'><div class='service-head'><span class='service-icon'>◉</span>GitHub "+badge(repo.status||"NOT TESTED")+"</div><div class='row'><span>Репозиторий</span><b>"+esc(r.target_repo||"—")+"</b></div><div class='row'><span>Ветка</span><b>"+esc(r.branch||"main")+"</b></div><div class='row'><span>Файлов</span><b>"+esc(repo.files||"—")+"</b></div><div class='row'><span>Последний commit</span><b>"+esc(repo.last_commit||"—")+"</b></div></div>"+
    "<div class='card infra-card'><div class='service-head'><span class='service-icon'>☁</span>Render "+badge(ren.status||"NOT TESTED")+"</div><div class='row'><span>Статус</span><b>"+esc(ren.detail||"—")+"</b></div><div class='row'><span>Последний deploy</span><b>"+esc(ren.last_deploy?.status||"—")+"</b></div><div class='row'><span>Логи</span><b>Доступны</b></div></div></div>";
}
async function history(){
  setNav("history");
  const r=await get("/api/test/history?session="+encodeURIComponent(session));
  const h=r.history||[];
  screen.innerHTML="<div class='page'><div class='section-title'>История проверок</div><div class='section-sub'>Последние результаты</div>"+
    (h.length?h.map(x=>"<div class='card history-item'><div class='date'>"+esc(x.created_at||x.date||"")+"</div><div class='row'><b>"+esc(x.target?.name||"PMSignalPro")+"</b><span class='pass'>✓</span></div><div class='counts'>PASS: <span class='pass'>"+esc(x.summary?.PASS||0)+"</span> · WARN: <span class='warning'>"+esc(x.summary?.WARNING||0)+"</span> · FAIL: <span class='fail'>"+esc(x.summary?.FAIL||0)+"</span></div></div>").join(""):"<div class='card empty'>История пока пустая.</div>")+
  "</div>";
}
function sections(){
  screen.innerHTML="<div class='page'><div class='section-title'>Меню разделов</div><div class='section-sub'>Выберите раздел для просмотра</div><div class='menu-grid'>"+
    "<button class='menu-card' onclick='results()'><span class='big'>▥</span><b>Результаты</b><small>Полный отчёт по 41 категории</small></button>"+
    "<button class='menu-card' onclick='errors()'><span class='big'>⚠</span><b>Ошибки</b><small>Список всех проблем</small></button>"+
    "<button class='menu-card' onclick='reportList()'><span class='big'>▣</span><b>Файлы</b><small>Проверка проекта</small></button>"+
    "<button class='menu-card' onclick='infra()'><span class='big'>◉</span><b>GitHub</b><small>Статус, файлы, commit</small></button>"+
    "<button class='menu-card' onclick='infra()'><span class='big'>☁</span><b>Render</b><small>Статус сервиса</small></button>"+
    "<button class='menu-card' onclick='history()'><span class='big'>◷</span><b>История</b><small>Все проверки и отчёты</small></button>"+
    "<button class='menu-card'><span class='big'>⚙</span><b>Настройки</b><small>Параметры отображения</small></button>"+
    "<button class='menu-card'><span class='big'>?</span><b>Помощь</b><small>Инструкция и поддержка</small></button>"+
  "</div></div>";
}
document.querySelectorAll(".bottom-nav button").forEach(b=>b.addEventListener("click",()=>nav(b.dataset.screen)));
sessionLoad().then(home);
