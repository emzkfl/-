const form = document.querySelector("#search-form");
const nameInput = document.querySelector("#character-name");
const dateInput = document.querySelector("#date");
const searchButton = document.querySelector("#search-button");
const statusEl = document.querySelector("#status");
const dashboard = document.querySelector("#dashboard");
const emptyState = document.querySelector("#empty-state");
const characterImage = document.querySelector("#character-image");
const characterTitle = document.querySelector("#character-title");
const worldBadge = document.querySelector("#world-badge");
const profileMeta = document.querySelector("#profile-meta");
const profileIcons = document.querySelector("#profile-icons");
const combatPower = document.querySelector("#combat-power");
const convertedPower = document.querySelector("#converted-power");
const hexaPower = document.querySelector("#hexa-power");
const hexaDetail = document.querySelector("#hexa-detail");
const selectedPresetSummary = document.querySelector("#selected-preset-summary");
const selectedPresetValue = document.querySelector("#selected-preset-value");
const selectedPresetDelta = document.querySelector("#selected-preset-delta");
const equipmentPresetButtons = document.querySelector("#equipment-preset-buttons");
const abilityPresetButtons = document.querySelector("#ability-preset-buttons");
const hyperPresetButtons = document.querySelector("#hyper-preset-buttons");
const bossBasis = document.querySelector("#boss-basis");
const bossList = document.querySelector("#boss-list");
const tabButtons = [...document.querySelectorAll(".view-tab")];
const tabPanels = [...document.querySelectorAll(".tab-panel")];
const equipmentIcons = document.querySelector("#equipment-icons");
const symbolIcons = document.querySelector("#symbol-icons");
const abilityList = document.querySelector("#ability-list");
const hyperList = document.querySelector("#hyper-list");
const extraList = document.querySelector("#extra-list");
const coverageList = document.querySelector("#coverage-list");
const upgradeSummary = document.querySelector("#upgrade-summary");
const upgradeSlotList = document.querySelector("#upgrade-slot-list");
const upgradeCategoryList = document.querySelector("#upgrade-category-list");
const upgradeList = document.querySelector("#upgrade-list");
const equipmentSummary = document.querySelector("#equipment-summary");
const itemList = document.querySelector("#item-list");
const rawOutput = document.querySelector("#raw-output");
const radar = document.querySelector("#radar");

const LABELS = {
  stat: "스탯",
  attack: "공마",
  damage: "공격%",
  critical: "크뎀",
  ignore: "방무",
  final: "최종",
};

let activeTab = "overview";
let activeData = null;
let selectedPresets = { itemPreset: null, abilityPreset: null, hyperPreset: null };

function formatNumber(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(number);
}

function koreanPower(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) return "-";
  const eok = Math.floor(number / 100000000);
  const man = Math.floor((number % 100000000) / 10000);
  const rest = Math.floor(number % 10000);
  if (eok > 0) return `${eok}억 ${man}만 ${formatNumber(rest)}`;
  if (man > 0) return `${man}만 ${formatNumber(rest)}`;
  return formatNumber(number);
}

function setStatus(message, tone = "idle") {
  statusEl.textContent = message;
  statusEl.dataset.tone = tone;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function readJson(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { error: text };
  }
}

function defaultDate() {
  const date = new Date();
  date.setDate(date.getDate() - 1);
  return date.toISOString().slice(0, 10);
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    const body = await readJson(response);
    dateInput.value = body.defaultDate || defaultDate();
  } catch {
    dateInput.value = defaultDate();
  }
}

function metaRow(label, value) {
  if (value === undefined || value === null || value === "") return "";
  return `<span><b>${escapeHtml(label)}</b>${escapeHtml(value)}</span>`;
}

