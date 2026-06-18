// ══════════════════════════════════════════
//  ДАННЫЕ ДЕЛ
// ══════════════════════════════════════════
const CASES = [
    {
        id: 1,
        title: "Исчезновение сценария",
        preview: "Сценарий нового фильма Боджека загадочно исчез прямо перед подписанием контракта.",
        description: "Сценарий нового фильма пропал прямо перед подписанием контракта. Кэролин в панике, продюсеры угрожают разорвать сделку. Поговори с каждым персонажем и выясни, кто взял сценарий и почему.",
        difficulty: "Лёгкое",
        hint: "Один из персонажей взял сценарий случайно, перепутав его с чем-то другим. Обрати внимание на кухню.",
        solution: ["тодд", "todd"],
        solutionFull: "Тодд взял сценарий случайно — он думал, что это меню пиццерии. Он использовал несколько страниц как подставку под горячую кружку кофе на кухне. Кэролин нашла документ в самый последний момент.",
        systemPrompt: `Ты персонаж из мультсериала «Конь БоДжек». Идёт детективное расследование.

ФАКТЫ ДЕЛА (знаешь ты и все персонажи, но никто не раскрывает правду напрямую):
- Сценарий нового фильма Боджека исчез вчера вечером со стола в гостиной.
- Тодд взял его случайно, думая что это меню для заказа пиццы.
- Тодд использовал несколько страниц как подставку под горячую кружку на кухне.
- Кэролин не знает где сценарий и очень нервничает.
- Боджек видел как Тодд ходил по гостиной вечером с какими-то бумагами.
- Диана заходила в офис Кэролин утром и заметила что та явно чем-то расстроена.

ТВОЯ ЗАДАЧА: отвечай в образе своего персонажа, давай косвенные подсказки, но НЕ называй прямо кто виноват. Говори по-русски.`,
        startLocation: "living_room"
    },
    {
        id: 2,
        title: "Тайна пропавшей бутылки",
        preview: "Любимое виски Боджека исчезло. Кто и зачем его спрятал?",
        description: "Боджек не может найти свою любимую бутылку виски — старого 12-летнего Macallan. Он подозревает всех. Поговори с персонажами и выясни, кто спрятал бутылку и зачем.",
        difficulty: "Лёгкое",
        hint: "Тот, кто спрятал, сделал это из заботы о Боджеке. Вещь всё ещё где-то в доме.",
        solution: ["диана", "diane"],
        solutionFull: "Диана спрятала бутылку, потому что беспокоилась о здоровье Боджека. Она видела как он пьёт в одиночестве три ночи подряд и решила вмешаться. Бутылка спрятана в её сумке в холле.",
        systemPrompt: `Ты персонаж из мультсериала «Конь БоДжек». Идёт детективное расследование.

ФАКТЫ ДЕЛА (знаешь ты и все персонажи, но никто не раскрывает правду напрямую):
- Бутылка виски Macallan 12 лет исчезла из гостиной Боджека.
- Диана спрятала её в своей сумке, которая сейчас стоит в холле.
- Диана видела как Боджек пил в одиночестве три ночи подряд и решила вмешаться.
- Тодд видел как Диана что-то убирала в сумку вчера вечером, но не знает что именно.
- Боджек злится и всех подозревает, особенно Тодда.
- Кэролин не знает ничего о бутылке.

ТВОЯ ЗАДАЧА: отвечай в образе своего персонажа, давай косвенные подсказки, но НЕ называй прямо кто виноват. Говори по-русски.`,
        startLocation: "living_room"
    },
    {
        id: 3,
        title: "Анонимное письмо",
        preview: "Боджек получил письмо с требованием публично извиниться. Кто его написал?",
        description: "Боджек получил конверт без обратного адреса с требованием публично извиниться за прошлое. Кто решил напомнить ему о старых грехах и что за этим стоит?",
        difficulty: "Среднее",
        hint: "Автор письма — не враг Боджека. Он хотел защитить кого-то близкого и действовал анонимно из дружеских побуждений.",
        solution: ["мистер подхвост", "подхвост", "mr peanutbutter", "dog", "пёс"],
        solutionFull: "Письмо написал Мистер Подхвост. Он хотел чтобы Боджек извинился перед Дианой за слова, которые причинили ей боль несколько лет назад. Он действовал анонимно, потому что не хотел испортить отношения с Боджеком напрямую.",
        systemPrompt: `Ты персонаж из мультсериала «Конь БоДжек». Идёт детективное расследование.

ФАКТЫ ДЕЛА (знаешь ты и все персонажи, но никто не раскрывает правду напрямую):
- Боджек получил анонимное письмо с требованием публично извиниться перед Дианой.
- Письмо написал Мистер Подхвост — он очень переживает за Диану.
- Мистер Подхвост купил конверт в магазине рядом с холлом.
- Тодд видел Мистера Подхвоста у почтового ящика утром.
- Диана не знает об этом письме.
- Кэролин считает что это чья-то шутка.
- Боджек растерян и не понимает кто это мог написать.

ТВОЯ ЗАДАЧА: отвечай в образе своего персонажа, давай косвенные подсказки, но НЕ называй прямо кто виноват. Говори по-русски.`,
        startLocation: "living_room"
    },
    {
        id: 4,
        title: "Сорванная съёмка",
        preview: "Кто-то залил кофе в камеру на съёмочной площадке. Случайность или умысел?",
        description: "Съёмки нового шоу Кэролин были сорваны — кто-то залил кофе в основную камеру. Страховка не покрывает умышленную порчу. Кэролин теряет деньги. Выясни, кто это сделал.",
        difficulty: "Сложное",
        hint: "Виновник хотел не навредить, а спасти проект от провала. Посмотри кто больше всего знал о качестве материала.",
        solution: ["кэролин", "caroline", "принцесса кэролин"],
        solutionFull: "Кэролин сама залила камеру кофе. Она посмотрела черновой монтаж и поняла, что шоу ужасно и провалится. Намеренно испортив оборудование, она получила время переработать сценарий и спасти проект от катастрофы. Это был рискованный, но единственный выход который она видела.",
        systemPrompt: `Ты персонаж из мультсериала «Конь БоДжек». Идёт детективное расследование.

ФАКТЫ ДЕЛА (знаешь ты и все персонажи, но никто не раскрывает правду напрямую):
- На съёмочной площадке шоу Кэролин кто-то залил кофе в основную камеру.
- Это сделала сама Кэролин — она посмотрела черновой монтаж и поняла что шоу провалится.
- Она решила «случайно» испортить оборудование чтобы выиграть время на переработку сценария.
- Тодд был рядом и видел Кэролин с кружкой кофе рядом с камерой, но не придал значения.
- Боджек слышал как Кэролин говорила по телефону о каком-то «запасном плане».
- Диана подозревает что произошедшее не случайно.

ТВОЯ ЗАДАЧА: отвечай в образе своего персонажа, давай косвенные подсказки, но НЕ называй прямо кто виноват. Говори по-русски.`,
        startLocation: "office"
    }
];

