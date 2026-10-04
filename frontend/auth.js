const reg = !!$("#full_name");
$("#f").onsubmit = async e => {
  e.preventDefault(); const btn = $("button[type=submit]"); btn.disabled = true; $("#err").textContent = "";
  try {
    const body = {email: $("#email").value.trim(), password: $("#pw").value};
    if (reg) { body.full_name = $("#full_name").value.trim(); for (const k of ["phone", "blood_group"]) if ($("#" + k).value) body[k] = $("#" + k).value; if ($("#age").value) body.age = +$("#age").value; }
    const d = await api(reg ? "/api/auth/register" : "/api/auth/login", {method: "POST", body});
    localStorage.setItem("mb_token", d.access_token); location.href = "dashboard.html";
  } catch (er) { $("#err").textContent = er.message; btn.disabled = false; }
};
