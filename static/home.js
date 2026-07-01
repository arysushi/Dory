const $ = (id) => document.getElementById(id);

function fmt(n) {
  return "$" + Number(n).toFixed(2);
}

function fmtCents(c) {
  return c + "¢";
}

async function loadHome() {
  const res = await fetch("/api/home");
  const data = await res.json();
  render(data);
}

async function returnToEnrollment() {
  await fetch("/api/reset-enrollment", { method: "POST" });
  window.location.href = "/synccents/onboarding";
}

function render(data) {
  $("savings-balance").textContent = fmt(data.savings_balance);
  $("total-saved").innerHTML =
    `${fmt(data.total_auto_saved)} saved <button type="button" class="invisible-btn" onclick="returnToEnrollment()" aria-label="Return to enrollment">automatically</button>`;

  const todayEl = $("today-amount");
  if (data.today_deposit.deposited) {
    todayEl.textContent = "+" + fmt(data.today_deposit.amount);
    todayEl.className = "today-amount done";
  } else if (data.can_deposit_today) {
    todayEl.textContent = `${fmtCents(data.daily_contribution_cents)} pending`;
    todayEl.className = "today-amount pending";
  } else {
    todayEl.textContent = "Skipped — below threshold";
    todayEl.className = "today-amount pending";
  }

  $("streak").textContent =
    data.streak_days === 1 ? "1 day streak" : `${data.streak_days} day streak`;

  $("daily-rate").textContent = fmtCents(data.daily_contribution_cents);
  $("monthly-proj").textContent = fmt(data.monthly_projection);
  $("threshold-display").textContent = fmt(data.min_balance_threshold);

  $("daily-feed").innerHTML = data.daily_feed.map((d) => `
    <div class="feed-row">
      <span class="feed-date">${d.label}</span>
      ${d.deposited
        ? `<span class="feed-amount">+${fmt(d.amount)}</span>`
        : `<span class="feed-amount missed">${d.label === "Today" && data.can_deposit_today ? "Pending" : "1.00"}</span>`
      }
    </div>
  `).join("");

  const yearly = (data.daily_contribution_cents / 100) * 365;
  $("tip-banner").textContent =
    `Saving ${fmtCents(data.daily_contribution_cents)} a day adds up to ${fmt(yearly)} a year — without feeling it.`;
}

loadHome();