// ══════════════════════════════════════════
//  ДАННЫЕ ЛОКАЦИЙ
// ══════════════════════════════════════════
const LOCATIONS = [
    {
        id: "living_room",
        name: "Гостиная",
        icon: "🛋️",
        bg: "/static/locations/background_bojack.jpg",
        npc: { id: "bojack", name: "Боджек", role: "Бывшая звезда телешоу", avatar: "/static/profiles/bojack_profile.png" }
    },
    {
        id: "office",
        name: "Офис",
        icon: "💼",
        bg: "/static/locations/background_caroline.png",
        npc: { id: "caroline", name: "Кэролин", role: "Продюсер", avatar: "/static/profiles/caroline_profile.png" }
    },
    {
        id: "kitchen",
        name: "Кухня",
        icon: "🍕",
        bg: "/static/locations/background_todd.png",
        npc: { id: "todd", name: "Тодд", role: "Друг Боджека", avatar: "/static/profiles/todd_profile.png" }
    },
    {
        id: "lobby",
        name: "Балкон",
        icon: "🚪",
        bg: "/static/locations/background_diane.png",
        npc: { id: "diane", name: "Диана", role: "Писатель и активист", avatar: "/static/profiles/diane_profile.png" }
    },
    {
        id: "bar",
        name: "Логово Подхвоста",
        icon: "🍺",
        bg: "/static/locations/background_dog.png",
        npc: { id: "dog", name: "Мистер Подхвост", role: "Верный друг", avatar: "/static/profiles/dog_profile.png" }
    }
];

