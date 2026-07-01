"""sync-cents — Synchrony app extension."""

from flask import Flask, jsonify, redirect, render_template, request, url_for

from synccents import SyncCents
from synccents.models import ExpenseCategory

app = Flask(__name__)
ss = SyncCents()


@app.route("/")
def index():
    if ss.enrolled:
        return redirect(url_for("home"))
    return redirect(url_for("onboarding"))


@app.route("/synccents/onboarding")
def onboarding():
    if ss.enrolled:
        return redirect(url_for("home"))
    return render_template("onboarding.html")


@app.route("/synccents")
def home():
    if not ss.enrolled:
        return redirect(url_for("onboarding"))
    return render_template("home.html")


@app.route("/synccents/settings")
def settings():
    if not ss.enrolled:
        return redirect(url_for("onboarding"))
    return render_template("settings.html")


# ── API ────────────────────────────────────────────────────────────

@app.route("/api/status")
def status():
    return jsonify({"enrolled": ss.enrolled})


@app.route("/api/onboarding")
def onboarding_data():
    return jsonify(ss.get_onboarding_data())


@app.route("/api/enroll", methods=["POST"])
def enroll():
    data = request.json or {}
    ss.enroll(
        daily_contribution_cents=int(data.get("daily_contribution_cents", 50)),
        min_balance_threshold=float(data.get("min_balance_threshold", 500)),
    )
    return jsonify({"enrolled": True, "home": ss.get_home_summary()})


@app.route("/api/reset-enrollment", methods=["POST"])
def reset_enrollment():
    ss.reset_enrollment()
    return jsonify({"enrolled": False, "redirect": "/synccents/onboarding"})


@app.route("/api/home")
def home_data():
    # Auto-run today's deposit if eligible
    ss.sync_cents()
    return jsonify(ss.get_home_summary())


@app.route("/api/sync", methods=["POST"])
def run_sync():
    deposit = ss.sync_cents()
    return jsonify({
        "deposit": deposit.to_dict() if deposit else None,
        "home": ss.get_home_summary(),
    })


@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify({
        "monthly_income": ss.monthly_income,
        "checking_balance": ss.checking_balance,
        "min_balance_threshold": ss.min_balance_threshold,
        "daily_contribution_cents": ss.daily_contribution_cents,
        "suggestion": ss.suggest_daily_contribution(),
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    ss.configure(
        monthly_income=data.get("monthly_income"),
        min_balance_threshold=data.get("min_balance_threshold"),
        daily_contribution_cents=data.get("daily_contribution_cents"),
    )
    if "checking_balance" in data:
        ss.checking_balance = float(data["checking_balance"])
    return jsonify({"ok": True, "home": ss.get_home_summary()})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
