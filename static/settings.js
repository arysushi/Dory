let suggestedCents = 50;
const $ = (id) => document.getElementById(id);

function fmt(n) {
  return "$" + Number(n).toFixed(2);
}

function updateProjection() {
  const cents = parseInt($("daily-cents").value) || 0;
  const monthly = (cents / 100) * 30;
  $("settings-projection").textContent = `≈ ${fmt(monthly)}/month`;
}

function applySuggested() {
  $("daily-cents").value = suggestedCents;
  updateProjection();
}

async function loadSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();

  suggestedCents = data.suggestion.suggested_cents;
  $("settings-suggested").textContent = suggestedCents + "¢";

  $("daily-cents").value = data.daily_contribution_cents;
  $("threshold").value = data.min_balance_threshold;
  $("income").value = data.monthly_income;
  $("checking").value = data.checking_balance;
  updateProjection();
}

async function saveSettings(e) {
  e.preventDefault();
  const status = $("save-status");

  await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      daily_contribution_cents: parseInt($("daily-cents").value) || 50,
      min_balance_threshold: parseFloat($("threshold").value) || 500,
      monthly_income: parseFloat($("income").value) || 0,
      checking_balance: parseFloat($("checking").value) || 0,
    }),
  });

  status.textContent = "Settings saved.";
  setTimeout(() => { status.textContent = ""; }, 3000);
}

$("daily-cents").addEventListener("input", updateProjection);
loadSettings();