// ══════════════════════════════════════════
//  СОСТОЯНИЕ
// ══════════════════════════════════════════
let state = {
    sessionId: null,
    currentLocationId: "living_room",
    selectedCase: null,
    loading: false,
    // Хранилище истории чата по локациям: { living_room: [...msgs], office: [...] }
    chatHistories: {}
};

// ══════════════════════════════════════════
//  ИНИЦИАЛИЗАЦИЯ
// ══════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
    renderCases();
    LOCATIONS.forEach(loc => { state.chatHistories[loc.id] = []; });
});

function renderCases() {
    document.getElementById("casesGrid").innerHTML = CASES.map(c => `
        <div class="case-card" onclick="selectCase(${c.id})">
            <div class="cn">Дело № ${c.id}</div>
            <div class="ct">${c.title}</div>
            <div class="cp">${c.preview}</div>
            <span class="cd">${c.difficulty}</span>
        </div>
    `).join("");
}

function selectCase(id) {
    const c = CASES.find(x => x.id === id);
    if (!c) return;
    state.selectedCase = c;
    // Сбросить историю чатов
    LOCATIONS.forEach(loc => { state.chatHistories[loc.id] = []; });

    document.getElementById("descNum").textContent = `Дело № ${c.id}`;
    document.getElementById("descTitle").textContent = c.title;
    document.getElementById("descText").textContent = c.description;
    showScreen("screenCaseDesc");
}

async function startGame() {
    showScreen("screenGame");
    const c = state.selectedCase;

    document.getElementById("topCaseTitle").textContent = `Дело № ${c.id}: ${c.title}`;

    // Сбросить локальные истории
    LOCATIONS.forEach(loc => { state.chatHistories[loc.id] = []; });

    // Начать или продолжить сессию для этого дела
    try {
        const res = await fetch("/api/game/session/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ case_id: c.id })
        });
        const data = await res.json();
        if (data.session_id) state.sessionId = data.session_id;

        // Если сессия была возобновлена — восстановить историю чатов из БД
        if (data.resumed && data.chat_histories) {
            _loadHistoriesFromServer(data.chat_histories);
        }
    } catch (e) { console.error("Session start error:", e); }

    // Добавить системное приветствие туда, где ещё нет истории
    LOCATIONS.forEach(loc => {
        if (state.chatHistories[loc.id].length === 0) {
            state.chatHistories[loc.id].push({
                type: "system",
                text: `Ты входишь в «${loc.name}». Здесь находится ${loc.npc.name}. Задавай вопросы, чтобы собрать улики.`
            });
        }
    });

    // Рендер вкладок и переход на стартовую локацию
    renderLocTabs();
    switchLocation(c.startLocation);
}

function _loadHistoriesFromServer(serverHistories) {
    // serverHistories = { "bojack": [{role, content}, ...], ... }
    // Конвертируем в отображаемые сообщения и кладём в state.chatHistories по локации
    const npcToLoc = {};
    LOCATIONS.forEach(loc => { npcToLoc[loc.npc.id] = loc; });

    Object.entries(serverHistories).forEach(([npcId, messages]) => {
        const loc = npcToLoc[npcId];
        if (!loc) return;
        const display = [{
            type: "system",
            text: `Ты входишь в «${loc.name}». Здесь находится ${loc.npc.name}. Задавай вопросы, чтобы собрать улики.`
        }];
        messages.forEach(msg => {
            if (msg.role === "user") {
                display.push({ type: "player", text: msg.content });
            } else if (msg.role === "assistant") {
                display.push({ type: "npc", text: msg.content, name: loc.npc.name });
            }
        });
        state.chatHistories[loc.id] = display;
    });
}