function renderProfile(data) {
  const basic = data.basic || {};
  const summary = data.summary || {};
  characterImage.src = basic.character_image || "";
  characterImage.hidden = !basic.character_image;
  characterTitle.textContent = basic.character_name || "-";
  worldBadge.textContent = basic.world_name || "-";

  profileMeta.innerHTML = [
    metaRow("직업", basic.character_class),
    metaRow("레벨", `Lv.${basic.character_level} (${basic.character_exp_rate || 0}%)`),
    metaRow("길드", basic.character_guild_name || "-"),
    metaRow("유니온", summary.unionLevel ? `${formatNumber(summary.unionLevel)} / ${summary.unionGrade || "-"}` : "-"),
    metaRow("환산 기준", summary.jobRuleApplied ? `${summary.mainStat} / ${summary.attackType}` : "스탯 자동 추정"),
    metaRow("주의", summary.jobNote),
  ].join("");

  renderProfileIcons(data.equipment || []);
}

function renderProfileIcons(items) {
  profileIcons.innerHTML = (items || [])
    .filter((item) => item.icon)
    .slice(0, 28)
    .map((item) => `<img src="${escapeHtml(item.icon)}" title="${escapeHtml(item.name)}" alt="" />`)
    .join("");
}

function renderScores(data) {
  const summary = data.summary || {};
  const primary = data.primaryMetric || {};
  const confidence = primary.confidence || {};
  combatPower.textContent = koreanPower(summary.combatPower);
  convertedPower.textContent = formatNumber(primary.value || summary.unifiedConverted380 || summary.hexaConverted380 || summary.converted380);
  hexaPower.textContent = formatNumber(summary.hexaConverted380);
  hexaDetail.textContent = `${primary.label || "대표 지표"} 기준 · 신뢰도 ${confidence.label || "-"} ${formatNumber(confidence.score || 0)}점 · HEXA Lv합 ${formatNumber(summary.hexaSkillTotalLevel || 0)} · 스탯기여 +${formatNumber(summary.hexaStatGain380 || 0)}`;
}

function presetByNo(rows, no) {
  return (rows || []).find((row) => Number(row.no) === Number(no));
}

function selectedCombination(data) {
  const combinations = data.presetViews?.combinations || [];
  return combinations.find(
    (row) =>
      Number(row.itemPreset) === Number(selectedPresets.itemPreset) &&
      Number(row.abilityPreset) === Number(selectedPresets.abilityPreset) &&
      Number(row.hyperPreset) === Number(selectedPresets.hyperPreset),
  );
}

function selectedUpgradePlan(data) {
  const plans = data.presetUpgradePlans || [];
  const matched = plans.find(
    (row) =>
      Number(row.itemPreset) === Number(selectedPresets.itemPreset) &&
      Number(row.abilityPreset) === Number(selectedPresets.abilityPreset) &&
      Number(row.hyperPreset) === Number(selectedPresets.hyperPreset),
  );
  return matched?.plan || data.itemUpgradePlan || {};
}

function selectedEquipment(data) {
  return presetByNo(data.presetViews?.equipment, selectedPresets.itemPreset)?.items || data.equipment || [];
}

function selectedAbility(data) {
  return presetByNo(data.presetViews?.ability, selectedPresets.abilityPreset)?.abilities || data.ability || [];
}

function selectedHyper(data) {
  return presetByNo(data.presetViews?.hyper, selectedPresets.hyperPreset)?.rows || [];
}

function presetButtonHtml(kind, row, selectedNo) {
  const presetNo = Number(row.no);
  const classes = ["preset-button"];
  if (presetNo === Number(selectedNo)) classes.push("active");
  if (row.active) classes.push("current");
  const count = row.count ? `${formatNumber(row.count)}개` : "정보 있음";
  return `<button class="${classes.join(" ")}" type="button" data-preset-kind="${kind}" data-preset-no="${presetNo}">
    <b>${presetNo}</b>
    <span>${row.active ? "현재" : count}</span>
  </button>`;
}

function renderPresetButtonGroup(target, kind, rows, selectedNo) {
  target.innerHTML = rows?.length
    ? rows.map((row) => presetButtonHtml(kind, row, selectedNo)).join("")
    : `<span class="muted">프리셋 정보 없음</span>`;
}

