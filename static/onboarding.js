let currentStep = 1;
let onboardingData = null;
let suggestedCents = 50;

const $ = (id) => document.getElementById(id);

function fmt(n) {
  return "$" + Number(n).toFixed(2);
}

function showStep(n) {
  currentStep = n;
  document.querySelectorAll(".step").forEach((s) => {
    s.classList.toggle("active", parseInt(s.dataset.step) === n);
  });
}

function nextStep() {
  if (currentStep < 4) showStep(currentStep + 1);
  if (currentStep === 4) updateConfirm();
}

function useSuggested() {
  $("daily-cents").value = suggestedCents;
  updateProjection();
}

function updateProjection() {
  const cents = parseInt($("daily-cents").value) || 0;
  const monthly = (cents / 100) * 30;
  const yearly = (cents / 100) * 365;
  $("projection-hint").textContent =
    `≈ ${fmt(monthly)}/month · ${fmt(yearly)}/year`;
}

function updateConfirm() {
  const cents = parseInt($("daily-cents").value) || 50;
  const threshold = parseFloat($("threshold").value) || 500;
  const monthly = (cents / 100) * 30;
  $("confirm-summary").innerHTML = `
    <div><strong>Daily contribution:</strong> ${cents}¢/day (${fmt(monthly)}/mo)</div>
    <div><strong>Safety balance:</strong> ${fmt(threshold)}</div>
    <div><strong>Deposits when:</strong> Checking is above ${fmt(threshold)}</div>
  `;
}

async function loadOnboarding() {
  const res = await fetch("/api/onboarding");
  onboardingData = await res.json();
  const s = onboardingData.suggestion;
  suggestedCents = s.suggested_cents;

  $("spending-summary").innerHTML = `
    <div class="big-number">${fmt(s.monthly_spending)}</div>
    <div class="analysis-label">estimated monthly spending</div>
  `;

  const habits = onboardingData.spending_habits;
  if (habits.length === 0) {
    $("category-breakdown").innerHTML = "";
  } else {
    $("category-breakdown").innerHTML = habits.map((h) => `
      <div class="category-row">
        <span class="cat-name">${h.category}</span>
        <span class="cat-pct">${fmt(h.total)} · ${h.percentage}%</span>
      </div>
    `).join("");
  }

  $("suggested-amount").textContent = `${s.suggested_cents}¢`;
  $("suggestion-detail").textContent = s.explanation;
  $("daily-cents").value = s.suggested_cents;
  updateProjection();
}

async function enroll() {
  const cents = parseInt($("daily-cents").value) || 50;
  const threshold = parseFloat($("threshold").value) || 500;

  await fetch("/api/enroll", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      daily_contribution_cents: cents,
      min_balance_threshold: threshold,
    }),
  });

  window.location.href = "/syncsave";
}

$("daily-cents").addEventListener("input", updateProjection);
$("threshold").addEventListener("input", updateConfirm);

loadOnboarding();