// ══════════════════════════════════════════
//  ЭКРАНЫ
// ══════════════════════════════════════════
function showScreen(id) {
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    document.getElementById(id).classList.add("active");
}

// ══════════════════════════════════════════
//  ЛОКАЦИИ
// ══════════════════════════════════════════
function renderLocTabs() {
    document.getElementById("locTabs").innerHTML = LOCATIONS.map(loc => `
        <button class="loc-tab ${loc.id === state.currentLocationId ? 'active' : ''}"
                id="tab-${loc.id}" onclick="switchLocation('${loc.id}')">
            <span class="tab-icon">${loc.icon}</span>
            <span class="tab-name">${loc.name}</span>
        </button>
    `).join("");
}

function switchLocation(locId) {
    // Сохранить текущую историю (уже в state.chatHistories)
    state.currentLocationId = locId;

    const loc = LOCATIONS.find(l => l.id === locId);
    if (!loc) return;

    // Обновить вкладки
    document.querySelectorAll(".loc-tab").forEach(t => t.classList.remove("active"));
    const tab = document.getElementById(`tab-${locId}`);
    if (tab) tab.classList.add("active");

    // Обновить фон и аватар
    document.getElementById("locBg").style.backgroundImage = `url('${loc.bg}')`;
    document.getElementById("charAvatar").src = loc.npc.avatar;
    document.getElementById("charAvatar").alt = loc.npc.name;
    document.getElementById("locNameBadge").textContent = loc.name;

    // Обновить шапку чата
    document.getElementById("npcAvatarSmall").src = loc.npc.avatar;
    document.getElementById("npcName").textContent = loc.npc.name;
    document.getElementById("npcRole").textContent = loc.npc.role;

    // Обновить placeholder инпута
    document.getElementById("msgInput").placeholder = `Спроси у ${loc.npc.name}...`;

    // Отрендерить историю чата этой локации
    renderChat();

    document.getElementById("msgInput").focus();
}

// ══════════════════════════════════════════
//  ЧАТ
// ══════════════════════════════════════════
function renderChat() {
    const log = document.getElementById("chatLog");
    const history = state.chatHistories[state.currentLocationId] || [];
    log.innerHTML = history.map(msg => renderMsg(msg)).join("");
    log.scrollTop = log.scrollHeight;
}

function renderMsg(msg) {
    if (msg.type === "system") {
        return `<div class="msg msg-system">${esc(msg.text)}</div>`;
    }
    if (msg.type === "player") {
        return `<div class="msg msg-player"><span class="bub">${esc(msg.text)}</span></div>`;
    }
    if (msg.type === "npc") {
        return `<div class="msg msg-npc">
            <div class="bub-name">${esc(msg.name)}</div>
            <span class="bub">${esc(msg.text)}</span>
        </div>`;
    }
    return "";
}

function addMsg(type, text, name = "") {
    const log = document.getElementById("chatLog");
    state.chatHistories[state.currentLocationId].push({ type, text, name });
    const div = document.createElement("div");
    div.innerHTML = renderMsg({ type, text, name });
    log.appendChild(div.firstChild);
    log.scrollTop = log.scrollHeight;
}

async function sendMessage(event) {
    if (event) event.preventDefault();
    const input = document.getElementById("msgInput");
    const text = input.value.trim();
    if (!text || state.loading) return;

    input.value = "";
    addMsg("player", text);
    setLoading(true);

    const loc = LOCATIONS.find(l => l.id === state.currentLocationId);
    const npc = loc.npc;

    try {
        const res = await fetch("/api/game/action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: state.sessionId,
                action: text,
                npc: npc.id,
                location: state.currentLocationId,
                case_context: state.selectedCase?.systemPrompt || ""
            })
        });
        const data = await res.json();

        if (data.success) {
            addMsg("npc", data.message, npc.name);
        } else {
            addMsg("system", data.message || data.detail || "Ошибка");
        }
    } catch (e) {
        addMsg("system", "Ошибка соединения с сервером.");
        console.error(e);
    } finally {
        setLoading(false);
        document.getElementById("msgInput").focus();
    }
}