function renderPresetBrowser(data) {
  const views = data.presetViews || {};
  renderPresetButtonGroup(equipmentPresetButtons, "itemPreset", views.equipment || [], selectedPresets.itemPreset);
  renderPresetButtonGroup(abilityPresetButtons, "abilityPreset", views.ability || [], selectedPresets.abilityPreset);
  renderPresetButtonGroup(hyperPresetButtons, "hyperPreset", views.hyper || [], selectedPresets.hyperPreset);

  const combo = selectedCombination(data);
  const basis = data.presetOptimization?.basis || data.summary?.unifiedBasis || "대표 환산";
  selectedPresetSummary.textContent = `${basis} · 장비 ${selectedPresets.itemPreset || "-"} · 어빌 ${selectedPresets.abilityPreset || "-"} · 하이퍼 ${selectedPresets.hyperPreset || "-"}`;
  selectedPresetValue.textContent = formatNumber(combo?.converted);
  const delta = Number(combo?.delta || 0);
  selectedPresetDelta.textContent = combo
    ? delta > 0
      ? `현재보다 +${formatNumber(delta)}`
      : delta < 0
        ? `현재보다 ${formatNumber(delta)}`
        : "현재 적용 조합"
    : "계산 가능한 조합 없음";
}

function applyPresetSelection(data) {
  renderPresetBrowser(data);
  renderProfileIcons(selectedEquipment(data));
  renderEquipmentPanel(data);
  renderAbilityPanel(data);
  renderHyperPanel(data);
  renderUpgradePlan(data);
  renderItems(data);
}

