import { api, auth } from "../api.js";
import { el, esc, toast } from "../ui.js";
import { navigate } from "../router.js";

export function render(container) {
  let mode = "login";

  const view = el(`<div id="login-root"></div>`);
  container.replaceChildren(view);

  const draw = () => {
    view.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = `
      #login-root {
        min-height: 100vh;
        min-height: 100dvh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(ellipse at 50% 0%, #0d1b3e 0%, #050810 60%, #000 100%);
        padding: 24px 20px;
        position: relative;
        overflow: hidden;
      }
      #login-root::before {
        content: '';
        position: absolute;
        top: -20%;
        left: 50%;
        transform: translateX(-50%);
        width: 600px;
        height: 400px;
        background: radial-gradient(ellipse, rgba(74,158,255,0.15) 0%, transparent 70%);
        pointer-events: none;
      }
      .login-card {
        width: 100%;
        max-width: 420px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 32px 28px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 25px 60px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06);
      }
      .login-title {
        text-align: center;
        margin-bottom: 8px;
      }
      .login-title .gym { font-size: 36px; font-weight: 700; letter-spacing: -0.03em; color: #fff; }
      .login-title .bro { color: #4a9eff; }
      .login-sub { text-align: center; color: rgba(255,255,255,0.45); font-size: 14px; margin-bottom: 32px; }
      .login-field { margin-bottom: 16px; }
      .login-field label { display: block; font-size: 13px; color: rgba(255,255,255,0.6); margin-bottom: 8px; font-weight: 500; letter-spacing: 0.01em; }
      .login-input-wrap { position: relative; }
      .login-input-wrap svg { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 16px; height: 16px; color: rgba(255,255,255,0.3); pointer-events: none; }
      .login-input {
        width: 100%;
        height: 50px;
        padding: 0 16px 0 42px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        color: #fff;
        font-size: 15px;
        font-family: inherit;
        transition: border-color 0.2s, background 0.2s;
        outline: none;
      }
      .login-input:focus {
        border-color: rgba(74,158,255,0.6);
        background: rgba(255,255,255,0.09);
      }
      .login-input::placeholder { color: rgba(255,255,255,0.2); }
      .login-btn {
        width: 100%;
        height: 52px;
        border-radius: 14px;
        background: linear-gradient(135deg, #4a9eff 0%, #2d7fd9 100%);
        color: #fff;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.01em;
        border: none;
        cursor: pointer;
        margin-top: 8px;
        transition: opacity 0.15s, transform 0.1s;
        box-shadow: 0 8px 24px rgba(74,158,255,0.35);
      }
      .login-btn:active { transform: scale(0.98); opacity: 0.9; }
      .login-btn:disabled { opacity: 0.6; cursor: default; }
      .login-toggle { text-align: center; margin-top: 20px; font-size: 13.5px; color: rgba(255,255,255,0.4); }
      .login-toggle a { color: #4a9eff; cursor: pointer; }
      .login-error {
        background: rgba(239,68,68,0.12);
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 13.5px;
        color: #fca5a5;
        margin-bottom: 16px;
      }
    `;
    document.head.appendChild(style);

    const emailField = mode === "register" ? `
      <div class="login-field">
        <label>Email</label>
        <div class="login-input-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,12 2,6"/></svg>
          <input class="login-input" type="email" id="email" placeholder="vos@email.com" autocomplete="email" inputmode="email">
        </div>
      </div>
    ` : "";

    const card = el(`
      <div class="login-card">
        <div class="login-title"><span class="gym">Gym<span class="bro">Bro</span></span></div>
        <div class="login-sub">Tu rutina, tu progreso.</div>

        <div id="err" class="login-error" style="display:none;"></div>

        ${emailField}

        <div class="login-field">
          <label>Usuario</label>
          <div class="login-input-wrap">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <input class="login-input" type="text" id="username" placeholder="tu usuario" autocomplete="username" autocapitalize="none" autocorrect="off">
          </div>
        </div>

        <div class="login-field">
          <label>Contraseña</label>
          <div class="login-input-wrap">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
            <input class="login-input" type="password" id="password" placeholder="••••••••" autocomplete="${mode === 'login' ? 'current-password' : 'new-password'}">
          </div>
        </div>

        <button class="login-btn" id="submit">${mode === "login" ? "Ingresar" : "Crear cuenta"}</button>

        <div class="login-toggle">
          ${mode === "login"
            ? `No tengo cuenta, <a id="toggle">registrarme</a>`
            : `Ya tengo cuenta, <a id="toggle">ingresar</a>`
          }
        </div>
      </div>
    `);

    view.appendChild(card);

    const errEl = card.querySelector("#err");
    const showErr = (msg) => { errEl.textContent = msg; errEl.style.display = "block"; };
    const hideErr = () => { errEl.style.display = "none"; };

    card.querySelector("#toggle").addEventListener("click", () => {
      mode = mode === "login" ? "register" : "login";
      draw();
    });

    const doSubmit = async () => {
      hideErr();
      const username = card.querySelector("#username").value.trim();
      const password = card.querySelector("#password").value;
      if (!username || !password) return showErr("Completa usuario y contraseña");

      const btn = card.querySelector("#submit");
      btn.disabled = true;
      btn.textContent = mode === "login" ? "Ingresando..." : "Creando cuenta...";

      try {
        const res = mode === "login"
          ? await api.login(username, password)
          : await api.register(username, card.querySelector("#email")?.value?.trim() || "", password);
        auth.set(res.access_token, res.user);
        navigate("/routines");
      } catch (e) {
        showErr(e.detail || e.message || "Error");
        btn.disabled = false;
        btn.textContent = mode === "login" ? "Ingresar" : "Crear cuenta";
      }
    };

    card.querySelector("#submit").addEventListener("click", doSubmit);
    card.addEventListener("keydown", (e) => { if (e.key === "Enter") doSubmit(); });

    // focus en username
    setTimeout(() => card.querySelector("#username")?.focus(), 50);
  };

  draw();
}