// ══════════════════════════════════════════
//  МЕНЮ / РЕСТАРТ
// ══════════════════════════════════════════
function backToMenu() {
    showScreen("screenCases");
    state.sessionId = null;
    state.selectedCase = null;
    LOCATIONS.forEach(loc => { state.chatHistories[loc.id] = []; });
}

async function restartCase() {
    if (!confirm("Начать дело заново? Вся история разговоров будет удалена.")) return;

    // Очистить историю на сервере
    if (state.sessionId) {
        try {
            await fetch("/api/game/chat/reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: state.sessionId })
            });
        } catch (e) { console.error("Reset error:", e); }
    }

    // Сбросить локальное состояние и перезапустить
    LOCATIONS.forEach(loc => { state.chatHistories[loc.id] = []; });
    state.sessionId = null;
    await startGame();
}

// ══════════════════════════════════════════
//  ПОДСКАЗКА
// ══════════════════════════════════════════
function openCaseModal() {
    const c = state.selectedCase;
    if (!c) return;
    document.getElementById("caseModalNum").textContent = `Дело № ${c.id}`;
    document.getElementById("caseModalTitle").textContent = c.title;
    document.getElementById("caseModalText").textContent = c.description;
    document.getElementById("caseModal").classList.add("open");
}

function openHintModal() {
    document.getElementById("hintText").textContent = state.selectedCase?.hint || "Подсказка недоступна.";
    document.getElementById("hintModal").classList.add("open");
    if (state.sessionId) {
        fetch("/api/game/hint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: state.sessionId })
        }).catch(() => {});
    }
}

// ══════════════════════════════════════════
//  ОТВЕТ / ПРОВЕРКА
// ══════════════════════════════════════════
function openAnswerModal() {
    document.getElementById("answerForm").style.display = "";
    document.getElementById("revealBlock").style.display = "none";
    document.getElementById("wrongMsg").style.display = "none";
    document.getElementById("answerInput").value = "";
    document.getElementById("answerModal").classList.add("open");
    setTimeout(() => document.getElementById("answerInput").focus(), 100);
}

async function checkAnswer() {
    const input = document.getElementById("answerInput").value.trim().toLowerCase();
    if (!input) return;

    const solutions = state.selectedCase?.solution || [];
    const correct = solutions.some(s => input.includes(s) || s.includes(input));

    if (correct) {
        if (state.sessionId) {
            await fetch("/api/game/solve", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: state.sessionId })
            }).catch(() => {});
        }
        showReveal(true);
    } else {
        if (state.sessionId) {
            fetch("/api/game/attempt", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: state.sessionId })
            }).catch(() => {});
        }
        document.getElementById("wrongMsg").style.display = "block";
    }
}

function giveUp() {
    showReveal(false);
}

function showReveal(correct) {
    document.getElementById("answerForm").style.display = "none";
    const reveal = document.getElementById("revealBlock");
    reveal.style.display = "block";

    document.getElementById("revealIcon").textContent = correct ? "✅" : "😔";
    document.getElementById("revealTitle").textContent = correct
        ? "Верно! Дело раскрыто!"
        : "Вот что произошло на самом деле...";
    document.getElementById("revealText").textContent = state.selectedCase?.solutionFull || "";
}

// ══════════════════════════════════════════
//  ВСПОМОГАТЕЛЬНЫЕ
// ══════════════════════════════════════════
function closeModal(id) {
    document.getElementById(id).classList.remove("open");
}

function setLoading(val) {
    state.loading = val;
    const btn = document.getElementById("sendBtn");
    const inp = document.getElementById("msgInput");
    if (btn) btn.disabled = val;
    if (inp) inp.disabled = val;
}

function esc(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
}

// Enter в модалке ответа
document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal-overlay.open").forEach(m => m.classList.remove("open"));
    }
});