function setActiveTab(tabName) {
  activeTab = tabName;
  tabButtons.forEach((button) => {
    const active = button.dataset.tab === tabName;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
  tabPanels.forEach((panel) => {
    panel.hidden = panel.dataset.panel !== tabName;
  });
}

function renderBosses(data) {
  const primary = data.primaryMetric || {};
  const converted = primary.value || data.summary?.unifiedConverted380 || data.summary?.bossBasisConverted380 || data.summary?.converted380;
  bossBasis.textContent = `${primary.label || data.summary?.unifiedBasis || "대표 환산"} ${formatNumber(converted)} · 20분 체력보정 기준`;
  bossList.innerHTML = (data.bossBoard || [])
    .map(
      (boss) => `<article class="boss-card" data-tone="${escapeHtml(boss.tone)}">
        <div class="boss-card-head">
          <strong>${escapeHtml(boss.name)}</strong>
          <span>${escapeHtml(boss.status)}</span>
        </div>
        <div class="boss-values">
          <div>
            <em>내 환산</em>
            <b>${formatNumber(boss.currentConverted || converted)}</b>
          </div>
          <div>
            <em>파티 요구</em>
            <b>${formatNumber(boss.partyRequired)}</b>
          </div>
          <div>
            <em>솔플 요구</em>
            <b>${formatNumber(boss.soloRequired)}</b>
          </div>
        </div>
        <small>20분 기준 · 파티 ${formatNumber(boss.partyRatio, 1)}% · 솔플 ${formatNumber(boss.soloRatio, 1)}% · ${escapeHtml(boss.gapLabel || "")}</small>
      </article>`,
    )
    .join("");
}

function iconTile(icon, label, sub = "") {
  return `<div class="icon-tile" title="${escapeHtml(label)}">
    ${icon ? `<img src="${escapeHtml(icon)}" alt="" />` : `<span></span>`}
    <b>${escapeHtml(sub)}</b>
  </div>`;
}

function renderSide(data) {
  renderEquipmentPanel(data);
  renderAbilityPanel(data);
  renderHyperPanel(data);

  symbolIcons.innerHTML = data.symbols
    .map((symbol) => iconTile(symbol.icon, symbol.name, symbol.level ? `Lv.${symbol.level}` : ""))
    .join("");
}

function renderEquipmentPanel(data) {
  equipmentIcons.innerHTML = selectedEquipment(data)
    .filter((item) => item.icon)
    .map((item) => iconTile(item.icon, item.name, item.starforce ? `${item.starforce}` : ""))
    .join("");
}

function renderAbilityPanel(data) {
  const rows = selectedAbility(data);
  abilityList.innerHTML = rows.length
    ? rows
        .map(
          (ability) => `<div class="ability">
            <span>${escapeHtml(ability.grade)}</span>
            <strong>${escapeHtml(ability.value)}</strong>
          </div>`,
        )
        .join("")
    : `<div class="muted">공개된 어빌리티 정보가 없습니다.</div>`;
}

function renderHyperPanel(data) {
  const rows = selectedHyper(data);
  hyperList.innerHTML = rows.length
    ? rows
        .map(
          (row) => `<div class="hyper-row">
            <span>${escapeHtml(row.name)}</span>
            <strong>Lv.${formatNumber(row.level || 0)}</strong>
            <small>${escapeHtml(row.increase || "증가량 정보 없음")}</small>
          </div>`,
        )
        .join("")
    : `<div class="muted">하이퍼스탯 프리셋 정보가 없습니다.</div>`;
}

function previewNames(rows, limit = 3) {
  const names = (rows || [])
    .map((row) => row.name || row.equipment || row.type)
    .filter(Boolean)
    .slice(0, limit);
  return names.length ? names.join(" · ") : "정보 없음";
}

function extraRow(label, count, preview) {
  return `<div class="extra-row">
    <span>${escapeHtml(label)}</span>
    <strong>${formatNumber(count || 0)}</strong>
    <small>${escapeHtml(preview)}</small>
  </div>`;
}

function coverageRow(label, value, preview) {
  return `<div class="coverage-row">
    <span>${escapeHtml(label)}</span>
    <strong>${escapeHtml(value)}</strong>
    <small>${escapeHtml(preview || "")}</small>
  </div>`;
}

function renderExtra(data) {
  const extra = data.extra || {};
  const counts = extra.counts || {};
  extraList.innerHTML = [
    extraRow("펫 장비", counts.pets, previewNames(extra.pets)),
    extraRow("링 스킬", counts.rings, previewNames(extra.rings)),
    extraRow("링크 스킬", counts.linkSkills, previewNames(extra.linkSkills)),
    extraRow("5·6차 스킬", counts.skills, previewNames(extra.skills)),
    extraRow("V코어", counts.vCores, previewNames(extra.vCores)),
    extraRow("HEXA 코어", counts.hexaCores, previewNames(extra.hexaCores)),
    extraRow("HEXA 스탯", counts.hexaStatCores, counts.hexaStatCores ? "설정 정보 수집됨" : "정보 없음"),
    extraRow("기타 능력치", counts.otherStats, previewNames(extra.otherStats)),
  ].join("");
}

function renderCoverage(data) {
  const coverage = data.calculationCoverage || {};
  const audit = data.calculationAudit || {};
  const quality = data.apiDataQuality || {};
  const formula = data.formulaDiagnostics || {};
  const primary = data.primaryMetric || {};
  const confidence = primary.confidence || {};
  const presetQuality = quality.presetSections || {};
  const current = coverage.current || {};
  const total = coverage.targetJobs || 0;
  const missing = [
    ...(coverage.missingDetailJobs || []),
    ...(coverage.missingMultiplierJobs || []),
    ...(coverage.missingCombatJobs || []),
  ];
  const apiStatus = {
    complete: "완전",
    partial: "선택 API 일부 누락",
    warning: "경고 있음",
    error: "필수 API 누락",
  }[quality.status] || "-";
  const warningPreview = (quality.warnings || [])
    .map((row) => `${row.section || "-"}: ${row.message || ""}`)
    .slice(0, 2)
    .join(" · ");
  const optionalMissingPreview = (quality.missingOptionalSections || []).slice(0, 4).join(" · ");
  const formulaStatus = {
    complete: "완전 적용",
    partial: "부분 적용",
    fallback: "임시 계산",
  }[formula.status] || "-";
  const formulaMissingPreview = (formula.missingTables || []).slice(0, 4).join(" · ");
  const confidenceReasons = (confidence.reasons || []).slice(0, 3).join(" · ");
  const coverageRows = [
    coverageRow(
      "대표 지표 신뢰도",
      `${confidence.label || "-"} · ${formatNumber(confidence.score || 0)}점`,
      confidenceReasons || primary.description || "대표 환산 신뢰도",
    ),
    coverageRow(
      "직업 공식",
      `${formula.matchedJob || current.job || "-"} · ${formulaStatus}`,
      formulaMissingPreview ? `부족: ${formulaMissingPreview}` : (formula.message || "직업별 계산식 적용 상태"),
    ),
    coverageRow(
      "API 데이터",
      `${formatNumber(quality.requiredPresent || 0)} / ${formatNumber(quality.requiredTotal || 0)} 필수 · ${formatNumber(quality.optionalPresent || 0)} / ${formatNumber(quality.optionalTotal || 0)} 선택`,
      `${formatNumber(quality.qualityPercent || 0, 1)}% · ${apiStatus}${optionalMissingPreview ? ` · 누락 ${optionalMissingPreview}` : ""}`,
    ),
    coverageRow("API 경고", `${formatNumber(quality.warningCount || 0)}개`, warningPreview || "없음"),
    coverageRow(
      "프리셋 API",
      `장비 ${formatNumber(presetQuality.itemPresetCount || 0)} · 어빌 ${formatNumber(presetQuality.abilityPresetCount || 0)} · 하이퍼 ${formatNumber(presetQuality.hyperPresetCount || 0)}`,
      quality.hexaAvailable ? "HEXA 데이터 수집됨" : "HEXA 데이터 없음 또는 미공개",
    ),
    coverageRow("KMS 상세식", `${formatNumber(coverage.coveredDetailJobs || 0)} / ${formatNumber(total)}`, "레테 포함 직업별 주스탯·무기상수 적용"),
    coverageRow("환산 보정", `${formatNumber(coverage.coveredMultiplierJobs || 0)} / ${formatNumber(total)}`, "원사이트 샘플 기반 직업별 배율"),
    coverageRow("전투력 모델", `${formatNumber(coverage.coveredCombatJobs || 0)} / ${formatNumber(total)}`, "특수 직업은 별도 모델 포함"),
    coverageRow("현재 직업", current.job || "-", `${current.mainStat || "-"} / ${current.attackType || "-"} · ${current.statMode || "single"}`),
    coverageRow("특수 보정", current.specialDetailModel || current.specialCombatModel || "일반 상세식", missing.length ? `누락 ${missing.length}개` : "누락 없음"),
  ];
  const auditRows = (audit.rows || []).map((row) => coverageRow(row.label, row.value, row.detail));
  coverageList.innerHTML = [...coverageRows, ...auditRows].join("");
}

function optionLine(label, value, suffix = "") {
  if (!Number.isFinite(Number(value)) || Number(value) === 0) return "";
  return `<span>${escapeHtml(label)} ${formatNumber(value, Number(value) % 1 ? 1 : 0)}${suffix}</span>`;
}

function renderUpgradePlan(data) {
  const plan = selectedUpgradePlan(data);
  const primary = data.primaryMetric || {};
  const rows = plan.top || [];
  const targets = (plan.upgradeTargets || []).join("/");
  const presetLabel = selectedPresets.itemPreset ? ` · 장비 ${selectedPresets.itemPreset}/어빌 ${selectedPresets.abilityPreset || "-"}/하이퍼 ${selectedPresets.hyperPreset || "-"}` : "";
  const focus = plan.repairFocus || {};
  const focusText = focus.description ? ` · ${focus.description}` : focus.slot ? ` · 우선 ${focus.slot}${focus.category ? `/${focus.category}` : ""}` : "";
  upgradeSummary.textContent = `${primary.label || plan.basis || data.summary?.unifiedBasis || "대표 환산"} · ${formatNumber(plan.currentConverted || primary.value || data.summary?.unifiedConverted380 || 0)}${presetLabel}${targets ? ` · ${targets}` : ""}${focusText}`;
  const checklistCards = (plan.repairChecklist || [])
    .slice(0, 3)
    .map((row) => `<article class="upgrade-slot priority">
      <span>${formatNumber(row.rank || 0)}순위 · ${escapeHtml(row.slot || "-")}</span>
      <strong>+${formatNumber(row.expectedGain || 0)}</strong>
      <small>${escapeHtml(row.type || "-")} · ${escapeHtml(row.action || "-")}</small>
      <em>${escapeHtml(row.item || "-")}${row.weakness?.label ? ` · ${escapeHtml(row.weakness.label)}` : ""}</em>
    </article>`)
    .join("");
  const slotCards = (plan.slotSummary || [])
    .slice(0, 4)
    .map((slot) => `<article class="upgrade-slot">
      <span>${escapeHtml(slot.slot)}</span>
      <strong>+${formatNumber(slot.totalGain)}</strong>
      <small>${formatNumber(slot.sharePercent, 1)}% · ${escapeHtml(slot.bestType || "-")} · ${escapeHtml(slot.bestAction || "-")}</small>
      <em>${escapeHtml(slot.bestItem || "-")}${slot.topWeakness ? ` · ${escapeHtml(slot.topWeakness)}` : ""}</em>
    </article>`)
    .join("");
  upgradeSlotList.innerHTML = checklistCards + slotCards;
  upgradeCategoryList.innerHTML = (plan.categorySummary || [])
    .slice(0, 5)
    .map((category) => `<article class="upgrade-category">
      <span>${escapeHtml(category.type)}</span>
      <strong>+${formatNumber(category.totalGain)}</strong>
      <small>${formatNumber(category.sharePercent, 1)}% · ${escapeHtml(category.bestItem || "-")} · ${escapeHtml(category.bestAction || "-")}</small>
    </article>`)
    .join("");
  if (!rows.length) {
    upgradeList.innerHTML = `<article class="upgrade-card empty-card">
      <strong>추천할 개선 항목이 없습니다</strong>
      <span>API 장비 정보가 부족하거나 이미 기준치를 만족한 장비입니다.</span>
    </article>`;
    return;
  }

  upgradeList.innerHTML = rows
    .map((row, index) => {
      const scenarios = (row.scenarios || [])
        .map((scenario) => `<em>${escapeHtml(scenario.type)} · ${escapeHtml(scenario.action)} · +${formatNumber(scenario.gain)}</em>`)
        .join("");
      const weaknesses = (row.weaknesses || [])
        .map((weakness) => `<em>${escapeHtml(weakness.label)} ${formatNumber(weakness.current, 1)}${escapeHtml(weakness.unit || "")}/${formatNumber(weakness.target, 1)}${escapeHtml(weakness.unit || "")}</em>`)
        .join("");
      return `<article class="upgrade-card">
        <div class="upgrade-rank">${index + 1}</div>
        <img src="${escapeHtml(row.icon)}" alt="" />
        <div class="upgrade-body">
          <div class="upgrade-head">
            <span>${escapeHtml(row.slot || row.part || "-")}</span>
            <b>${escapeHtml(row.name || "-")}</b>
            <i>${escapeHtml(row.currentState || "-")}</i>
          </div>
          <strong>${escapeHtml(row.recommendedType)} · ${escapeHtml(row.recommendedAction)}</strong>
          <small>${escapeHtml(row.reason || "")}</small>
          <small class="upgrade-options">잠재 ${escapeHtml(row.potentialSummary || "-")} · 에디 ${escapeHtml(row.additionalPotentialSummary || "-")}</small>
          <div class="upgrade-metrics">
            <span>예상 +${formatNumber(row.expectedGain)} (${formatNumber(row.expectedGainPercent || 0, 2)}%)</span>
            <span>현재 기여 ${formatNumber(row.contribution)}</span>
            <span>우선 ${formatNumber(row.priorityScore)}</span>
          </div>
          <div class="upgrade-weaknesses">${weaknesses}</div>
          <div class="upgrade-scenarios">${scenarios}</div>
        </div>
      </article>`;
    })
    .join("");
}

function renderItems(data) {
  const summary = data.summary || {};
  const items = selectedEquipment(data);
  const starforceTotal = items.reduce((sum, item) => sum + Number(item.starforce || 0), 0);
  equipmentSummary.textContent = `${items.length || summary.equipmentCount || 0}개 · 스타포스 ${formatNumber(starforceTotal || summary.starforceTotal || 0)}`;
  itemList.innerHTML = items
    .map((item) => {
      const lines = [
        optionLine(data.summary.mainStat, item.mainOption),
        optionLine(data.summary.attackType, item.attackOption),
        optionLine("보공", item.bossDamage, "%"),
        optionLine("데미지", item.damage, "%"),
        optionLine("올스탯", item.allStat, "%"),
      ]
        .filter(Boolean)
        .join("");
      const potentials = [...item.potentials, ...item.additionalPotentials]
        .slice(0, 4)
        .map((line) => `<em>${escapeHtml(line)}</em>`)
        .join("");
      return `<article class="item-card">
        <img src="${escapeHtml(item.icon)}" alt="" />
        <div class="item-body">
          <div class="item-top">
            <span>${escapeHtml(item.starforce ? `${item.starforce}성` : item.slot)}</span>
            <b>${escapeHtml(item.name)}</b>
          </div>
          <div class="item-options">${lines || "<span>옵션 정보 없음</span>"}</div>
          <div class="potentials">${potentials}</div>
        </div>
      </article>`;
    })
    .join("");
}

function point(cx, cy, radius, index, total, percent) {
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total;
  const length = radius * (percent / 100);
  return [cx + Math.cos(angle) * length, cy + Math.sin(angle) * length];
}

function drawRadar(values) {
  const keys = Object.keys(LABELS);
  const cx = 120;
  const cy = 120;
  const radius = 78;
  const grid = [25, 50, 75, 100]
    .map((level) => {
      const points = keys.map((_, index) => point(cx, cy, radius, index, keys.length, level).join(",")).join(" ");
      return `<polygon points="${points}" class="radar-grid" />`;
    })
    .join("");
  const axes = keys
    .map((key, index) => {
      const [x, y] = point(cx, cy, radius, index, keys.length, 100);
      const [lx, ly] = point(cx, cy, radius + 22, index, keys.length, 100);
      return `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" class="radar-axis" />
        <text x="${lx}" y="${ly}" text-anchor="middle">${LABELS[key]}</text>`;
    })
    .join("");
  const dataPoints = keys
    .map((key, index) => point(cx, cy, radius, index, keys.length, Math.max(0, Math.min(100, values[key] || 0))).join(","))
    .join(" ");
  radar.innerHTML = `${grid}${axes}<polygon points="${dataPoints}" class="radar-fill" />`;
}

function render(data) {
  activeData = data;
  const views = data.presetViews || {};
  selectedPresets = {
    itemPreset: views.active?.itemPreset || views.equipment?.[0]?.no || null,
    abilityPreset: views.active?.abilityPreset || views.ability?.[0]?.no || null,
    hyperPreset: views.active?.hyperPreset || views.hyper?.[0]?.no || null,
  };
  emptyState.hidden = true;
  dashboard.hidden = false;
  renderProfile(data);
  renderScores(data);
  renderPresetBrowser(data);
  renderProfileIcons(selectedEquipment(data));
  renderBosses(data);
  renderSide(data);
  renderExtra(data);
  renderCoverage(data);
  renderUpgradePlan(data);
  renderItems(data);
  drawRadar(data.radar || {});
  rawOutput.textContent = JSON.stringify(data, null, 2);
  setActiveTab(activeTab);
}

async function search(characterName, date) {
  setStatus("조회 중", "busy");
  searchButton.disabled = true;
  try {
    const response = await fetch("/api/character", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ characterName, date }),
    });
    const body = await readJson(response);
    if (!response.ok) throw new Error(body.error || "조회에 실패했습니다.");
    render(body);
    setStatus("조회 완료", "ready");
  } finally {
    searchButton.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const name = nameInput.value.trim();
  if (!name) {
    setStatus("닉네임을 입력해주세요", "error");
    nameInput.focus();
    return;
  }
  if (searchButton.disabled) return;
  search(name, dateInput.value).catch((error) => {
    setStatus(error.message, "error");
  });
});

tabButtons.forEach((button) => {
  button.addEventListener("click", () => setActiveTab(button.dataset.tab || "overview"));
});

document.addEventListener("click", (event) => {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest("[data-preset-kind]");
  if (!button || !activeData) return;
  const kind = button.dataset.presetKind;
  const no = Number(button.dataset.presetNo);
  if (!kind || !Number.isFinite(no)) return;
  selectedPresets = { ...selectedPresets, [kind]: no };
  applyPresetSelection(activeData);
});

loadHealth();
